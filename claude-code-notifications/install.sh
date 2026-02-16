#!/bin/bash
# 企业微信通知快速安装脚本

set -e

echo "================================"
echo "Claude Code 企业微信通知安装"
echo "================================"
echo

# 检查是否提供了 Webhook URL
if [ -z "$1" ]; then
    echo "错误：请提供企业微信 Webhook URL"
    echo
    echo "使用方法："
    echo "  bash install.sh <webhook_url>"
    echo
    echo "示例："
    echo "  bash install.sh https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key"
    exit 1
fi

WEBHOOK_URL="$1"

# 验证 URL 格式
if [[ ! "$WEBHOOK_URL" =~ ^https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key= ]]; then
    echo "警告：Webhook URL 格式可能不正确"
    echo "正确格式：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检测 Claude Code 配置目录
CLAUDE_DIR="$HOME/.claude"
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "错误：未找到 Claude Code 配置目录 $CLAUDE_DIR"
    echo "请确认已安装 Claude Code"
    exit 1
fi

echo "✓ 找到 Claude Code 配置目录"

# 创建符号链接到 Claude Code plugins
PLUGIN_DIR="$CLAUDE_DIR/plugins/notify-wechat"
mkdir -p "$(dirname "$PLUGIN_DIR")"

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -L "$PLUGIN_DIR" ]; then
    echo "✓ 更新现有符号链接"
    rm "$PLUGIN_DIR"
fi

ln -s "$SCRIPT_DIR" "$PLUGIN_DIR"
echo "✓ 创建符号链接: $PLUGIN_DIR -> $SCRIPT_DIR"

# 检查并更新 settings.json
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "创建新的 settings.json"
    echo "{\"hooks\":{\"Stop\":[{\"matcher\":\"always\",\"command\":\"python3 $PLUGIN_DIR/send-notify.py\"}]}}" > "$SETTINGS_FILE"
else
    echo "检查现有 settings.json 配置..."

    # 使用 Python 处理 JSON
    python3 << EOF
import json
import sys

with open('$SETTINGS_FILE', 'r') as f:
    config = json.load(f)

# 确保 hooks 存在
if 'hooks' not in config:
    config['hooks'] = {}

if 'Stop' not in config['hooks']:
    config['hooks']['Stop'] = []

# 检查是否已存在通知配置
hook_command = f"python3 {sys.argv[1]}/send-notify.py"
existing = any(h.get('command') == hook_command for h in config['hooks']['Stop'])

if not existing:
    config['hooks']['Stop'].append({
        'matcher': 'always',
        'command': hook_command
    })

    with open('$SETTINGS_FILE', 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("✓ 已添加 Stop Hook 配置")
else:
    print("✓ Stop Hook 配置已存在，跳过")
EOF
    python3 - "$PLUGIN_DIR"
fi

# 设置环境变量提示
echo
echo "================================"
echo "设置环境变量"
echo "================================"
echo
echo "请将以下内容添加到你的 shell 配置文件："
echo
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "  echo 'export WECHAT_WEBHOOK=\"$WEBHOOK_URL\"' >> ~/.zshrc  # 或 ~/.bashrc"
    echo "  source ~/.zshrc"
else
    echo "  [System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', '$WEBHOOK_URL', 'User')"
fi
echo

# 验证脚本
echo "================================"
echo "验证安装"
echo "================================"
echo

if python3 -c "import sys; sys.path.insert(0, '$PLUGIN_DIR'); import send_notify" 2>/dev/null; then
    echo "✓ 脚本语法检查通过"
else
    # send_notify.py 是直接执行的，不需要 import
    python3 -m py_compile "$PLUGIN_DIR/send-notify.py"
    echo "✓ 脚本语法检查通过"
fi

echo
echo "================================"
echo "安装完成！"
echo "================================"
echo
echo "后续步骤："
echo "  1. 设置环境变量 WECHAT_WEBHOOK"
echo "  2. 重启 Claude Code"
echo "  3. 执行一个简单任务测试"
echo
echo "测试命令："
echo "  echo '{\"transcript_path\":\"/tmp/test-transcript.jsonl\"}' | python3 $PLUGIN_DIR/send-notify.py"
echo
