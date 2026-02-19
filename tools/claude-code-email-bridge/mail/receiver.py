#!/usr/bin/env python3
"""
IMAP邮件接收器
支持IDLE模式和轮询降级
"""

import imaplib
import email
import logging
import select
import time
from typing import List, Optional
from email.message import Message

logger = logging.getLogger(__name__)


class EmailReceiver:
    """IMAP邮件接收器"""

    def __init__(self, server: str, port: int, username: str, password: str):
        """
        初始化接收器

        Args:
            server: IMAP服务器地址
            port: IMAP端口
            username: 用户名
            password: 密码/授权码
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.client: Optional[imaplib.IMAP4_SSL] = None
        self._idle_supported = False
        self._connected = False

    def connect(self) -> bool:
        """
        连接到IMAP服务器

        Returns:
            连接是否成功
        """
        try:
            self.client = imaplib.IMAP4_SSL(self.server, self.port)
            self._connected = True
            logger.info(f"IMAP连接成功: {self.server}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"IMAP连接失败: {e}")
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
            logger.info(f"IMAP登录成功: {self.username}")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP登录失败: {e}")
            return False

    def select_inbox(self) -> bool:
        """
        选择收件箱

        Returns:
            是否成功
        """
        if not self.client:
            return False

        try:
            self.client.select("INBOX")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"选择收件箱失败: {e}")
            return False

    def supports_idle(self) -> bool:
        """
        检查服务器是否支持IDLE命令

        Returns:
            是否支持IDLE
        """
        if not self.client:
            return False

        # 同时检查服务器能力和客户端（imaplib）是否支持IDLE
        server_supports = "IDLE" in self.client.capabilities
        client_supports = hasattr(self.client, 'idle')
        self._idle_supported = server_supports and client_supports
        logger.info(f"IDLE支持: {self._idle_supported} (服务器={server_supports}, 客户端={client_supports})")
        return self._idle_supported

    def search_unread(self) -> List[bytes]:
        """
        搜索未读邮件

        Returns:
            未读邮件UID列表
        """
        if not self.client:
            return []

        try:
            status, messages = self.client.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                return []
            return messages[0].split()
        except imaplib.IMAP4.error as e:
            logger.error(f"搜索邮件失败: {e}")
            return []

    def fetch_email(self, uid: bytes) -> Optional[bytes]:
        """
        获取邮件内容

        Args:
            uid: 邮件UID

        Returns:
            邮件原始字节，失败返回None
        """
        if not self.client:
            return None

        try:
            status, data = self.client.fetch(uid, "(RFC822)")
            if status != "OK":
                return None

            for response in data:
                if isinstance(response, tuple):
                    return response[1]
            return None
        except imaplib.IMAP4.error as e:
            logger.error(f"获取邮件失败: {e}")
            return None

    def mark_as_read(self, uid: bytes) -> bool:
        """
        标记邮件为已读

        Args:
            uid: 邮件UID

        Returns:
            是否成功
        """
        if not self.client:
            return False

        try:
            self.client.store(uid, "+FLAGS", "\\Seen")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"标记已读失败: {e}")
            return False

    def idle_wait(self, timeout: int = 290) -> bool:
        """
        IDLE模式等待新邮件

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否有新邮件
        """
        if not self.client or not self._idle_supported:
            return False

        try:
            # 发送IDLE命令
            self.client.idle()
            logger.debug("进入IDLE模式")

            # 等待服务器推送
            self.client.idle_check(timeout=timeout)

            # 退出IDLE
            self.client.idle_done()
            return True
        except imaplib.IMAP4.abort:
            logger.warning("IDLE连接中断")
            try:
                self.client.idle_done()
            except:
                pass
            return False
        except Exception as e:
            logger.warning(f"IDLE等待失败: {e}")
            try:
                self.client.idle_done()
            except:
                pass
            return False

    def poll_wait(self, interval: int = 30) -> bool:
        """
        轮询等待（降级方案）

        Args:
            interval: 轮询间隔（秒）

        Returns:
            True（总是返回，表示轮询完成）
        """
        logger.debug(f"轮询等待 {interval} 秒")
        time.sleep(interval)
        return True

    def disconnect(self) -> bool:
        """
        断开连接

        Returns:
            是否成功
        """
        if self.client:
            try:
                self.client.close()
                self.client.logout()
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
        if not self.select_inbox():
            return False

        self.supports_idle()
        return True

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        self.login()
        self.select_inbox()
        self.supports_idle()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
        return False
