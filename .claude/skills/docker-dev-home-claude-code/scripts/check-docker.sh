#!/usr/bin/env bash
set -e

echo "=== Docker 环境检查 ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "   请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

echo "✓ Docker 已安装"

# Get Docker version
DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
echo "   版本: $DOCKER_VERSION"
echo ""

# Check if Docker daemon is running
echo "🔍 检查 Docker 服务状态..."
if ! docker info &> /dev/null; then
    echo "❌ Docker 服务未运行"
    echo "   请启动 Docker Desktop 或 Docker daemon"
    exit 1
fi

echo "✓ Docker 服务运行中"
echo ""

# Check if docker-compose is available
echo "🔍 检查 docker-compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    echo "✓ docker-compose 已安装"
    echo "   版本: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short)
    echo "✓ docker compose 已安装"
    echo "   版本: $COMPOSE_VERSION"
else
    echo "❌ docker-compose 未安装"
    echo "   请访问 https://docs.docker.com/compose/install/ 安装"
    exit 1
fi

echo ""
echo "=== 环境检查完成 ✓ ==="
