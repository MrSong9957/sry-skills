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
