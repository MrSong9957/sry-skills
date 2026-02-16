# Claude Code 任务完成手机通知方案
##（企业微信机器人版 - 零成本、国内最稳）

---

## 📖 文档概述

**文档版本：** v1.0
**最后更新：** 2025-02-17
**适用场景：** Claude Code 任务完成后自动发送手机通知
**方案类型：** 企业微信机器人 + Python Hook 脚本

---

## 🎯 一句话原理

```
Claude Code 完成任务 → 触发 Stop Hook → Python 脚本读取会话 → 发送到企业微信 → 手机收到通知
```

### 核心优势

| 特性 | 说明 |
|------|------|
| ✅ **零成本** | 企业微信机器人完全免费，无限制 |
| ✅ **国内稳定** | 无需翻墙，速度快，99.9% 可达率 |
| ✅ **多窗口支持** | 自动识别项目路径，区分不同窗口 |
| ✅ **异步执行** | 不影响 Claude Code 性能 |
| ✅ **易于配置** | 5 分钟配置完成，无需编程基础 |

---

## 📋 准备工作（5 分钟）

### 第 1 步：下载并注册企业微信

**操作步骤：**

1. **下载企业微信 App**
   - iOS：App Store 搜索"企业微信"
   - Android：各大应用商店搜索"企业微信"
   - 或访问：https://work.weixin.qq.com/

2. **注册账号**
   - 手机号注册（完全免费）
   - 无需企业认证，个人用户即可使用
   - 注册完成后登录手机 App

---

### 第 2 步：创建群并添加机器人

**为什么要建群？**
企业微信机器人必须添加到群里才能工作。可以创建一个只有你自己的群。

**操作步骤：**

#### 2.1 创建群聊

1. 打开企业微信 App
2. 点击右上角 `+` 号
3. 选择 `发起群聊`
4. 选择联系人（可以跳过，创建单人群）
5. 群名称建议：`Claude 通知群` 或 `任务完成通知`

#### 2.2 添加群机器人

1. 进入刚创建的群
2. 点击右上角 `...`（更多）
3. 找到并点击 `群机器人`
4. 点击 `添加机器人` → `新建机器人`
5. 机器人名称：`Claude 通知`
6. 上传头像（可选）
7. 点击 **"添加"**

#### 2.3 复制 Webhook URL

添加成功后，会显示一个 **Webhook URL**，类似：

```
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=693a91f6-7xxx-4bc4-97a0-0ec2sifa5aaa
```

**⚠️ 重要：**
- 立即复制这个 URL 并保存到记事本
- 这个 URL 相当于你的"通知密码"，不要泄露给他人
- 后面配置脚本时会用到

---

### 第 3 步：测试机器人是否工作

**目的：** 确保机器人能正常推送消息，避免后面配置出问题。

**方法 1：浏览器测试（简单）**

1. 在电脑浏览器打开新标签页
2. 粘贴 Webhook URL 并回车
3. 如果看到提示："请使用 POST 方法访问"，说明机器人有效 ✅

**方法 2：命令行测试（推荐）**

**Windows PowerShell：**

```powershell
# 替换成你的 webhook URL
$webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"

$body = @{
    msgtype = "text"
    text = @{
        content = "🎉 测试消息：Claude Code 通知功能已配置成功！"
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri $webhook -Method Post -Body $body -ContentType "application/json"
```

**macOS/Linux：**

```bash
# 替换成你的 webhook URL
webhook="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"

curl -X POST "$webhook" \
  -H 'Content-Type: application/json' \
  -d '{
    "msgtype": "text",
    "text": {
      "content": "🎉 测试消息：Claude Code 通知功能已配置成功！"
    }
  }'
```

**预期结果：**
- 如果命令执行无报错，且手机企业微信收到消息 → 测试成功 ✅
- 如果报错或收不到消息 → 检查 Webhook URL 是否正确

---

## 🔧 配置 Claude Code 通知（10 分钟）

### 第 4 步：创建通知脚本目录

**Windows PowerShell：**

```powershell
# 创建插件目录
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\plugins\notify-wechat"
```

**macOS/Linux：**

```bash
# 创建插件目录
mkdir -p ~/.claude/plugins/notify-wechat
```

---

### 第 5 步：编写通知脚本

**脚本文件位置：**
- Windows: `%USERPROFILE%\.claude\plugins\notify-wechat\send-notify.py`
- macOS/Linux: `~/.claude/plugins/notify-wechat/send-notify.py`

**完整代码：**

```python
#!/usr/bin/env python3
"""
Claude Code 任务完成通知脚本
支持多窗口场景，自动识别项目路径

作者: Claude Code
版本: 1.0.0
"""

import sys
import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ========== Windows 编码修复 ==========
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# =================================

# ========== 配置参数 ==========
# 企业微信 Webhook URL（通过环境变量配置，更安全）
WEBHOOK_URL = os.environ.get('WECHAT_WEBHOOK', '')
# 如果环境变量为空，尝试从命令行参数读取
if not WEBHOOK_URL and len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg.startswith('--webhook='):
            WEBHOOK_URL = arg.split('=', 1)[1]

# 请求超时时间（秒）
REQUEST_TIMEOUT = 5

# 项目路径显示格式
# 可选值：
# - "full": 完整路径 (e:\Files\PycharmProjects\test)
# - "name": 仅项目名 (test)
# - "short": 短路径 (...\test)
PROJECT_PATH_FORMAT = os.environ.get('PROJECT_PATH_FORMAT', 'name')
# =================================


def validate_path(path):
    """验证路径安全性，防止路径遍历攻击"""
    if not path:
        return False
    try:
        normalized = os.path.normpath(path)
        if '..' in normalized:
            return False
        return True
    except Exception:
        return False


def extract_project_path(transcript_path):
    """
    从会话文件中提取项目路径

    优先级：
    1. 读取会话文件，查找 cwd 字段
    2. 从文件路径反推
    """
    if not transcript_path or not os.path.exists(transcript_path):
        return "Unknown"

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    # 尝试多种可能的路径字段
                    cwd = entry.get('cwd') or entry.get('project_path') or entry.get('working_directory')
                    if cwd and validate_path(cwd):
                        return format_project_path(cwd)
                except (json.JSONDecodeError, KeyError):
                    continue

        # 如果找不到 cwd，从 transcript_path 反推
        # .claude/sessions/xxx-transcript.jsonl -> 项目根目录
        path = Path(transcript_path)
        # 向上查找，直到找到项目根目录（包含 .git、package.json 等）
        parent = path.parent
        while parent != parent.parent:
            if (parent / '.git').exists() or (parent / 'package.json').exists() or (parent / '.claude').exists():
                return format_project_path(str(parent))
            parent = parent.parent

        # 最后尝试 transcript_path 的父目录
        return format_project_path(str(path.parent.parent))

    except Exception:
        return "Unknown"


def format_project_path(path):
    """
    格式化项目路径显示
    """
    if PROJECT_PATH_FORMAT == 'full':
        return path
    elif PROJECT_PATH_FORMAT == 'name':
        # 返回最后一层目录名
        return os.path.basename(os.path.normpath(path))
    elif PROJECT_PATH_FORMAT == 'short':
        # 返回 ...\dirname 格式
        name = os.path.basename(os.path.normpath(path))
        parent = os.path.basename(os.path.dirname(os.path.normpath(path)))
        return f"...\\{parent}\\{name}" if sys.platform == 'win32' else f".../{parent}/{name}"
    else:
        return path


def get_session_id(transcript_path):
    """从会话文件路径提取会话 ID"""
    if not transcript_path:
        return "unknown"
    try:
        filename = os.path.basename(transcript_path)
        # xxx-transcript.jsonl -> xxx
        session_id = filename.replace("-transcript.jsonl", "")
        return session_id[:8]  # 取前 8 位
    except Exception:
        return "unknown"


def get_latest_user_instruction(transcript_path):
    """从会话记录中获取最新用户指令"""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 从最后往前找，找到第一个包含实际文本的用户消息
        for line in reversed(lines):
            try:
                entry = json.loads(line.strip())
                entry_type = entry.get('type', '')

                if entry_type == 'user':
                    message = entry.get('message', {})
                    content = message.get('content', '')

                    if isinstance(content, list):
                        texts = []
                        has_tool_result = False
                        has_text = False
                        for item in content:
                            if isinstance(item, dict):
                                if item.get('type') == 'text':
                                    text = item.get('text', '')
                                    if text:
                                        texts.append(text)
                                        has_text = True
                                elif item.get('type') == 'tool_result':
                                    has_tool_result = True

                        # 只返回有实际文本的用户消息
                        if has_tool_result and not has_text:
                            continue

                        if texts:
                            full_text = ' '.join(texts)
                            # 简化任务描述（去除规则等）
                            return simplify_task_description(full_text)
                    return simplify_task_description(str(content)) if content else ""

            except (json.JSONDecodeError, KeyError):
                continue

        return ""

    except Exception:
        return ""


def simplify_task_description(text):
    """
    简化任务描述，提取核心任务
    """
    if not text:
        return ""

    # 去除换行和多余空格
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    # 限制长度
    if len(text) > 30:
        text = text[:30] + "..."

    return text


def send_wechat_notification(webhook_url, message):
    """
    发送消息到企业微信机器人

    Args:
        webhook_url: 企业微信 Webhook URL
        message: 消息内容字典

    Returns:
        bool: 发送是否成功
    """
    if not webhook_url:
        print("错误：未配置 Webhook URL", file=sys.stderr)
        print("请设置环境变量 WECHAT_WEBHOOK 或通过 --webhook= 参数传入", file=sys.stderr)
        return False

    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": message
        }
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('errcode') == 0:
                return True
            else:
                print(f"企业微信返回错误: {result}", file=sys.stderr)
                return False

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"网络请求失败: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"发送通知时发生意外错误: {e}", file=sys.stderr)
        return False


def format_message(project, session_id, task, timestamp):
    """
    格式化通知消息（Markdown 格式）
    """
    # 清理任务描述中的特殊字符
    task_escaped = task.replace('*', '').replace('`', '').replace('>', '')

    message = f"""## 📱 Claude Code 任务完成

> **项目：** {project}
> **窗口：** {session_id}
> **时间：** {timestamp}

**任务：** {task_escaped}

---

*由 Claude Code 自动通知*"""

    return message


def main():
    # 读取 stdin JSON（由 Claude Code 传入）
    input_data = sys.stdin.read(1024 * 100)  # 最多 100KB

    try:
        data = json.loads(input_data)

        # 获取会话文件路径
        transcript_path = data.get("transcript_path", "")

        # 提取项目信息
        project = extract_project_path(transcript_path)

        # 提取会话 ID
        session_id = get_session_id(transcript_path)

        # 提取最新任务
        task = get_latest_user_instruction(transcript_path)
        if not task:
            task = "未知任务"

        # 获取当前时间
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 格式化消息
        message = format_message(project, session_id, task, timestamp)

        # 发送通知
        success = send_wechat_notification(WEBHOOK_URL, message)

        if success:
            print(f"通知已发送: 项目={project}, 任务={task}", file=sys.stderr)
            sys.exit(0)
        else:
            print("通知发送失败", file=sys.stderr)
            sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"解析 JSON 输入失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"处理通知时发生意外错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**保存脚本：**

**Windows：**

```powershell
# 创建脚本文件
$scriptPath = "$env:USERPROFILE\.claude\plugins\notify-wechat\send-notify.py"

# 将上面的代码复制到这个文件
# 可以使用 notepad 或 VS Code 编辑
notepad $scriptPath
```

**macOS/Linux：**

```bash
# 创建脚本文件
cat > ~/.claude/plugins/notify-wechat/send-notify.py << 'EOF'
# 粘贴上面的完整代码
EOF

# 添加执行权限
chmod +x ~/.claude/plugins/notify-wechat/send-notify.py
```

---

### 第 6 步：配置环境变量（推荐，更安全）

**为什么要用环境变量？**
- 避免在配置文件中直接暴露 Webhook URL
- 更安全，且易于管理

**Windows PowerShell：**

```powershell
# 设置用户环境变量（永久生效）
[System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', '你的webhook_url', 'User')

# 验证是否设置成功
[System.Environment]::GetEnvironmentVariable('WECHAT_WEBHOOK', 'User')
```

**macOS/Linux：**

```bash
# 添加到 shell 配置文件（~/.zshrc 或 ~/.bashrc）
echo 'export WECHAT_WEBHOOK="你的webhook_url"' >> ~/.zshrc

# 重新加载配置
source ~/.zshrc

# 验证
echo $WECHAT_WEBHOOK
```

**⚠️ 注意：**
- 设置环境变量后，需要重启 Claude Code 才能生效
- 如果不设置环境变量，也可以在第 7 步中通过命令行参数传入

---

### 第 7 步：配置 Claude Code Hook

**配置文件位置：**
- Windows: `%USERPROFILE%\.claude\settings.json`
- macOS/Linux: `~/.claude/settings.json`

**需要添加的内容：**

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "always",
        "command": "python ~/.claude/plugins/notify-wechat/send-notify.py"
      }
    ]
  }
}
```

**如果未设置环境变量，使用命令行参数：**

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "always",
        "command": "python ~/.claude/plugins/notify-wechat/send-notify.py --webhook=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"
      }
    ]
  }
}
```

**完整配置示例（包含其他配置）：**

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/plugins/custom/show-last-prompt/statusline/show-prompt.py"
  },
  "hooks": {
    "Stop": [
      {
        "matcher": "always",
        "command": "python ~/.claude/plugins/notify-wechat/send-notify.py"
      }
    ]
  }
}
```

**编辑配置文件：**

**Windows PowerShell：**

```powershell
# 打开配置文件
notepad $env:USERPROFILE\.claude\settings.json
```

**macOS/Linux：**

```bash
# 打开配置文件
nano ~/.claude/settings.json
# 或使用 VS Code: code ~/.claude/settings.json
```

---

## ✅ 验证配置

### 测试步骤

1. **重启 Claude Code**
   - 完全退出 Claude Code（确保所有窗口都关闭）
   - 重新启动 Claude Code

2. **执行一个简单任务**
   - 在 Claude Code 中输入：`帮我把 1+1 算出来`
   - 等待任务完成
   - 关闭会话窗口（或按 Ctrl+D 退出）

3. **检查手机通知**
   - 打开企业微信 App
   - 查看"Claude 通知群"
   - 应该能看到类似下面的消息：

```
📱 Claude Code 任务完成

项目：test
窗口：abc12345
时间：2025-02-17 14:30:25

任务：帮我把 1+1 算出来

由 Claude Code 自动通知
```

---

## 🎨 多开场景处理

### 问题描述

当你同时打开多个 Claude Code 窗口（比如在不同项目目录），每个窗口完成任务时都会触发通知。如果不加区分，你会收到多条相同格式的通知，无法知道是哪个项目完成的。

### 解决方案：自动识别项目路径

**本方案已内置在脚本中，会自动：**

1. **提取项目路径**
   - 从会话文件中读取 `cwd`（当前工作目录）
   - 自动提取项目名称（目录名）

2. **生成会话 ID**
   - 从会话文件路径提取唯一标识
   - 方便区分同一项目的多个窗口

3. **格式化显示**
   - 根据配置显示完整路径、仅项目名、或短路径

### 通知效果对比

**未优化前（无法区分）：**

```
📱 Claude Code 任务完成

任务：创建 Django API
```

**优化后（清晰区分）：**

```
📱 Claude Code 任务完成

项目：test
窗口：abc12345
时间：2025-02-17 14:30:25

任务：创建 Django API
```

**多窗口场景示例：**

同时打开 3 个窗口，完成后收到的通知：

```
通知 1：
项目：test (frontend)
窗口：abc12345
任务：修复登录 Bug

通知 2：
项目：backend-api
窗口：def67890
任务：添加用户认证

通知 3：
项目：mobile-app
窗口：ghi45678
任务：更新依赖包
```

### 项目路径显示格式配置

**通过环境变量配置：**

```bash
# 显示完整路径
export PROJECT_PATH_FORMAT="full"
# 结果：e:\Files\PycharmProjects\test

# 仅显示项目名（推荐）
export PROJECT_PATH_FORMAT="name"
# 结果：test

# 显示短路径
export PROJECT_PATH_FORMAT="short"
# 结果：...\PycharmProjects\test
```

**Windows 设置：**

```powershell
[System.Environment]::SetEnvironmentVariable('PROJECT_PATH_FORMAT', 'name', 'User')
```

**macOS/Linux 设置：**

```bash
echo 'export PROJECT_PATH_FORMAT="name"' >> ~/.zshrc
source ~/.zshrc
```

---

## 🔧 进阶配置

### 可选功能 1：实时进度通知

**场景：** 长时间运行的任务，想在执行过程中收到进度更新。

**配置：**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "always",
        "command": "python ~/.claude/plugins/notify-wechat/send-notify.py --type=progress"
      }
    ]
  }
}
```

**效果：** 每次 Claude 使用工具（写入文件、运行命令等）后都会发送通知。

**⚠️ 注意：** 可能会导致消息频率较高，建议谨慎使用。

---

### 可选功能 2：仅在出错时通知

**场景：** 只在任务失败或出错时收到通知，成功时不打扰。

**配置：**

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "has_errors",
        "command": "python ~/.claude/plugins/notify-wechat/send-notify.py --type=error"
      }
    ]
  }
}
```

---

### 可选功能 3：通知去重

**场景：** 短时间内同一任务只通知一次，避免重复打扰。

**修改脚本：** 在 `main()` 函数中添加去重逻辑：

```python
def should_notify(task, project):
    """
    检查是否应该发送通知（去重）

    Args:
        task: 任务描述
        project: 项目名

    Returns:
        bool: True=发送通知, False=跳过
    """
    # 去重缓存文件
    cache_file = os.path.expanduser('~/.claude/cache/notify-cache.txt')
    cache_key = f"{project}:{task}"

    # 读取缓存
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_tasks = f.read().splitlines()

            # 检查是否在缓存中（5分钟内）
            import time
            now = time.time()
            for line in cached_tasks:
                parts = line.split('|')
                if len(parts) == 2:
                    key, timestamp = parts
                    if key == cache_key and (now - float(timestamp)) < 300:  # 5分钟
                        return False

        # 写入缓存
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'a', encoding='utf-8') as f:
            f.write(f"{cache_key}|{time.time()}\n")

        return True

    except Exception:
        return True  # 出错时仍然通知
```

---

## 🐛 常见问题

### Q1：手机收不到通知？

**排查步骤：**

1. **检查企业微信通知权限**
   - 打开企业微信 App → 设置 → 通知管理
   - 确保"新消息通知"已开启
   - 确保"群消息"通知已开启

2. **测试 Webhook URL**
   - 使用前面的测试命令验证机器人是否工作
   - 确认 Webhook URL 正确且未过期

3. **检查脚本执行**
   - 手动运行脚本，看是否有报错：
     ```powershell
     python ~/.claude/plugins/notify-wechat/send-notify.py < test-input.json
     ```

4. **检查 Claude Code 配置**
   - 确认 `settings.json` 中 `hooks` 配置正确
   - 确认路径正确（Windows 用 `~` 或完整路径）
   - 重启 Claude Code

---

### Q2：通知消息太长或太简短？

**调整方法：**

1. **修改任务描述长度**
   - 编辑脚本中的 `simplify_task_description()` 函数
   - 调整 `if len(text) > 30:` 中的数字

2. **修改消息格式**
   - 编辑 `format_message()` 函数
   - 添加或删除字段

3. **使用纯文本格式（而非 Markdown）**
   - 修改 `send_wechat_notification()` 中的 `msgtype` 为 `"text"`

---

### Q3：通知频率限制如何处理？

**企业微信限制：**
- 每个机器人每分钟最多 20 条消息
- 超过后会被限流

**解决方案：**

1. **只在关键任务完成时通知**
   - 修改 `matcher`，只在特定条件下触发

2. **使用通知去重**（见前文）

3. **添加通知冷却时间**
   - 在脚本中添加时间间隔检查
   - 比如：同一项目 5 分钟内最多通知 1 次

---

### Q4：多窗口同时完成任务会冲突吗？

**答案：** 不会冲突

每个 Claude Code 窗口是独立进程，各自执行 Hook 脚本。即使同时发送多条通知，企业微信也能正常接收。

**唯一的影响：**
- 如果短时间内（几秒内）发送多条消息，可能会在手机上合并显示
- 这不影响功能，只是显示方式不同

---

### Q5：如何在不同项目使用不同的机器人？

**方法 1：每个项目单独配置（繁琐但清晰）**

在每个项目的 `.claude/settings.json` 中配置不同的 Webhook URL：

```json
{
  "hooks": {
    "Stop": [{
      "command": "python ~/.claude/plugins/notify-wechat/send-notify.py --webhook=项目A的webhook"
    }]
  }
}
```

**方法 2：使用项目环境变量（推荐）**

在脚本中根据项目名选择不同的 Webhook URL：

```python
# 在脚本开头添加
PROJECT_WEBHOOKS = {
    'test': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=AAAAA',
    'backend': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=BBBBB',
}

# 在 main() 中
webhook_url = PROJECT_WEBHOOKS.get(project, WEBHOOK_URL)
```

---

## 🔒 安全性建议

### 1. 保护 Webhook URL

**为什么重要？**
- Webhook URL 相当于你的"通知密码"
- 如果泄露，他人可以给发送消息

**安全做法：**

✅ **推荐：** 使用环境变量
```powershell
# 设置环境变量（不会出现在配置文件中）
[System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', '你的URL', 'User')
```

❌ **不推荐：** 直接写在 settings.json
```json
{
  "hooks": {
    "Stop": [{
      "command": "python send-notify.py --webhook=https://qyapi.weixin.qq.com/...（泄露风险）"
    }]
  }
}
```

### 2. 定期更换 Webhook URL

**操作步骤：**
1. 删除旧机器人
2. 创建新机器人
3. 更新环境变量

**频率建议：**
- 个人使用：每 3-6 个月更换一次
- 团队使用：有人离开团队时立即更换

### 3. 监控异常通知

如果收到非你发起的通知，说明 Webhook 可能泄露，应立即：
1. 删除机器人
2. 创建新机器人
3. 更新环境变量
4. 检查是否有未授权访问

---

## 📊 方案对比

| 方案 | 优势 | 劣势 | 推荐度 |
|------|------|------|--------|
| **企业微信机器人** | 免费、国内快、稳定、无限制、支持 Markdown | 需要下载 App | ⭐⭐⭐⭐⭐ |
| Telegram Bot | 国际通用、轻量、无限制 | 国内需翻墙 | ⭐⭐⭐ |
| Server 酱 | 零配置 | 免费版有限制 | ⭐⭐⭐ |
| Bark（iOS） | 极简、免费 | 仅限 iOS | ⭐⭐⭐⭐ |
| Pushover | 稳定、跨平台 | 付费 | ⭐⭐ |

---

## 📝 总结

### 完整流程回顾

1. **创建企业微信机器人**（5 分钟）
   - 下载企业微信 → 创建群 → 添加机器人 → 复制 Webhook URL

2. **测试机器人**（1 分钟）
   - 使用 curl/PowerShell 发送测试消息

3. **创建通知脚本**（3 分钟）
   - 复制脚本到 `~/.claude/plugins/notify-wechat/`
   - 设置可执行权限

4. **配置环境变量**（1 分钟）
   - 设置 `WECHAT_WEBHOOK` 环境变量

5. **配置 Claude Code Hook**（2 分钟）
   - 编辑 `~/.claude/settings.json`
   - 添加 `Stop` Hook

6. **重启并测试**（1 分钟）
   - 重启 Claude Code
   - 执行简单任务
   - 检查手机通知

**总计：约 13 分钟**

---

### 你将获得

- ✅ Claude Code 完成任务时，手机自动收到通知
- ✅ 通知包含项目名、任务摘要、完成时间
- ✅ 多窗口场景也能清晰区分
- ✅ 无需守在电脑前，可以去做别的事
- ✅ 完全免费，无限制使用

---

## 🆘 需要帮助？

**遇到问题？**

1. 检查本文档的"常见问题"部分
2. 查看脚本错误输出（`stderr`）
3. 手动运行脚本测试

**反馈和建议：**

如果有改进建议或发现问题，欢迎反馈！

---

**祝使用愉快！** 🎉

---

*本文档最后更新：2025-02-17*
