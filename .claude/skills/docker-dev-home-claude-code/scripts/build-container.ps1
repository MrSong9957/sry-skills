# PowerShell script to build and start Docker container
$ErrorActionPreference = "Stop"

Write-Host "=== 构建并启动 Docker 容器 ===" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ 错误: 未找到 docker-compose.yml" -ForegroundColor Red
    Write-Host "   请先运行配置生成脚本"
    exit 1
}

# Check dev-home directory
Write-Host "🔍 检查 dev-home 配置..." -ForegroundColor Yellow
if (Test-Path ".env") {
    # Read .env file to get DEV_HOME_PATH
    $envContent = Get-Content ".env" | Where-Object { $_ -match "^DEV_HOME_PATH=" }
    if ($envContent) {
        $devHomePath = ($envContent -split "=", 2)[1].Trim()
    } else {
        $devHomePath = ".\dev-home"
    }

    if (-not (Test-Path "$devHomePath\root")) {
        Write-Host "❌ 错误: dev-home 目录不存在: $devHomePath\root" -ForegroundColor Red
        Write-Host "   请先运行配置生成脚本"
        exit 1
    }

    Write-Host "✓ dev-home 配置: $devHomePath" -ForegroundColor Green

    # Check if using shared dev-home
    if ($devHomePath -match "^\.\.") {
        Write-Host "⚠️  使用共享 dev-home: $devHomePath" -ForegroundColor Yellow
        Write-Host "   多个项目将共享 Claude Code 状态"
    }
} else {
    Write-Host "⚠️  未找到 .env 文件,使用默认 dev-home: .\dev-home" -ForegroundColor Yellow
}
Write-Host ""

# Build the Docker image
Write-Host "📦 构建 Docker 镜像..." -ForegroundColor Yellow
docker-compose build --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 镜像构建失败" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 镜像构建完成" -ForegroundColor Green
Write-Host ""

# Start the container
Write-Host "🚀 启动容器..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 容器启动失败" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 容器已启动" -ForegroundColor Green
Write-Host ""

# Wait for container to be ready
Write-Host "⏳ 等待容器就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Show container status
Write-Host "📊 容器状态:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

# Get container name
$containerId = docker-compose ps -q
if ($containerId) {
    $containerName = docker inspect --format='{{.Name}}' $containerId 2>$null
    if ($containerName) {
        $containerName = $containerName -replace '/', ''
        Write-Host "✓ 构建完成!" -ForegroundColor Green
        Write-Host "   容器名称: $containerName"
    }
}
Write-Host ""

# Show next steps
Write-Host "📋 下一步操作:" -ForegroundColor Cyan
Write-Host "   - 查看日志: docker-compose logs -f"
Write-Host "   - 进入容器: docker-compose exec app sh"
Write-Host "   - 停止容器: docker-compose down"
Write-Host "   - 重启容器: docker-compose restart"
