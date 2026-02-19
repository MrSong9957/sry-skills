#!/usr/bin/env python3
"""
Claude Code执行器
复用现有claude_executor.py逻辑
"""

import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class ClaudeExecutor:
    """Claude Code命令执行器"""

    DEFAULT_TIMEOUT = 300
    OUTPUT_FILE = Path("claude_output.txt")

    def __init__(self, output_file: Optional[Path] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        初始化执行器

        Args:
            output_file: 输出文件路径
            timeout: 执行超时时间（秒）
        """
        self.output_file = output_file or self.OUTPUT_FILE
        self.timeout = timeout
        self.project_dir = self._get_valid_project_dir()

    def _get_valid_project_dir(self) -> Path:
        """
        获取有效的项目目录

        Returns:
            有效的项目目录路径
        """
        # 首先尝试当前工作目录
        cwd = Path.cwd()
        if cwd.exists() and cwd.is_dir():
            logger.debug(f"使用当前工作目录: {cwd}")
            return cwd

        # 回退到脚本所在目录的父目录
        script_dir = Path(__file__).parent.parent
        if script_dir.exists() and script_dir.is_dir():
            logger.warning(f"当前工作目录无效，使用脚本目录: {script_dir}")
            return script_dir

        # 最终回退到用户主目录
        home_dir = Path.home()
        logger.warning(f"脚本目录无效，回退到用户主目录: {home_dir}")
        return home_dir

    def set_project_dir(self, project_dir: str) -> None:
        """
        设置项目目录（带验证）

        Args:
            project_dir: 项目目录路径

        Raises:
            ValueError: 目录不存在或无效
        """
        validated_dir = self._validate_project_dir(project_dir)
        self.project_dir = Path(validated_dir)
        logger.info(f"项目目录已设置: {self.project_dir}")

    def _validate_project_dir(self, project_dir: str) -> str:
        """
        验证项目目录有效性

        Args:
            project_dir: 项目目录路径

        Returns:
            验证通过的绝对路径

        Raises:
            ValueError: 目录不存在或无效
        """
        path = Path(project_dir).resolve()

        if not path.exists():
            raise ValueError(f"项目目录不存在: {project_dir}")

        if not path.is_dir():
            raise ValueError(f"路径不是目录: {project_dir}")

        return str(path)

    def execute(self, command: str) -> Dict:
        """
        执行Claude Code命令

        Args:
            command: 要执行的命令

        Returns:
            执行结果字典:
            {
                'success': bool,
                'output': str,
                'summary': str,
                'error': Optional[str]
            }
        """
        logger.info(f"执行Claude命令: {command[:100]}...")

        try:
            # 方法1: 尝试使用 claude -p 非交互模式
            result = self._run_with_print_mode(command)
            if result["success"]:
                return result

            # 方法2: 回退到 PTY 交互模式
            logger.info("回退到 PTY 交互模式")
            return self._run_with_pty_mode(command)

        except subprocess.TimeoutExpired:
            logger.error(f"执行超时 ({self.timeout}s)")
            return {
                "success": False,
                "output": "",
                "summary": "",
                "error": f"执行超时 ({self.timeout}s)"
            }
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "success": False,
                "output": "",
                "summary": "",
                "error": str(e)
            }

    def _run_with_print_mode(self, command: str) -> Dict:
        """
        使用 claude -p 非交互模式执行

        Args:
            command: 要执行的命令

        Returns:
            执行结果字典
        """
        try:
            cmd = [
                'claude',
                '-p',
                '--no-session-persistence',
                command
            ]

            env = os.environ.copy()
            env['CLAUDECODE'] = ''

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout,
                env=env,
                cwd=str(self.project_dir)
            )

            output = result.stdout
            if not output:
                output = result.stderr

            summary = self._extract_summary(output)
            self._save_summary(summary, command)

            return {
                "success": result.returncode == 0 or bool(output),
                "output": output,
                "summary": summary,
                "error": None
            }

        except FileNotFoundError:
            logger.warning("claude 命令未找到")
            return {
                "success": False,
                "output": "",
                "summary": "",
                "error": "claude 命令未找到"
            }
        except Exception as e:
            logger.warning(
                f"print mode 失败: {type(e).__name__}: {e}\n"
                f"  项目目录: {self.project_dir}\n"
                f"  目录存在: {self.project_dir.exists()}\n"
                f"  是否目录: {self.project_dir.is_dir() if self.project_dir.exists() else 'N/A'}"
            )
            return {
                "success": False,
                "output": "",
                "summary": "",
                "error": str(e)
            }

    def _run_with_pty_mode(self, command: str) -> Dict:
        """
        使用 PTY 伪终端模式执行（回退方案）

        平台兼容性:
        - Unix/Linux: 使用 PTY 伪终端
        - Windows: 使用 subprocess.PIPE 代替
        """
        if sys.platform == 'win32':
            return self._run_windows_mode(command)
        else:
            return self._run_unix_pty_mode(command)

    def _run_windows_mode(self, command: str) -> Dict:
        """
        Windows: 使用 subprocess.PIPE 交互模式

        Windows 不支持 pty 模块，使用标准输入/输出管道
        """
        # 运行前验证路径
        if not self.project_dir.exists():
            logger.error(f"项目目录不存在: {self.project_dir}")
            return {
                "success": False,
                "output": "",
                "summary": "",
                "error": f"项目目录不存在: {self.project_dir}"
            }

        if not self.project_dir.is_dir():
            logger.error(f"项目路径不是目录: {self.project_dir}")
            return {
                "success": False,
                "output": "",
                "summary": "",
                "error": f"路径不是目录: {self.project_dir}"
            }

        process = None
        output_buffer = []

        try:
            # 使用绝对路径并规范化
            cwd_path = str(self.project_dir.resolve())

            process = subprocess.Popen(
                ['claude'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd_path,
                encoding='utf-8',
                errors='replace'
            )

            logger.info(f"Claude 已启动 (PID: {process.pid})")

            # 发送命令
            stdout, stderr = process.communicate(
                input=(command + '\n'),
                timeout=self.timeout
            )

            output = stdout or stderr
            summary = self._extract_summary(output)
            self._save_summary(summary, command)

            return {
                "success": process.returncode == 0 or bool(output),
                "output": output,
                "summary": summary,
                "error": None
            }

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            logger.error(f"执行超时 ({self.timeout}s)")
            return {
                "success": False,
                "output": ''.join(output_buffer),
                "summary": "",
                "error": f"执行超时 ({self.timeout}s)"
            }
        except Exception as e:
            logger.error(f"Windows模式执行失败: {e}")
            return {
                "success": False,
                "output": ''.join(output_buffer),
                "summary": "",
                "error": str(e)
            }

    def _run_unix_pty_mode(self, command: str) -> Dict:
        """
        Unix/Linux: 使用 PTY 伪终端模式执行
        """
        import pty
        import select

        master_fd = slave_fd = None
        process = None
        output_buffer = []

        try:
            master_fd, slave_fd = pty.openpty()

            process = subprocess.Popen(
                ['claude'],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                text=False,
                close_fds=True,
                cwd=str(self.project_dir)
            )
            os.close(slave_fd)
            slave_fd = None

            logger.info(f"Claude 已启动 (PID: {process.pid})")
            time.sleep(1)

            os.write(master_fd, (command + '\n').encode('utf-8'))
            logger.info("命令已发送")

            idle_count = 0
            max_idle = 50
            start_time = time.time()

            while (time.time() - start_time) < self.timeout:
                if process.poll() is not None:
                    logger.info(f"进程已退出 (退出码: {process.returncode})")
                    break

                if select.select([master_fd], [], [], 0.1)[0]:
                    try:
                        data = os.read(master_fd, 4096)
                        if data:
                            output_buffer.append(data.decode('utf-8', errors='replace'))
                            idle_count = 0
                    except OSError:
                        break
                else:
                    idle_count += 1

                if idle_count >= max_idle:
                    logger.info("检测到空闲，发送 EOF 退出")
                    os.write(master_fd, b'\x04')
                    time.sleep(0.5)
                    try:
                        while select.select([master_fd], [], [], 0.5)[0]:
                            data = os.read(master_fd, 4096)
                            if not data:
                                break
                            output_buffer.append(data.decode('utf-8', errors='replace'))
                    except OSError:
                        pass
                    break

            full_output = ''.join(output_buffer)
            summary = self._extract_summary(full_output)
            self._save_summary(summary, command)

            return {
                "success": True,
                "output": full_output,
                "summary": summary,
                "error": None
            }

        except Exception as e:
            logger.error(f"PTY模式执行失败: {e}")
            return {
                "success": False,
                "output": ''.join(output_buffer),
                "summary": "",
                "error": str(e)
            }
        finally:
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

    def _strip_ansi(self, text: str) -> str:
        """移除 ANSI 转义序列"""
        ansi_csi = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
        ansi_osc = re.compile(r'\x1b\][^\x07\x1b]*[\x07\x1b\\]')

        text = ansi_csi.sub('', text)
        text = ansi_osc.sub('', text)

        cleaned = []
        for char in text:
            code = ord(char)
            if code >= 32 or code in (9, 10):
                cleaned.append(char)
        return ''.join(cleaned)

    def _extract_summary(self, output: str) -> str:
        """
        从 Claude Code 输出中提取任务总结

        Args:
            output: 原始输出

        Returns:
            提取的总结
        """
        clean_output = self._strip_ansi(output)

        summary_keywords = ['Total cost:', '会话总结', 'Session Summary']
        summary_start = -1

        for keyword in summary_keywords:
            idx = clean_output.find(keyword)
            if idx != -1:
                summary_start = idx
                break

        if summary_start == -1:
            logger.info("未找到标准总结格式，返回完整输出")
            return clean_output.strip()

        summary = clean_output[summary_start:].strip()
        summary = re.sub(r'\n{3,}', '\n\n', summary)

        return summary

    def _save_summary(self, summary: str, command: str) -> None:
        """保存总结到文件"""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        content = f"""{'=' * 60}
Claude Code 任务总结
时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
命令: {command[:100]}...
{'=' * 60}

{summary}

{'=' * 60}
"""

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"总结已保存到: {self.output_file}")

    def read_output_file(self) -> str:
        """读取输出文件内容"""
        try:
            if self.output_file.exists():
                return self.output_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"读取输出文件失败: {e}")
        return ""
