# PowerShell script to check Docker environment
$ErrorActionPreference = "Stop"

Write-Host "=== Docker 环境检查 ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "🔍 检查 Docker 安装..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker 已安装" -ForegroundColor Green
        Write-Host "   $dockerVersion"
        Write-Host ""
    } else {
        throw "Docker not found"
    }
} catch {
    Write-Host "❌ Docker 未安装" -ForegroundColor Red
    Write-Host "   请访问 https://docs.docker.com/get-docker/ 安装 Docker Desktop"
    exit 1
}

# Check if Docker daemon is running
Write-Host "🔍 检查 Docker 服务状态..." -ForegroundColor Yellow
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker 服务运行中" -ForegroundColor Green
        Write-Host ""
    } else {
        throw "Docker daemon not running"
    }
} catch {
    Write-Host "❌ Docker 服务未运行" -ForegroundColor Red
    Write-Host "   请启动 Docker Desktop"
    exit 1
}

# Check if docker-compose is available
Write-Host "🔍 检查 docker-compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ docker-compose 已安装" -ForegroundColor Green
        Write-Host "   $composeVersion"
    } else {
        throw "docker-compose not found"
    }
} catch {
    # Try docker compose (plugin version)
    try {
        $composeVersion = docker compose version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ docker compose 已安装" -ForegroundColor Green
            Write-Host "   $composeVersion"
        } else {
            throw "docker compose not found"
        }
    } catch {
        Write-Host "❌ docker-compose 未安装" -ForegroundColor Red
        Write-Host "   Docker Desktop 应包含 docker-compose"
        Write-Host "   请确保 Docker Desktop 正确安装"
        exit 1
    }
}

Write-Host ""
Write-Host "=== 环境检查完成 ✓ ===" -ForegroundColor Green
