#!/usr/bin/env python3
"""
SMTP邮件发送器
支持SSL/TLS加密、长内容截断、附件
"""

import smtplib
import email
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    """SMTP邮件发送器"""

    # 长内容截断阈值
    MAX_BODY_LENGTH = 50000

    def __init__(self, server: str, port: int, username: str, password: str):
        """
        初始化发送器

        Args:
            server: SMTP服务器地址
            port: SMTP端口
            username: 用户名
            password: 密码/授权码
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.client: Optional[smtplib.SMTP_SSL] = None
        self._connected = False

    def connect(self) -> bool:
        """
        连接到SMTP服务器

        Returns:
            连接是否成功
        """
        try:
            self.client = smtplib.SMTP_SSL(self.server, self.port, timeout=30)
            self._connected = True
            logger.info(f"SMTP连接成功: {self.server}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"SMTP连接失败: {e}")
            self._connected = False
            return False

    def login(self) -> bool:
        """
        登录到邮箱

        Returns:
            登录是否成功
        """
        if not self.client or not self._connected:
            logger.error("未连接到服务器")
            return False

        try:
            self.client.login(self.username, self.password)
            logger.info(f"SMTP登录成功: {self.username}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            return False

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        original_message_id: Optional[str] = None
    ) -> bool:
        """
        发送邮件

        Args:
            to: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            html: 是否为HTML格式
            original_message_id: 原始邮件ID（用于回复）

        Returns:
            发送是否成功
        """
        if not self.client or not self._connected:
            logger.error("未连接到服务器")
            return False

        try:
            # 处理长内容
            content, is_truncated = self._prepare_content(body)

            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = to
            msg["Subject"] = subject
            msg["Date"] = email.utils.formatdate(localtime=True)

            # 设置回复头
            if original_message_id:
                msg["In-Reply-To"] = original_message_id
                msg["References"] = original_message_id

            # 添加正文
            subtype = "html" if html else "plain"
            msg.attach(MIMEText(content, subtype, "utf-8"))

            # 如果内容被截断，添加完整附件
            if is_truncated:
                attachment = MIMEApplication(body.encode("utf-8"))
                filename = f"claude_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                attachment.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(attachment)

            # 发送
            self.client.send_message(msg)
            logger.info(f"邮件发送成功: to={to}, subject={subject[:30]}...")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def send_reply(
        self,
        to: str,
        subject: str,
        body: str,
        original_message_id: str,
        html: bool = False
    ) -> bool:
        """
        回复邮件

        Args:
            to: 收件人邮箱
            subject: 回复主题
            body: 回复正文
            original_message_id: 原始邮件ID
            html: 是否为HTML格式

        Returns:
            发送是否成功
        """
        # 添加Re:前缀（如果没有）
        if not subject.startswith("Re:") and not subject.startswith("RE:"):
            subject = f"Re: {subject}"

        return self.send_email(to, subject, body, html, original_message_id)

    def _prepare_content(self, content: str) -> tuple:
        """
        处理内容，返回处理后的内容和是否被截断

        Args:
            content: 原始内容

        Returns:
            (处理后的内容, 是否被截断)
        """
        is_truncated = len(content) > self.MAX_BODY_LENGTH

        if is_truncated:
            body = content[:self.MAX_BODY_LENGTH]
            footer = f"\n\n{'=' * 60}\n"
            footer += f"⚠️ 内容已截断 ({len(content)} 字符 → {self.MAX_BODY_LENGTH} 字符)\n"
            footer += f"📎 完整内容见附件\n"
            footer += f"📅 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return body + footer, True

        return content, False

    def disconnect(self) -> bool:
        """
        断开连接

        Returns:
            是否成功
        """
        if self.client:
            try:
                self.client.quit()
            except:
                pass
            finally:
                self.client = None
                self._connected = False
        return True

    def reconnect(self) -> bool:
        """
        重新连接

        Returns:
            是否成功
        """
        self.disconnect()
        time.sleep(1)

        if not self.connect():
            return False
        if not self.login():
            return False

        return True

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
        return False
