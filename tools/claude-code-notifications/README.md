# Claude Code 企业微信通知

基于企业微信机器人的 Claude Code 任务完成通知方案。

## 功能特性

- ✅ 零成本：企业微信机器人完全免费
- ✅ 国内稳定：无需翻墙，99.9% 可达率
- ✅ 多窗口支持：自动识别项目路径
- ✅ 异步执行：不影响 Claude Code 性能

---

## AI IDE 极简安装 🚀

### 选择你的安装方式

#### 🤖 AI 辅助安装（推荐，30 秒搞定）

只需要告诉 AI 一句话，让它帮你配置：

**复制这段话发送给 AI：**

```
请帮我在 ~/.claude/settings.json 中配置企业微信通知，Webhook URL 是：
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key

配置要求：
1. 使用当前目录下的 claude-code-notifications/send-notify.py 脚本
2. 在 Stop hook 中调用
3. 路径使用绝对路径
```

**AI 会自动完成：**
✅ 读取现有配置文件
✅ 添加通知配置（不覆盖现有设置）
✅ 保存并验证配置格式

**你只需要：**
1. 准备好你的企业微信 Webhook URL
2. 复制上面的指令，把 `你的key` 替换成实际值
3. 发送给 AI，坐等完成！

💡 **提示：** 如果 AI 问你路径，告诉它：`使用当前工作目录的绝对路径`

---

#### 📋 手动安装（5 分钟）

**方式一：自动脚本（推荐）**

复制整段命令到终端，一次运行即可完成：

**Windows PowerShell：**
```powershell
$webhook = Read-Host "请输入你的企业微信 Webhook URL"
[System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', $webhook, 'User')

$configPath = "$env:USERPROFILE\.claude\settings.json"
$scriptPath = "$PWD\claude-code-notifications\send-notify.py"

$config = Get-Content $configPath -Raw | ConvertFrom-Json
if (-not $config.hooks.Stop) { $config.hooks.Stop = @() }
$config.hooks.Stop += @{
    matcher = "always"
    command = "python3 `"$scriptPath`""
}

$config | ConvertTo-Json -Depth 10 | Set-Content $configPath
Write-Host "✅ 配置完成！重启 Claude Code 即可生效" -ForegroundColor Green
```

**macOS/Linux：**
```bash
read -p "请输入你的企业微信 Webhook URL: " webhook
echo "export WECHAT_WEBHOOK=\"$webhook\"" >> ~/.zshrc && source ~/.zshrc

CONFIG_FILE="$HOME/.claude/settings.json"
SCRIPT_PATH="$(pwd)/claude-code-notifications/send-notify.py"

# 备份原配置
cp "$CONFIG_FILE" "$CONFIG_FILE.bak"

# 添加配置（使用 jq）
if command -v jq &> /dev/null; then
    tmp=$(mktemp)
    jq --arg cmd "python3 $SCRIPT_PATH" '.hooks.Stop += [{"matcher": "always", "command": $cmd}]' "$CONFIG_FILE" > "$tmp"
    mv "$tmp" "$CONFIG_FILE"
else
    echo "请手动添加以下配置到 $CONFIG_FILE 的 hooks.Stop 数组中："
    echo "{\"matcher\": \"always\", \"command\": \"python3 $SCRIPT_PATH\"}"
fi

echo "✅ 配置完成！重启 Claude Code 即可生效"
```

---

**方式二：手动复制配置**

**第 1 步：设置环境变量**

复制你的 Webhook URL，替换下面命令中的 `你的key`，然后运行：

**Windows PowerShell：**
```powershell
[System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key', 'User')
```

**macOS/Linux：**
```bash
echo 'export WECHAT_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"' >> ~/.zshrc
source ~/.zshrc
```

---

**第 2 步：添加配置到 Claude Code**

打开文件 `~/.claude/settings.json`，找到 `"hooks"` 部分，在 `"Stop"` 数组中添加：

```json
{
  "matcher": "always",
  "command": "python3 /你的项目绝对路径/claude-code-notifications/send-notify.py"
}
```

💡 **如何找到绝对路径？**
- Windows: 在项目文件夹中右键 → "复制路径"
- macOS/Linux: 在项目文件夹运行 `pwd` 命令

---

**第 3 步：测试通知**

重启 Claude Code，执行任意任务后关闭会话，检查企业微信是否收到通知。

✅ **成功！** 🎉
❌ **失败？** 查看下方 [故障排查](#故障排查)

---

#### ⚙️ 高级配置（可选）

<details>
<summary>📖 点击展开高级配置选项</summary>

**通知格式自定义**

通过环境变量 `PROJECT_PATH_FORMAT` 控制项目路径显示：

```bash
# 显示完整路径
export PROJECT_PATH_FORMAT="full"

# 仅显示项目名（推荐，默认）
export PROJECT_PATH_FORMAT="name"

# 显示短路径（最后两级目录）
export PROJECT_PATH_FORMAT="short"
```

**Windows 设置：**
```powershell
[System.Environment]::SetEnvironmentVariable('PROJECT_PATH_FORMAT', 'name', 'User')
```

**仅通知特定项目**

如果你有多个项目，只想为特定项目启用通知：

修改配置中的 `matcher`：

```json
{
  "matcher": "cwd:/path/to/specific/project",
  "command": "python3 /path/to/claude-code-notifications/send-notify.py"
}
```

**自定义通知内容**

编辑 `send-notify.py` 中的 `format_message()` 函数，自定义通知格式：

```python
def format_message(project_path, window_id, timestamp):
    return f"""
🎯 任务完成通知

项目: {project_name}
时间: {timestamp}
状态: 成功
"""
```

**调试模式**

启用详细日志输出：

```bash
export DEBUG_MODE=true
```

查看完整日志：
```bash
# Windows
Get-Content $env:USERPROFILE\.claude\hooks.log -Tail 50

# macOS/Linux
tail -f ~/.claude/hooks.log
```

</details>

---

## 传统安装方式

如果你想了解手动配置的详细步骤，请参考下方内容。

### 1. 配置 Webhook URL

将你的企业微信 Webhook URL 设置为环境变量：

**Windows PowerShell：**
```powershell
[System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key', 'User')
```

**macOS/Linux：**
```bash
echo 'export WECHAT_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"' >> ~/.zshrc
source ~/.zshrc
```

### 2. 配置 Claude Code Hook

编辑 `~/.claude/settings.json`，添加以下配置：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "always",
        "command": "python3 /workspace/project/claude-code-notifications/send-notify.py"
      }
    ]
  }
}
```

**注意：** 将路径替换为你实际的 `claude-code-notifications` 目录路径。

### 3. 测试

1. 重启 Claude Code
2. 执行一个简单任务
3. 关闭会话窗口
4. 检查手机企业微信通知

## 目录结构

```
claude-code-notifications/
├── send-notify.py      # 通知脚本
├── .env.example        # 配置示例
└── README.md           # 本文件
```

## 通知格式

```
📱 Claude Code 任务完成

项目：project
窗口：abc12345
时间：2026-02-16 14:30:25

任务：修复登录 Bug

由 Claude Code 自动通知
```

## 故障排查

### 手机收不到通知？

1. 检查企业微信通知权限是否开启
2. 测试 Webhook URL 是否有效
3. 检查环境变量是否正确设置
4. 重启 Claude Code

### 脚本执行错误？

手动运行脚本测试：
```bash
echo '{"transcript_path":"/path/to/transcript.jsonl"}' | python3 send-notify.py
```

## 安全建议

- 使用环境变量存储 Webhook URL，不要直接写在配置文件中
- 定期更换 Webhook URL（建议 3-6 个月）
- 监控异常通知，发现泄露立即更换

## 参考文档

完整配置指南请参考：[docs/CLAUDE_CODE_MOBILE_NOTIFICATION.md](../docs/CLAUDE_CODE_MOBILE_NOTIFICATION.md)
