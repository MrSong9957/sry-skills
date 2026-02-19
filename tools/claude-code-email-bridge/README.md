# Claude Email Bridge

通过邮件远程控制 Claude Code 的轻量级桥接工具。

## 特性

- 📧 **邮件驱动**：通过 IMAP 接收命令，SMTP 返回结果
- 🔒 **安全白名单**：只响应授权发件人的命令
- 🔄 **命令队列**：基于 SQLite 的持久化队列，支持重试
- 🤖 **Claude 集成**：直接调用 Claude Code CLI 执行命令
- 📦 **零依赖**：仅使用 Python 标准库

## 快速开始

### 1. 环境要求

- Python 3.8+
- Claude Code CLI（已安装）
- IMAP/SMTP 邮箱账号

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 邮件服务器配置
EMAIL_IMAP_SERVER=imap.example.com
EMAIL_IMAP_PORT=993
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_ACCOUNT=your@email.com
EMAIL_PASSWORD=your-password

# Claude Code 配置
CLAUDE_CODE_PATH=/usr/local/bin/claude

# 安全白名单（逗号分隔）
EMAIL_WHITELIST=user1@example.com,user2@example.com
```

### 3. 运行

```bash
python main.py
```

## 邮件命令格式

发送邮件到配置的账号，主题格式：

```
To: your@email.com
Subject: <命令>

可选的详细说明...
```

## 模块说明

| 模块 | 文件 | 功能 |
|-----|------|------|
| 主入口 | `main.py` | 应用启动、主循环 |
| 配置 | `config/settings.py` | 环境变量加载 |
| 邮件解析 | `mail/parser.py` | 提取命令、白名单验证 |
| 邮件接收 | `mail/receiver.py` | IMAP + IDLE 实时接收 |
| 邮件发送 | `mail/sender.py` | SMTP 发送结果 |
| 队列管理 | `queue/manager.py` | SQLite 命令队列 |
| 执行器 | `core/executor.py` | Claude Code 执行 |

## 可移植性

所有模块均可独立移植到其他项目：

- `queue/manager.py` - 通用任务队列
- `mail/*.py` - 邮件处理系统
- `config/settings.py` - 配置加载器
- `core/executor.py` - Claude Code 集成

## 注意事项

### Windows 兼容性

`queue/manager.py` 使用了 Unix 专用的 `fcntl` 文件锁。

在 Windows 上运行时，需要修改为：
- `msvcrt.locking`（Windows 原生）
- `filelock` 库（跨平台）
- 或移除文件锁，依赖 SQLite 事务

### 安全建议

- 使用应用专用密码（而非账户密码）
- 启用 IMAP/SMTP 的 SSL/TLS 加密
- 严格配置白名单
- 定期审查命令历史

## 许可证

MIT License
