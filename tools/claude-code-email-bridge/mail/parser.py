#!/usr/bin/env python3
"""
邮件解析器
从EmailMessage提取命令和元数据
"""

import email
import re
import logging
from email.message import Message
from typing import Optional, Dict, Any
from email.header import decode_header

logger = logging.getLogger(__name__)


class EmailParser:
    """邮件解析器"""

    def __init__(self, whitelist: list = None):
        """
        初始化解析器

        Args:
            whitelist: 发件人白名单列表
        """
        self.whitelist = whitelist or []

    def set_whitelist(self, whitelist: list) -> None:
        """设置白名单"""
        self.whitelist = whitelist

    def extract_sender(self, msg: Message) -> str:
        """
        提取发件人邮箱地址

        Args:
            msg: EmailMessage对象

        Returns:
            发件人邮箱地址
        """
        from_header = msg.get("From", "")
        if not from_header:
            return ""

        # 解析From头，可能包含名称
        # 例如: "John Doe <john@example.com>" 或 john@example.com
        match = re.search(r"<(.+?)>", from_header)
        if match:
            return match.group(1).strip()

        # 没有尖括号，直接返回
        return from_header.strip()

    def is_sender_whitelisted(self, sender: str) -> bool:
        """
        检查发件人是否在白名单中

        Args:
            sender: 发件人邮箱

        Returns:
            是否在白名单中
        """
        if not self.whitelist:
            # 没有设置白名单，接受所有发件人
            return True

        sender_lower = sender.lower()
        return any(allowed.lower() in sender_lower for allowed in self.whitelist)

    def extract_command(self, msg: Message) -> str:
        """
        提取邮件正文作为命令

        Args:
            msg: EmailMessage对象

        Returns:
            命令文本
        """
        body = self._get_body(msg)
        # 去除引用内容
        body = self._strip_replies(body)
        return body.strip()

    def extract_message_id(self, msg: Message) -> Optional[str]:
        """
        提取邮件Message-ID用于回复

        Args:
            msg: EmailMessage对象

        Returns:
            Message-ID或None
        """
        return msg.get("Message-ID")

    def extract_subject(self, msg: Message) -> str:
        """
        提取邮件主题

        Args:
            msg: EmailMessage对象

        Returns:
            解码后的主题
        """
        subject = msg.get("Subject", "")
        return self._decode_header(subject)

    def parse_email(self, raw_email: bytes) -> Dict[str, Any]:
        """
        解析原始邮件字节

        Args:
            raw_email: 原始邮件字节

        Returns:
            包含解析结果的字典
        """
        msg = email.message_from_bytes(raw_email)

        sender = self.extract_sender(msg)
        message_id = self.extract_message_id(msg)
        subject = self.extract_subject(msg)
        command = self.extract_command(msg)

        return {
            "sender": sender,
            "message_id": message_id,
            "subject": subject,
            "command": command,
            "is_whitelisted": self.is_sender_whitelisted(sender),
        }

    def _get_body(self, msg: Message) -> str:
        """
        提取邮件正文（纯文本优先）

        Args:
            msg: EmailMessage对象

        Returns:
            邮件正文
        """
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # 跳过附件
                if "attachment" in content_disposition:
                    continue

                # 优先获取纯文本
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(charset, errors="ignore")
                        return body

            # 没有纯文本，尝试HTML
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        html = payload.decode(charset, errors="ignore")
                        return self._html_to_text(html)
        else:
            # 单部分邮件
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload:
                content = payload.decode(charset, errors="ignore")
                if msg.get_content_type() == "text/html":
                    return self._html_to_text(content)
                return content

        return body

    def _html_to_text(self, html: str) -> str:
        """
        简单的HTML转纯文本

        Args:
            html: HTML内容

        Returns:
            纯文本内容
        """
        # 移除HTML标签
        text = re.sub(r"<[^>]+>", " ", html)
        # 移除多余的空白
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _strip_replies(self, text: str) -> str:
        """
        去除邮件回复引用内容

        Args:
            text: 邮件正文

        Returns:
            去除引用后的正文
        """
        lines = text.split("\n")
        result = []

        for line in lines:
            # 跳过引用行
            if line.strip().startswith(">"):
                continue
            # 跳过常见的回复分隔符
            if re.match(r"^[-_]{3,}\s*(Original|Reply|Forward)", line, re.IGNORECASE):
                break
            if re.match(r"^On.*wrote:", line):
                break
            result.append(line)

        return "\n".join(result).strip()

    def _decode_header(self, header: str) -> str:
        """
        解码邮件头

        Args:
            header: 邮件头字符串

        Returns:
            解码后的字符串
        """
        if not header:
            return ""

        decoded_parts = decode_header(header)
        result = []

        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                charset = charset or "utf-8"
                try:
                    result.append(part.decode(charset, errors="ignore"))
                except (LookupError, UnicodeDecodeError):
                    result.append(part.decode("utf-8", errors="ignore"))
            else:
                result.append(str(part))

        return "".join(result)
