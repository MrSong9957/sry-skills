#!/usr/bin/env python3
"""
邮件双向通信系统主入口
监听邮件 → 解析命令 → 执行Claude → 发送结果
"""

import signal
import sys
import logging
import time
import os
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from mail.parser import EmailParser
from mail.receiver import EmailReceiver
from mail.sender import EmailSender
from queue.manager import CommandQueue
from core.executor import ClaudeExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('email_bridge.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmailCommandApp:
    """邮件命令应用"""

    def __init__(self):
        """初始化应用"""
        self.settings = get_settings()
        self.running = False
        self.shutdown_requested = False

        # 初始化组件
        self.queue = CommandQueue(self.settings.get_db_path())
        self.executor = ClaudeExecutor(
            output_file=Path(self.settings.get_output_file()),
            timeout=self.settings.get_claude_timeout()
        )
        self.executor.set_project_dir(self.settings.get_project_dir())

        # 获取配置
        imap_config = self.settings.get_imap_config()
        smtp_config = self.settings.get_smtp_config()

        # 初始化邮件组件（稍后连接）
        self.receiver = EmailReceiver(
            server=imap_config["server"],
            port=imap_config["port"],
            username=imap_config["username"],
            password=imap_config["password"]
        )

        self.sender = EmailSender(
            server=smtp_config["server"],
            port=smtp_config["port"],
            username=smtp_config["username"],
            password=smtp_config["password"]
        )

        self.parser = EmailParser(whitelist=self.settings.get_whitelist())

        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，准备优雅停机...")
        self.shutdown_requested = True

    def start(self):
        """启动应用"""
        logger.info("=" * 60)
        logger.info("邮件双向通信系统启动")
        logger.info("=" * 60)

        # 连接邮件服务
        if not self._connect_email_services():
            logger.error("邮件服务连接失败，退出")
            return

        # 重置卡住的命令
        stuck_count = self.queue.reset_stuck_commands()
        if stuck_count > 0:
            logger.info(f"重置了 {stuck_count} 个卡住的命令")

        self.running = True
        logger.info("系统启动完成，开始监听邮件...")

        # 主循环
        try:
            while self.running and not self.shutdown_requested:
                self._loop_iteration()
        except KeyboardInterrupt:
            logger.info("用户中断")
        finally:
            self._shutdown()

    def _connect_email_services(self) -> bool:
        """连接邮件服务"""
        # IMAP连接
        if not self.receiver.connect():
            logger.error("IMAP连接失败")
            return False
        if not self.receiver.login():
            logger.error("IMAP登录失败")
            return False
        if not self.receiver.select_inbox():
            logger.error("选择收件箱失败")
            return False

        idle_supported = self.receiver.supports_idle()
        logger.info(f"IDLE模式: {'支持' if idle_supported else '不支持（将使用轮询）'}")

        # SMTP连接
        if not self.sender.connect():
            logger.error("SMTP连接失败")
            return False
        if not self.sender.login():
            logger.error("SMTP登录失败")
            return False

        return True

    def _loop_iteration(self):
        """单次循环迭代"""
        try:
            # 1. 接收新邮件
            self._receive_emails()

            # 2. 处理队列
            self._process_queue()

            # 3. 等待（IDLE或轮询）
            if self.receiver._idle_supported and not self.shutdown_requested:
                self.receiver.idle_wait(timeout=290)
            else:
                self.receiver.poll_wait(interval=self.settings.get_polling_interval())

            # 4. 定期清理（每小时）
            if int(time.time()) % 3600 < 30:
                self.queue.delete_old_completed(days=7)

        except Exception as e:
            logger.error(f"循环迭代异常: {e}", exc_info=True)
            time.sleep(10)

    def _receive_emails(self):
        """接收邮件并加入队列"""
        try:
            # 检查连接状态，必要时重连
            if not self.receiver._connected:
                logger.warning("IMAP连接断开，尝试重连...")
                if not self.receiver.reconnect():
                    return

            # 搜索未读邮件
            unread_uids = self.receiver.search_unread()
            logger.debug(f"发现 {len(unread_uids)} 封未读邮件")

            for uid in unread_uids:
                try:
                    raw_email = self.receiver.fetch_email(uid)
                    if not raw_email:
                        continue

                    # 解析邮件
                    parsed = self.parser.parse_email(raw_email)

                    # 检查白名单
                    if not parsed["is_whitelisted"]:
                        logger.warning(f"发件人不在白名单: {parsed['sender']}")
                        self.receiver.mark_as_read(uid)
                        continue

                    # 检查命令是否为空
                    command = parsed["command"].strip()
                    if not command:
                        logger.info("邮件正文为空，跳过")
                        self.receiver.mark_as_read(uid)
                        continue

                    # 加入队列
                    cmd_id = self.queue.enqueue(
                        sender=parsed["sender"],
                        command=command,
                        message_id=parsed["message_id"],
                        subject=parsed["subject"]
                    )

                    if cmd_id:
                        logger.info(f"命令已加入队列: id={cmd_id}, from={parsed['sender']}")

                    # 标记为已读
                    self.receiver.mark_as_read(uid)

                except Exception as e:
                    logger.error(f"处理邮件失败: {e}")

        except Exception as e:
            logger.error(f"接收邮件失败: {e}")

    def _process_queue(self):
        """处理队列中的命令"""
        cmd = self.queue.dequeue()
        if not cmd:
            return

        logger.info(f"开始处理命令: id={cmd['id']}, command={cmd['command'][:50]}...")

        try:
            # 执行命令
            result = self.executor.execute(cmd["command"])

            if result["success"]:
                # 成功
                output = result["summary"] or result["output"]
                self.queue.update_status(cmd["id"], CommandQueue.STATUS_COMPLETED, result=output)

                # 发送结果邮件
                self._send_result(cmd, output, success=True)

            else:
                # 失败
                error_msg = result.get("error", "未知错误")
                self.queue.update_status(cmd["id"], CommandQueue.STATUS_FAILED, error=error_msg)

                # 检查是否重试
                if self.queue.should_retry(cmd["id"], self.settings.get_max_retries()):
                    retry_count = self.queue.increment_retry(cmd["id"])
                    logger.warning(f"命令执行失败，将重试 ({retry_count}/{self.settings.get_max_retries()}): {error_msg}")
                    self.queue.update_status(cmd["id"], CommandQueue.STATUS_PENDING)
                else:
                    logger.error(f"命令执行失败，已达最大重试次数: {error_msg}")
                    self._send_result(cmd, error_msg, success=False)

        except Exception as e:
            logger.error(f"处理命令异常: {e}", exc_info=True)
            self.queue.update_status(cmd["id"], CommandQueue.STATUS_FAILED, error=str(e))

    def _send_result(self, cmd: dict, content: str, success: bool):
        """
        发送结果邮件

        Args:
            cmd: 命令字典
            content: 结果内容
            success: 是否成功
        """
        # 空值检查 - 防止发送空白邮件
        if not content or not content.strip():
            logger.warning(f"结果内容为空，跳过发送邮件: cmd_id={cmd.get('id')}")
            if success:
                content = "命令执行成功，但未返回任何输出。\n\n命令: " + cmd.get('command', 'N/A')
            else:
                content = f"命令执行失败，错误信息为空。\n\n命令: {cmd.get('command', 'N/A')}"

        try:
            # 确保SMTP连接正常
            if not self.sender._connected:
                if not self.sender.reconnect():
                    logger.error("SMTP重连失败，无法发送结果邮件")
                    return

            # 构建主题
            if success:
                subject = f"✅ Claude执行完成 - {cmd.get('subject', '无主题')[:30]}"
            else:
                subject = f"❌ Claude执行失败 - {cmd.get('subject', '无主题')[:30]}"

            # 发送回复邮件
            if cmd.get("message_id"):
                self.sender.send_reply(
                    to=cmd["sender"],
                    subject=subject,
                    body=content,
                    original_message_id=cmd["message_id"]
                )
            else:
                self.sender.send_email(
                    to=cmd["sender"],
                    subject=subject,
                    body=content
                )

            logger.info(f"结果邮件已发送: to={cmd['sender']}")

        except Exception as e:
            logger.error(f"发送结果邮件失败: {e}")

    def _shutdown(self):
        """优雅停机"""
        logger.info("开始优雅停机...")

        self.running = False

        # 断开邮件连接
        if self.receiver:
            self.receiver.disconnect()
        if self.sender:
            self.sender.disconnect()

        # 释放队列资源
        if self.queue:
            self.queue.close()

        # 打印统计信息
        stats = self.queue.get_stats()
        logger.info(f"队列统计: {stats}")

        logger.info("系统已停机")


def main():
    """主函数"""
    app = EmailCommandApp()
    app.start()


if __name__ == "__main__":
    main()
