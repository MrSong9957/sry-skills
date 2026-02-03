#!/usr/bin/env bash
set -e

echo "=== 构建并启动 Docker 容器 ==="
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 未找到 docker-compose.yml"
    echo "   请先运行配置生成脚本"
    exit 1
fi

# Check dev-home directory
echo "🔍 检查 dev-home 配置..."
if [ -f ".env" ]; then
    source .env
    DEV_HOME=${DEV_HOME_PATH:-"./dev-home"}

    if [ ! -d "$DEV_HOME/root" ]; then
        echo "❌ 错误: dev-home 目录不存在: $DEV_HOME/root"
        echo "   请先运行配置生成脚本"
        exit 1
    fi

    echo "✓ dev-home 配置: $DEV_HOME"

    # Check if using shared dev-home
    if [[ "$DEV_HOME" == ".."* ]]; then
        echo "⚠️  使用共享 dev-home: $DEV_HOME"
        echo "   多个项目将共享 Claude Code 状态"
    fi
else
    echo "⚠️  未找到 .env 文件,使用默认 dev-home: ./dev-home"
fi
echo ""

# Build the Docker image
echo "📦 构建 Docker 镜像..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败"
    exit 1
fi

echo "✓ 镜像构建完成"
echo ""

# Start the container
echo "🚀 启动容器..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 容器启动失败"
    exit 1
fi

echo "✓ 容器已启动"
echo ""

# Wait for container to be ready
echo "⏳ 等待容器就绪..."
sleep 3

# Show container status
echo "📊 容器状态:"
docker-compose ps
echo ""

# Get container name
CONTAINER_NAME=$(docker-compose ps -q | xargs docker inspect --format='{{.Name}}' | sed 's/\///')
echo "✓ 构建完成!"
echo "   容器名称: $CONTAINER_NAME"
echo ""

# Show next steps
echo "📋 下一步操作:"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 进入容器: docker-compose exec app sh"
echo "   - 停止容器: docker-compose down"
echo "   - 重启容器: docker-compose restart"
