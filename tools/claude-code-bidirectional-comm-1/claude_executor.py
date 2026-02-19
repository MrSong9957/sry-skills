#!/usr/bin/env python3
"""
Claude Code 命令执行器 - 获取任务总结
核心功能：发送指令给 Claude Code，获取执行总结，写入文件
"""

import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


# =============================================================================
# 配置
# =============================================================================

DEFAULT_COMMAND = "请总结当前项目的架构"
OUTPUT_FILE = Path("claude-code-bidirectional-comm/claude_output.txt")
LOG_FILE = Path("claude-code-bidirectional-comm/claude_executor.log")
EXECUTION_TIMEOUT = 300  # 5分钟超时


# =============================================================================
# 日志配置
# =============================================================================

def setup_logging() -> logging.Logger:
    """配置日志系统"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# =============================================================================
# 输出过滤器
# =============================================================================

def strip_ansi(text: str) -> str:
    """移除 ANSI 转义序列"""
    # CSI: ESC[ ...
    ansi_csi = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
    # OSC: ESC] ...
    ansi_osc = re.compile(r'\x1b\][^\x07\x1b]*[\x07\x1b\\]')

    text = ansi_csi.sub('', text)
    text = ansi_osc.sub('', text)

    # 移除控制字符，保留换行和制表符
    cleaned = []
    for char in text:
        code = ord(char)
        if code >= 32 or code in (9, 10):
            cleaned.append(char)
    return ''.join(cleaned)


def extract_summary_from_output(output: str) -> str:
    """
    从 Claude Code 输出中提取任务总结

    总结特征：
    - 包含 "Total cost:", "Total duration", "Usage:" 等字段
    - 通常在输出末尾
    """
    clean_output = strip_ansi(output)

    # 查找总结块的开始
    summary_keywords = ['Total cost:', '会话总结', 'Session Summary']
    summary_start = -1

    for keyword in summary_keywords:
        idx = clean_output.find(keyword)
        if idx != -1:
            summary_start = idx
            break

    if summary_start == -1:
        # 没有找到总结格式，返回整个清理后的输出
        logger.info("未找到标准总结格式，返回完整输出")
        return clean_output.strip()

    # 提取从总结开始到末尾的内容
    summary = clean_output[summary_start:].strip()

    # 移除多余的空行
    summary = re.sub(r'\n{3,}', '\n\n', summary)

    return summary


# =============================================================================
# 执行器
# =============================================================================

class ClaudeCodeExecutor:
    """Claude Code 命令执行器"""

    def __init__(self, output_file: Path = OUTPUT_FILE, timeout: int = EXECUTION_TIMEOUT):
        self.output_file = output_file
        self.timeout = timeout

    def execute(self, command: str) -> bool:
        """
        执行 Claude Code 命令并保存总结

        Args:
            command: 要执行的命令或提示词

        Returns:
            是否执行成功
        """
        logger.info(f"执行命令: {command[:100]}...")

        try:
            # 方法1: 尝试使用 claude -p 非交互模式
            result = self._run_with_print_mode(command)
            if result:
                return True

            # 方法2: 回退到 PTY 交互模式
            logger.info("回退到 PTY 交互模式")
            return self._run_with_pty_mode(command)

        except subprocess.TimeoutExpired:
            logger.error(f"执行超时 ({self.timeout}s)")
            return False
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return False

    def _run_with_print_mode(self, command: str) -> bool:
        """
        使用 claude -p 非交互模式执行

        优点：自动等待完成，结构化输出
        """
        try:
            # 构建命令
            cmd = [
                'claude',
                '-p',  # 非交互模式
                '--no-session-persistence',  # 不保存会话
                command
            ]

            # 设置环境变量（如果在 Claude 内部调用）
            env = os.environ.copy()
            env['CLAUDECODE'] = ''  # 避免嵌套检测

            # 执行命令（阻塞等待完成）
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd='/workspace/project'
            )

            # 检查退出码
            if result.returncode != 0:
                logger.warning(f"claude -p 返回码: {result.returncode}")
                if result.stderr:
                    logger.warning(f"错误输出: {result.stderr[:500]}")
                # 即使返回码非0，尝试解析输出

            # 获取输出
            output = result.stdout
            if not output:
                output = result.stderr

            # 提取并保存总结
            summary = extract_summary_from_output(output)
            self._save_summary(summary, command)

            return True

        except FileNotFoundError:
            logger.warning("claude 命令未找到，尝试 PTY 模式")
            return False
        except Exception as e:
            logger.debug(f"print mode 失败: {e}")
            return False

    def _run_with_pty_mode(self, command: str) -> bool:
        """
        使用 PTY 伪终端模式执行（回退方案）
        """
        import pty
        import select

        master_fd = slave_fd = None
        process = None

        try:
            # 创建伪终端
            master_fd, slave_fd = pty.openpty()

            # 启动进程
            process = subprocess.Popen(
                ['claude'],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                text=False,
                close_fds=True
            )
            os.close(slave_fd)
            slave_fd = None

            logger.info(f"Claude 已启动 (PID: {process.pid})")

            # 等待启动
            time.sleep(1)

            # 发送命令
            os.write(master_fd, (command + '\n').encode())
            logger.info("命令已发送")

            # 读取输出
            output_buffer = []
            idle_count = 0
            max_idle = 50  # 5秒无输出认为完成

            start_time = time.time()

            while (time.time() - start_time) < self.timeout:
                # 检查进程是否退出
                if process.poll() is not None:
                    logger.info(f"进程已退出 (退出码: {process.returncode})")
                    break

                # 检查是否有数据
                if select.select([master_fd], [], [], 0.1)[0]:
                    try:
                        data = os.read(master_fd, 4096)
                        if data:
                            output_buffer.append(data.decode(errors='replace'))
                            idle_count = 0
                    except OSError:
                        break
                else:
                    idle_count += 1

                # 空闲超时
                if idle_count >= max_idle:
                    logger.info("检测到空闲，发送 EOF 退出")
                    os.write(master_fd, b'\x04')  # Ctrl+D
                    time.sleep(0.5)
                    # 读取剩余输出
                    try:
                        while select.select([master_fd], [], [], 0.5)[0]:
                            data = os.read(master_fd, 4096)
                            if not data:
                                break
                            output_buffer.append(data.decode(errors='replace'))
                    except OSError:
                        pass
                    break

            # 合并输出
            full_output = ''.join(output_buffer)

            # 提取并保存总结
            summary = extract_summary_from_output(full_output)
            self._save_summary(summary, command)

            return True

        finally:
            # 清理资源
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except:
                    process.kill()
            if master_fd is not None:
                try:
                    os.close(master_fd)
                except:
                    pass
            if slave_fd is not None:
                try:
                    os.close(slave_fd)
                except:
                    pass

    def _save_summary(self, summary: str, command: str) -> None:
        """保存总结到文件"""
        # 确保目录存在
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # 格式化输出
        content = f"""{'=' * 60}
Claude Code 任务总结
时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
命令: {command[:100]}...
{'=' * 60}

{summary}

{'=' * 60}
"""

        # 写入文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"总结已保存到: {self.output_file}")


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Code 命令执行器")
    parser.add_argument('command', nargs='?', default=DEFAULT_COMMAND, help="要执行的命令")
    parser.add_argument('-t', '--timeout', type=int, default=EXECUTION_TIMEOUT, help="超时时间（秒）")
    parser.add_argument('-o', '--output', type=str, help="输出文件路径")
    args = parser.parse_args()

    output_file = Path(args.output) if args.output else OUTPUT_FILE

    print("=" * 60)
    print("Claude Code 命令执行器")
    print("=" * 60)

    executor = ClaudeCodeExecutor(output_file=output_file, timeout=args.timeout)

    try:
        if executor.execute(args.command):
            print(f"\n执行成功！总结已保存到: {output_file}")
            return 0
        else:
            print("\n执行失败，请查看日志")
            return 1
    except KeyboardInterrupt:
        print("\n用户中断")
        return 130


if __name__ == "__main__":
    sys.exit(main())
