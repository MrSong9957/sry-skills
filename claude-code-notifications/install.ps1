# 企业微信通知快速安装脚本 (Windows PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$WebhookUrl
)

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Claude Code 企业微信通知安装" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 验证 URL 格式
if ($WebhookUrl -notmatch "^https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=") {
    Write-Host "警告：Webhook URL 格式可能不正确" -ForegroundColor Yellow
    Write-Host "正确格式：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" -ForegroundColor Yellow
    $confirm = Read-Host "是否继续？(y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        exit 1
    }
}

# 检测 Claude Code 配置目录
$claudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $claudeDir)) {
    Write-Host "错误：未找到 Claude Code 配置目录 $claudeDir" -ForegroundColor Red
    Write-Host "请确认已安装 Claude Code" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 找到 Claude Code 配置目录" -ForegroundColor Green

# 获取当前脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pluginDir = "$claudeDir\plugins\notify-wechat"

# 创建插件目录
$pluginsParent = Split-Path -Parent $pluginDir
if (-not (Test-Path $pluginsParent)) {
    New-Item -ItemType Directory -Path $pluginsParent -Force | Out-Null
}

# 创建符号链接（需要管理员权限）或复制
try {
    if (Test-Path $pluginDir) {
        Write-Host "✓ 移除现有插件目录" -ForegroundColor Green
        Remove-Item $pluginDir -Force -Recurse
    }

    # 尝试创建符号链接
    $null = New-Item -ItemType SymbolicLink -Path $pluginDir -Target $scriptDir -Force
    Write-Host "✓ 创建符号链接: $pluginDir -> $scriptDir" -ForegroundColor Green
} catch {
    # 如果符号链接失败，使用 junction 或复制
    Write-Host "  符号链接失败，使用复制方式" -ForegroundColor Yellow
    if (Test-Path $pluginDir) {
        Remove-Item $pluginDir -Force -Recurse
    }
    Copy-Item -Path $scriptDir -Destination $pluginDir -Recurse
    Write-Host "✓ 复制文件到: $pluginDir" -ForegroundColor Green
}

# 设置环境变量
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "设置环境变量" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

try {
    [System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', $WebhookUrl, 'User')
    Write-Host "✓ 已设置用户环境变量 WECHAT_WEBHOOK" -ForegroundColor Green
} catch {
    Write-Host "✗ 设置环境变量失败: $_" -ForegroundColor Red
    Write-Host "请手动设置：" -ForegroundColor Yellow
    Write-Host "  [System.Environment]::SetEnvironmentVariable('WECHAT_WEBHOOK', '$WebhookUrl', 'User')" -ForegroundColor White
}

# 检查并更新 settings.json
$settingsFile = "$claudeDir\settings.json"
$pythonPath = "python"  # 或 "python3"

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "配置 Claude Code Hook" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $settingsFile)) {
    Write-Host "创建新的 settings.json" -ForegroundColor Yellow
    $config = @{
        hooks = @{
            Stop = @(
                @{
                    matcher = "always"
                    command = "$pythonPath $pluginDir\send-notify.py"
                }
            )
        }
    }
    $config | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
    Write-Host "✓ 已创建配置文件" -ForegroundColor Green
} else {
    Write-Host "检查现有 settings.json 配置..." -ForegroundColor Yellow

    try {
        $config = Get-Content $settingsFile -Raw | ConvertFrom-Json
        $hookCommand = "$pythonPath $pluginDir\send-notify.py"

        if (-not $config.hooks) {
            $config | Add-Member -Type NoteProperty -Name 'hooks' -Value @{ Stop = @() }
        }

        if (-not $config.hooks.Stop) {
            $config.hooks | Add-Member -Type NoteProperty -Name 'Stop' -Value @()
        }

        $existing = $config.hooks.Stop | Where-Object { $_.command -eq $hookCommand }

        if (-not $existing) {
            $newHook = @{
                matcher = "always"
                command = $hookCommand
            }
            $config.hooks.Stop += $newHook

            $config | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Host "✓ 已添加 Stop Hook 配置" -ForegroundColor Green
        } else {
            Write-Host "✓ Stop Hook 配置已存在，跳过" -ForegroundColor Green
        }
    } catch {
        Write-Host "✗ 更新配置文件失败: $_" -ForegroundColor Red
        Write-Host "请手动编辑 $settingsFile 添加以下配置：" -ForegroundColor Yellow
        Write-Host @"
{
  "hooks": {
    "Stop": [
      {
        "matcher": "always",
        "command": "python $pluginDir\send-notify.py"
      }
    ]
  }
}
"@ -ForegroundColor White
    }
}

# 验证脚本
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "验证安装" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

try {
    & $pythonPath -m py_compile "$pluginDir\send-notify.py"
    Write-Host "✓ 脚本语法检查通过" -ForegroundColor Green
} catch {
    Write-Host "✗ 脚本语法检查失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后续步骤：" -ForegroundColor White
Write-Host "  1. 重启 Claude Code" -ForegroundColor White
Write-Host "  2. 执行一个简单任务测试" -ForegroundColor White
Write-Host ""
Write-Host "测试命令：" -ForegroundColor White
Write-Host "  echo '{\"transcript_path\":\"C:\\temp\\test-transcript.jsonl\"}' | python $pluginDir\send-notify.py" -ForegroundColor Gray
Write-Host ""
