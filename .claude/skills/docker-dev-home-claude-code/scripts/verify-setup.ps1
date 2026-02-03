# PowerShell script to verify Claude Code CLI installation
$ErrorActionPreference = "Stop"

Write-Host "=== 验证 Claude Code CLI 安装 ===" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ 错误: 未找到 docker-compose.yml" -ForegroundColor Red
    exit 1
}

# Check container status
Write-Host "🔍 检查容器状态..." -ForegroundColor Yellow
$containerStatus = docker-compose ps --services --filter "status=running"

if ([string]::IsNullOrEmpty($containerStatus)) {
    Write-Host "❌ 容器未运行" -ForegroundColor Red
    Write-Host "   请先运行: docker-compose up -d"
    exit 1
}

Write-Host "✓ 容器运行中" -ForegroundColor Green
Write-Host ""

# Check Claude Code CLI installation
Write-Host "🔍 检查 Claude Code CLI..." -ForegroundColor Yellow
try {
    $versionOutput = docker-compose exec -T app claude --version 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Claude Code CLI 已安装" -ForegroundColor Green
        Write-Host "   版本信息: $versionOutput"
    } else {
        Write-Host "⚠ Claude Code CLI 未安装或无法访问" -ForegroundColor Yellow
        Write-Host "   可能原因:"
        Write-Host "   - 容器仍在初始化中，请稍后重试"
        Write-Host "   - Dockerfile 未正确配置 CLI 安装"
        exit 1
    }
} catch {
    Write-Host "⚠ Claude Code CLI 未安装或无法访问" -ForegroundColor Yellow
    Write-Host "   可能原因:"
    Write-Host "   - 容器仍在初始化中，请稍后重试"
    Write-Host "   - Dockerfile 未正确配置 CLI 安装"
    exit 1
}

Write-Host ""
Write-Host ""

# Verify dev-home mount
Write-Host "🔍 检查 dev-home 挂载..." -ForegroundColor Yellow
try {
    $testResult = docker-compose exec -T app test -d /root/.config/claude 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Claude Code 配置目录已持久化" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Claude Code 配置目录尚未创建(首次运行正常)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  无法检查 dev-home 挂载" -ForegroundColor Yellow
}

# Verify state persistence
Write-Host ""
Write-Host "🔍 测试状态持久化..." -ForegroundColor Yellow
try {
    $testFile = docker-compose exec -T app sh -c "echo 'test-$(date)' > /root/.persistence-test 2>&1"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 可以在 /root 写入数据" -ForegroundColor Green

        # Check if file exists on host
        $devHomePath = ".\dev-home"
        if (Test-Path ".env") {
            $envContent = Get-Content ".env" | Where-Object { $_ -match "^DEV_HOME_PATH=" }
            if ($envContent) {
                $devHomePath = ($envContent -split "=", 2)[1].Trim()
            }
        }

        $testFilePath = Join-Path $devHomePath "root\.persistence-test"
        if (Test-Path $testFilePath) {
            Write-Host "✓ 数据已同步到宿主机: $testFilePath" -ForegroundColor Green
            Remove-Item $testFilePath -Force
        } else {
            Write-Host "⚠️  数据未同步到宿主机(可能需要等待)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  无法在 /root 写入数据" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  无法测试状态持久化" -ForegroundColor Yellow
}
Write-Host ""

# Check environment variable
Write-Host "🔍 检查环境变量配置..." -ForegroundColor Yellow
try {
    $apiKey = docker-compose exec -T app printenv ANTHROPIC_API_KEY 2>$null

    if ($apiKey -match "sk-") {
        Write-Host "✓ ANTHROPIC_API_KEY 已配置" -ForegroundColor Green
    } else {
        Write-Host "⚠ ANTHROPIC_API_KEY 未配置或无效" -ForegroundColor Yellow
        Write-Host "   请在 .env 文件中设置你的 API Key"
    }
} catch {
    Write-Host "⚠ 无法检查环境变量" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 验证完成 ===" -ForegroundColor Cyan

# Show usage hints
Write-Host ""
Write-Host "📋 使用提示:" -ForegroundColor Cyan
Write-Host "   进入容器交互模式:"
Write-Host "   > docker-compose exec app sh"
Write-Host ""
Write-Host "   在容器内启动 Claude Code:"
Write-Host "   > claude"
