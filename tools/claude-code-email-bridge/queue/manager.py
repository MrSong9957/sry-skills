#!/usr/bin/env python3
"""
SQLite命令队列管理器
支持任务状态跟踪、重试机制、文件锁
"""

import sqlite3
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

# 跨平台文件锁
if sys.platform == 'win32':
    import msvcrt
    import os
else:
    import fcntl

logger = logging.getLogger(__name__)


class CommandQueue:
    """SQLite命令队列管理器"""

    # 状态常量
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __init__(self, db_path: str = "commands.db", use_lock: bool = True):
        """
        初始化队列管理器

        Args:
            db_path: 数据库文件路径
            use_lock: 是否使用文件锁（测试环境可设为False）
        """
        # 转换为绝对路径
        db_path_obj = Path(db_path).resolve()
        self.db_path = str(db_path_obj)
        self.lock_file_path = str(db_path_obj.parent / f"{db_path_obj.name}.lock")
        self.lock_fd = None
        self._use_lock = use_lock

        # 确保目录存在
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    command TEXT NOT NULL,
                    message_id TEXT,
                    subject TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    result TEXT,
                    error TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON commands(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_message_id ON commands(message_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON commands(created_at)")

            conn.commit()

    def _acquire_lock(self) -> bool:
        """
        获取文件锁（跨平台）

        Returns:
            是否成功获取锁
        """
        if not self._use_lock:
            return True

        try:
            self.lock_fd = open(self.lock_file_path, 'w')

            if sys.platform == 'win32':
                # Windows: 使用 msvcrt.locking
                try:
                    msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
                except (IOError, OSError):
                    logger.warning("无法获取文件锁（Windows），可能有其他进程正在运行")
                    return False
            else:
                # Unix: 使用 fcntl
                try:
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    logger.warning("无法获取文件锁（Unix），可能有其他进程正在运行")
                    return False

            return True
        except (IOError, OSError) as e:
            logger.warning(f"无法获取文件锁: {e}")
            return False

    def _release_lock(self) -> None:
        """释放文件锁（跨平台）"""
        if self.lock_fd:
            try:
                if sys.platform == 'win32':
                    # Windows: 解锁
                    try:
                        self.lock_fd.seek(0)
                        msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass
                else:
                    # Unix: 解锁
                    try:
                        fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                    except:
                        pass

                self.lock_fd.close()
            except Exception as e:
                logger.warning(f"释放文件锁时出错: {e}")
            finally:
                self.lock_fd = None

    def enqueue(
        self,
        sender: str,
        command: str,
        message_id: Optional[str] = None,
        subject: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """
        将命令加入队列

        Args:
            sender: 发件人邮箱
            command: 命令内容
            message_id: 邮件Message-ID
            subject: 邮件主题
            metadata: 额外元数据

        Returns:
            命令ID，失败返回None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO commands (sender, command, message_id, subject)
                    VALUES (?, ?, ?, ?)
                    """,
                    (sender, command, message_id, subject)
                )
                conn.commit()
                cmd_id = cursor.lastrowid
                logger.info(f"命令入队: id={cmd_id}, sender={sender}, command={command[:50]}...")
                return cmd_id
        except sqlite3.IntegrityError:
            logger.warning(f"命令已存在（重复邮件）: message_id={message_id}")
            return None
        except Exception as e:
            logger.error(f"命令入队失败: {e}")
            return None

    def dequeue(self) -> Optional[Dict]:
        """
        从队列取出一个待处理命令

        Returns:
            命令字典，无可用命令返回None
        """
        # 获取文件锁
        if not self._acquire_lock():
            return None

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # 先获取待处理命令
                cursor = conn.execute(
                    """
                    SELECT * FROM commands
                    WHERE status = ?
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (self.STATUS_PENDING,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                cmd_id = row["id"]

                # 更新状态为处理中
                conn.execute(
                    """
                    UPDATE commands
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (self.STATUS_PROCESSING, cmd_id)
                )
                conn.commit()

                # 再次查询以获取更新后的数据
                cursor = conn.execute("SELECT * FROM commands WHERE id = ?", (cmd_id,))
                updated_row = cursor.fetchone()

                logger.info(f"命令出队: id={cmd_id}")
                return dict(updated_row)

        except Exception as e:
            logger.error(f"命令出队失败: {e}")
            return None
        finally:
            self._release_lock()

    def update_status(
        self,
        cmd_id: int,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        更新命令状态

        Args:
            cmd_id: 命令ID
            status: 新状态
            result: 执行结果
            error: 错误信息

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status == self.STATUS_COMPLETED:
                    conn.execute(
                        """
                        UPDATE commands
                        SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (status, result, cmd_id)
                    )
                elif status == self.STATUS_FAILED:
                    conn.execute(
                        """
                        UPDATE commands
                        SET status = ?, error = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (status, error, cmd_id)
                    )
                else:
                    conn.execute(
                        """
                        UPDATE commands
                        SET status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (status, cmd_id)
                    )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
            return False

    def increment_retry(self, cmd_id: int) -> int:
        """
        增加重试计数

        Args:
            cmd_id: 命令ID

        Returns:
            新的重试计数
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE commands
                    SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (cmd_id,)
                )
                conn.commit()

                cursor = conn.execute("SELECT retry_count FROM commands WHERE id = ?", (cmd_id,))
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"增加重试计数失败: {e}")
            return 0

    def should_retry(self, cmd_id: int, max_retries: int = 3) -> bool:
        """
        检查命令是否应该重试

        Args:
            cmd_id: 命令ID
            max_retries: 最大重试次数

        Returns:
            是否应该重试
        """
        cmd = self.get_by_id(cmd_id)
        if not cmd:
            return False

        return cmd.get("retry_count", 0) < max_retries

    def get_by_id(self, cmd_id: int) -> Optional[Dict]:
        """
        根据ID获取命令

        Args:
            cmd_id: 命令ID

        Returns:
            命令字典，不存在返回None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM commands WHERE id = ?", (cmd_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"获取命令失败: {e}")
            return None

    def get_pending_commands(self, limit: int = 10) -> List[Dict]:
        """
        获取待处理命令列表

        Args:
            limit: 最大数量

        Returns:
            命令列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM commands
                    WHERE status = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (self.STATUS_PENDING, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取待处理命令失败: {e}")
            return []

    def get_failed_commands(self, limit: int = 10) -> List[Dict]:
        """
        获取失败命令列表

        Args:
            limit: 最大数量

        Returns:
            命令列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM commands
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (self.STATUS_FAILED, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取失败命令失败: {e}")
            return []

    def delete_old_completed(self, days: int = 7) -> int:
        """
        删除旧的已完成命令

        Args:
            days: 保留天数

        Returns:
            删除的命令数量
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM commands
                    WHERE status IN ('completed', 'failed')
                    AND completed_at < datetime('now', '-' || ? || ' days')
                    """,
                    (days,)
                )
                conn.commit()
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.info(f"清理旧命令: {deleted} 条")
                return deleted
        except Exception as e:
            logger.error(f"清理旧命令失败: {e}")
            return 0

    def get_stats(self) -> Dict[str, int]:
        """
        获取队列统计信息

        Returns:
            统计字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}

                for status in [self.STATUS_PENDING, self.STATUS_PROCESSING,
                             self.STATUS_COMPLETED, self.STATUS_FAILED]:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM commands WHERE status = ?",
                        (status,)
                    )
                    stats[status] = cursor.fetchone()[0]

                return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def reset_stuck_commands(self, timeout_minutes: int = 30) -> int:
        """
        重置卡住的命令（处理中但超时）

        Args:
            timeout_minutes: 超时时间（分钟）

        Returns:
            重置的命令数量
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE commands
                    SET status = 'pending', updated_at = CURRENT_TIMESTAMP
                    WHERE status = 'processing'
                    AND updated_at < datetime('now', '-' || ? || ' minutes')
                    """,
                    (timeout_minutes,)
                )
                conn.commit()
                reset = cursor.rowcount
                if reset > 0:
                    logger.warning(f"重置卡住的命令: {reset} 条")
                return reset
        except Exception as e:
            logger.error(f"重置卡住的命令失败: {e}")
            return 0

    def close(self) -> None:
        """
        关闭队列管理器，释放所有资源

        应在应用退出时调用以确保文件锁和数据库连接正确释放
        """
        logger.info("关闭队列管理器，释放资源...")
        self._release_lock()
        logger.info("队列管理器已关闭")
