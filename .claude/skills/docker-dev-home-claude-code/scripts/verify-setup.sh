#!/usr/bin/env bash
set -e

echo "=== 验证 Claude Code CLI 安装 ==="
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 未找到 docker-compose.yml"
    exit 1
fi

# Check container status
echo "🔍 检查容器状态..."
CONTAINER_STATUS=$(docker-compose ps --services --filter "status=running")

if [ -z "$CONTAINER_STATUS" ]; then
    echo "❌ 容器未运行"
    echo "   请先运行: docker-compose up -d"
    exit 1
fi

echo "✓ 容器运行中"
echo ""

# Check Claude Code CLI installation
echo "🔍 检查 Claude Code CLI..."
VERSION_OUTPUT=$(docker-compose exec -T app claude --version 2>&1)

if [ $? -eq 0 ]; then
    echo "✓ Claude Code CLI 已安装"
    echo "   版本信息: $VERSION_OUTPUT"
else
    echo "⚠ Claude Code CLI 未安装或无法访问"
    echo "   可能原因:"
    echo "   - 容器仍在初始化中，请稍后重试"
    echo "   - Dockerfile 未正确配置 CLI 安装"
    exit 1
fi

echo ""
echo ""

# Verify dev-home mount
echo "🔍 检查 dev-home 挂载..."
if docker-compose exec -T app test -d /root/.config/claude 2>/dev/null; then
    echo "✓ Claude Code 配置目录已持久化"
else
    echo "⚠️  Claude Code 配置目录尚未创建(首次运行正常)"
fi

# Verify state persistence
echo ""
echo "🔍 测试状态持久化..."
if docker-compose exec -T app sh -c "echo 'test-$(date)' > /root/.persistence-test 2>/dev/null"; then
    echo "✓ 可以在 /root 写入数据"

    # Check if file exists on host
    DEV_HOME=$(grep "^DEV_HOME_PATH" .env 2>/dev/null | cut -d'=' -f2)
    DEV_HOME=${DEV_HOME:-"./dev-home"}

    if [ -f "$DEV_HOME/root/.persistence-test" ]; then
        echo "✓ 数据已同步到宿主机: $DEV_HOME/root/.persistence-test"
        rm -f "$DEV_HOME/root/.persistence-test"
    else
        echo "⚠️  数据未同步到宿主机(可能需要等待)"
    fi
else
    echo "⚠️  无法在 /root 写入数据"
fi
echo ""

# Check environment variable
echo "🔍 检查环境变量配置..."
API_KEY_SET=$(docker-compose exec -T app printenv ANTHROPIC_API_KEY 2>/dev/null | grep -q "sk-" && echo "true" || echo "false")

if [ "$API_KEY_SET" = "true" ]; then
    echo "✓ ANTHROPIC_API_KEY 已配置"
else
    echo "⚠ ANTHROPIC_API_KEY 未配置或无效"
    echo "   请在 .env 文件中设置你的 API Key"
fi

echo ""
echo "=== 验证完成 ==="

# Show usage hints
echo ""
echo "📋 使用提示:"
echo "   进入容器交互模式:"
echo "   $ docker-compose exec app sh"
echo ""
echo "   在容器内启动 Claude Code:"
echo "   $ claude"
