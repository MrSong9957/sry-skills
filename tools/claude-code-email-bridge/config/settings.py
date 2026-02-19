#!/usr/bin/env python3
"""
邮件双向通信系统配置模块
从环境变量加载配置，优先从项目根目录.env加载
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Settings:
    """环境变量配置加载器"""

    # 默认值
    DEFAULT_IMAP_SERVER = "imap.qq.com"
    DEFAULT_IMAP_PORT = 993
    DEFAULT_SMTP_SERVER = "smtp.qq.com"
    DEFAULT_SMTP_PORT = 465
    DEFAULT_POLLING_INTERVAL = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_DB_PATH = "commands.db"
    DEFAULT_CLAUDE_TIMEOUT = 3600

    def __init__(self):
        """初始化配置"""
        self._load_env_files()
        self._validate()

    def _load_env_files(self) -> None:
        """
        从.env文件加载环境变量
        优先级：项目根目录.env > 模块目录.env
        """
        # 获取项目根目录（向上查找包含.env的目录）
        current_dir = Path(__file__).resolve()
        env_files = []

        # 当前模块的.env
        module_env = current_dir.parent.parent / ".env"
        if module_env.exists():
            env_files.append(module_env)

        # 项目根目录的.env（向上查找）
        root_env = current_dir
        for _ in range(5):  # 最多向上5层
            root_env = root_env.parent
            if (root_env / ".env").exists():
                env_files.append(root_env / ".env")
                break

        # 按优先级加载（项目根目录优先）
        for env_file in reversed(env_files):
            self._load_env_file(env_file)

    def _load_env_file(self, env_file: Path) -> None:
        """加载单个.env文件"""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue
                    # 解析 KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 只设置未设置的环境变量
                        if key and os.getenv(key) is None:
                            os.environ[key] = value
        except Exception as e:
            print(f"警告: 加载 {env_file} 失败: {e}")

    def get_imap_config(self) -> dict:
        """获取IMAP配置"""
        return {
            "server": os.getenv("IMAP_SERVER", self.DEFAULT_IMAP_SERVER),
            "port": int(os.getenv("IMAP_PORT", str(self.DEFAULT_IMAP_PORT))),
            "username": os.getenv("EMAIL_USERNAME", ""),
            "password": os.getenv("EMAIL_PASSWORD", ""),
        }

    def get_smtp_config(self) -> dict:
        """获取SMTP配置"""
        return {
            "server": os.getenv("SMTP_SERVER", self.DEFAULT_SMTP_SERVER),
            "port": int(os.getenv("SMTP_PORT", str(self.DEFAULT_SMTP_PORT))),
            "username": os.getenv("EMAIL_USERNAME", ""),
            "password": os.getenv("EMAIL_PASSWORD", ""),
        }

    def get_whitelist(self) -> list:
        """获取白名单发件人列表"""
        whitelist = os.getenv("EMAIL_WHITELIST", "")
        return [email.strip() for email in whitelist.split(",") if email.strip()]

    def get_db_path(self) -> str:
        """获取数据库路径（默认在模块目录下）"""
        default_path = Path(__file__).parent.parent / self.DEFAULT_DB_PATH
        env_path = os.getenv("DATABASE_PATH")
        return str(env_path) if env_path else str(default_path)

    def get_polling_interval(self) -> int:
        """获取轮询间隔（秒）"""
        return int(os.getenv("POLLING_INTERVAL", str(self.DEFAULT_POLLING_INTERVAL)))

    def get_max_retries(self) -> int:
        """获取最大重试次数"""
        return int(os.getenv("MAX_RETRIES", str(self.DEFAULT_MAX_RETRIES)))

    def get_claude_timeout(self) -> int:
        """获取Claude执行超时（秒）"""
        return int(os.getenv("CLAUDE_TIMEOUT", str(self.DEFAULT_CLAUDE_TIMEOUT)))

    def get_project_dir(self) -> str:
        """
        获取项目目录（带验证和智能检测）

        Returns:
            项目目录的绝对路径字符串
        """
        # 优先使用环境变量
        env_dir = os.getenv("CLAUDE_PROJECT_DIR")
        if env_dir:
            p = Path(env_dir).resolve()
            if p.exists() and p.is_dir():
                logger.info(f"使用环境变量指定的项目目录: {p}")
                return str(p)
            logger.warning(f"环境变量 CLAUDE_PROJECT_DIR 指向的目录不存在: {env_dir}")

        # 智能检测: 向上查找包含 .git 或 .claude 的目录
        current_dir = Path(__file__).resolve().parent
        for _ in range(6):  # 最多向上6层
            # 检查是否为项目根目录
            if (current_dir / ".git").exists() or (current_dir / ".claude").exists():
                logger.info(f"检测到项目根目录: {current_dir}")
                return str(current_dir)
            current_dir = current_dir.parent

        # 回退: 使用当前工作目录
        cwd = Path.cwd().resolve()
        logger.warning(f"未检测到项目根目录，使用当前工作目录: {cwd}")
        return str(cwd)

    def get_output_file(self) -> str:
        """获取输出文件路径（默认在模块目录下）"""
        default_path = Path(__file__).parent.parent / "claude_output.txt"
        env_path = os.getenv("CLAUDE_OUTPUT_FILE")
        return str(env_path) if env_path else str(default_path)

    def _validate(self) -> None:
        """验证必需配置"""
        required = ["EMAIL_USERNAME", "EMAIL_PASSWORD"]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            print(f"错误: 缺少必需的环境变量: {', '.join(missing)}")
            print(f"请在项目根目录的.env文件中添加:")
            print("  EMAIL_USERNAME=274504958@qq.com")
            print("  EMAIL_PASSWORD=your_qq_auth_code")
            print("  EMAIL_WHITELIST=18669209957@163.com")
            sys.exit(1)

        # 验证白名单
        if not self.get_whitelist():
            print("警告: 未设置EMAIL_WHITELIST，将接受所有发件人的邮件")


# 单例实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
