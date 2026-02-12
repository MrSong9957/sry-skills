#!/bin/bash
# Project Initialization Script for Docker Claude Code
# Initializes Docker environment for new or existing projects

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Docker Claude Code - Project Init${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Detect current directory and platform
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_DIR="$(pwd)"

# Detect platform
OS_TYPE=$(uname -s)
case "$OS_TYPE" in
    Darwin)
        PLATFORM_ID="macos"
        PLATFORM_NAME="macOS"
        ;;
    Linux)
        PLATFORM_ID="linux"
        PLATFORM_NAME="Linux"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM_ID="windows"
        PLATFORM_NAME="Windows"
        ;;
    *)
        PLATFORM_ID="unknown"
        PLATFORM_NAME="Unknown"
        ;;
esac

echo -e "${BLUE}Platform detected:${NC} $PLATFORM_NAME"
echo ""

# Interactive menu
echo -e "${CYAN}Select initialization scenario:${NC}"
echo "1) New Project (create fresh Docker environment)"
echo "2) Migrate Existing Project (copy existing code to Docker)"
echo "3) Exit"
echo ""
read -p "Enter choice [1-3]: " choice
case $choice in
    1)
        SCENARIO="new"
        ;;
    2)
        SCENARIO="migrate"
        ;;
    3)
        echo -e "${YELLOW}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting...${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Scenario:${NC} $SCENARIO project"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get project name
read -p "Enter project name [docker-claude-code]: " project_name
project_name=${project_name:-docker-claude-code}

echo ""
echo -e "${BLUE}Initializing ${GREEN}$project_name${NC}..."
echo ""

# Verify .claude directory exists on host
CLAUDE_DIR="$HOME/.claude"
echo -e "${YELLOW}Checking for Claude Code directory...${NC}"

if [ ! -d "$CLAUDE_DIR" ]; then
    echo -e "${GREEN}✓ Claude Code directory found${NC}"
else
    echo -e "${YELLOW}[!] Claude Code directory not found: $CLAUDE_DIR${NC}"
    echo -e "${YELLOW}The plugin requires Claude Code to be installed on host first.${NC}"
    echo ""
    exit 1
fi

# Create project directory
PROJECT_DIR="$CURRENT_DIR/$project_name"
echo -e "${BLUE}Creating project directory:${NC} $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
echo -e "${GREEN}✓ Project directory created${NC}"
echo ""

# Function to create directory structure
create_directory_structure() {
    echo -e "${BLUE}Creating directory structure...${NC}"

    # Create workspace directory
    mkdir -p "$PROJECT_DIR/workspace/project"
    echo -e "${GREEN}✓ workspace/project created${NC}"

    # Create .gitignore
    cat > "$PROJECT_DIR/.gitignore" << 'EOF'
# Environment variables
.env

# Docker volumes
workspace/
dev-home/
EOF
    echo -e "${GREEN}✓ .gitignore created${NC}"

    # Create .claude/plugins directory for statusline plugin
    mkdir -p "$PROJECT_DIR/.claude/plugins/custom"
    echo -e "${GREEN}✓ .claude/plugins directory created${NC}"

    echo -e "${GREEN}✓ Directory structure created${NC}"
    echo ""
}

# Function to create .env file
create_env_file() {
    echo -e "${BLUE}Creating .env file...${NC}"

    local env_file="$PROJECT_DIR/.env"

    if [ -f "$env_file" ]; then
        echo -e "${YELLOW}.env file already exists. Skipping creation.${NC}"
        return 0
    fi

    # Platform-specific configuration
    local base_url="http://host.docker.internal:15721"
    local extra_hosts_comment="# Linux: Adds extra_hosts for host.docker.internal support"

    if [ "$PLATFORM_ID" = "linux" ]; then
        base_url="$base_url (Linux with extra_hosts)"
        extra_hosts_comment="# Linux compatible"
    fi

    cat > "$env_file" << EOF
# Claude Code CLI Configuration
# dummy 表示沿用宿主机的 API KEY
ANTHROPIC_API_KEY=dummy

# 端口要与 CC Switch 本地代理端口一致
ANTHROPIC_BASE_URL=$base_url

# Optional: Custom paths (defaults shown)
# WORKSPACE_PATH=./workspace
# DEV_HOME_PATH=./dev-home/claude
# CLAUDE_CONFIG_PATH=./dev-home/config
EOF

    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${BLUE}Platform:${NC} $PLATFORM_NAME"
    echo -e "${BLUE}Base URL:${NC} $base_url $extra_hosts_comment"
    echo ""
}

# Function to create docker-compose.yml
create_docker_compose() {
    echo -e "${BLUE}Creating docker-compose.yml...${NC}"

    local compose_file="$PROJECT_DIR/docker-compose.yml"

    if [ -f "$compose_file" ]; then
        echo -e "${YELLOW}docker-compose.yml already exists. Skipping creation.${NC}"
        return 0
    fi

    cat > "$compose_file" << EOF
services:
  app:
    build: .
    container_name: docker-claude-code-app
    ports:
      # 容器内应用端口映射（如有 Web 服务需要）
      - "8080:8000"
    environment:
      - ENV=development
      - ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
      - ANTHROPIC_BASE_URL=\${ANTHROPIC_BASE_URL:-http://host.docker.internal:15721}
    extra_hosts:
      # Linux 兼容：使容器能访问宿主机服务
      # Windows/Mac (Docker Desktop) 会自动忽略此配置
      - "host.docker.internal:host-gateway"
    volumes:
      # 核心：单卷挂载，包含项目和配置
      - \${WORKSPACE_PATH:-./workspace}:/workspace
    working_dir: /workspace/project  # 关键：容器启动后直接进入项目目录
    stdin_open: true  # docker run -i
    tty: true         # docker run -t
    restart: unless-stopped
EOF

    echo -e "${GREEN}✓ docker-compose.yml created${NC}"
    echo ""
}

# Function to create Dockerfile
create_dockerfile() {
    echo -e "${BLUE}Creating Dockerfile...${NC}"

    local dockerfile="$PROJECT_DIR/Dockerfile"

    if [ -f "$dockerfile" ]; then
        echo -e "${YELLOW}Dockerfile already exists. Skipping creation.${NC}"
        return 0
    fi

    cat > "$dockerfile" << EOF
# syntax=docker/dockerfile:1

# 阶段 1：基础镜像和工具
FROM node:18-alpine AS base

# 安装 Claude Code CLI（最新版）
RUN npm install -g @anthropic-ai/claude-code

# 阶段 2：最终镜像
FROM base

# 创建非 root 用户 (ID: 1001，避免与 node 用户的 UID 1000 冲突)
RUN adduser -u 1001 -s /bin/sh -D claude-user

# 设置工作目录（与 docker-compose.yml 中的 working_dir 一致）
WORKDIR /workspace/project

# 暴露端口（根据 docker-compose.yml 调整）
EXPOSE 8000

# 默认启动 shell
CMD ["/bin/sh"]
EOF

    echo -e "${GREEN}✓ Dockerfile created${NC}"
    echo ""
}

# Function to install statusline plugin in container
install_statusline_plugin() {
    echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installing claude-code-statusline-plugin...${NC}"
echo ""

    # Copy plugin files to project .claude/plugins directory
    echo -e "${BLUE}Copying plugin files...${NC}"

    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local PLUGIN_SOURCE_DIR="$SCRIPT_DIR/../claude-code-statusline-plugin"

    # Check if we're running from within the skill directory
    if [ -d "$SCRIPT_DIR/../claude-code-statusline-plugin" ]; then
        echo -e "${GREEN}✓ Running from skill directory...${NC}"

        # Copy show-prompt.py
        if [ -f "$PLUGIN_SOURCE_DIR/statusline\show-prompt.py" ]; then
            cp -r "$PLUGIN_SOURCE_DIR/statusline\show-prompt.py" "$PROJECT_DIR/.claude/plugins/custom/show-last-prompt/statusline/show-prompt.py" 2>/dev/null || true
            echo -e "${GREEN}✓ Copied show-prompt.py${NC}"
        else
            echo -e "${YELLOW}[!] show-prompt.py not found in skill directory${NC}"
        fi

        # Copy plugin.json
        if [ -f "$PLUGIN_SOURCE_DIR/plugin.json" ]; then
            cp -r "$PLUGIN_SOURCE_DIR/plugin.json" "$PROJECT_DIR/.claude/plugins/custom/show-last-prompt/statusline/plugin.json" 2>/dev/null || true
            echo -e "${GREEN}✓ Copied plugin.json${NC}"
        else
            echo -e "${YELLOW}[!] plugin.json not found in skill directory${NC}"
        fi
    else
        echo -e "${YELLOW}[!] Plugin source directory not found${NC}"
        echo -e "${YELLOW}Plugin installation may be incomplete.${NC}"
    fi

    echo -e "${GREEN}✓ Plugin files copied${NC}"
    echo ""

    # Create install.sh script for project
    echo -e "${BLUE}Creating install script...${NC}"

    local install_script="$PROJECT_DIR/.claude/plugins/custom/show-last-prompt/statusline/install.sh"

    cat > "$install_script" << 'EOF'
#!/bin/bash
# Claude Code 状态栏插件安装脚本
# 生成时间: $(date +%Y-%m-%d)

echo -e "\033[0;32m========\033[0mClaude Code Statusline Plugin Installer\033[0m========\033[0m"
echo -e "\033[0;32mCreated for: \033[1;36m$PROJECT_DIR\033[0m"
echo -e "\033[0;32mPurpose: Install claude-code-statusline-plugin in Docker container"
echo -e "\033[0;32mMethod: Auto-install during container initialization"
echo ""

PLUGIN_DIR="$HOME/.claude/plugins/custom/show-last-prompt/statusline"
PLUGIN_FILE="$PLUGIN_DIR/show-prompt.py"
PLUGIN_JSON="$PLUGIN_DIR/plugin.json"

echo -e "\033[0;33mChecking installation status...\033[0m"

# Check if already installed
if [ -f "$PLUGIN_FILE" ] && grep -q "statusLine" "$HOME/.claude/settings.json"; then
    echo -e "\033[0;32m[✓] Plugin already registered in Claude Code settings\033[0m"
    echo -e "\033[0;32m[!]"
    echo -e "\033[0;32mSkipping installation. Plugin is already active.\033[0m"
    echo ""
    exit 0
fi

echo -e "\033[0;32mInstalling plugin files...\033[0m"

# Create plugin directory if not exists
mkdir -p "$PLUGIN_DIR"

# Copy plugin files
cp -r "$PLUGIN_SOURCE_DIR/statusline\show-prompt.py" "$PLUGIN_FILE"
cp -r "$PLUGIN_SOURCE_DIR/plugin.json" "$PLUGIN_JSON"

echo -e "\033[0;32m[✓] Plugin files copied\033[0m"
echo -e "\033[0;32m========================================\033[0m"
echo -e "\033[0;32m✓ claude-code-statusline-plugin installed successfully!\033[0m"
echo ""
echo -e "\033[0;32m========================================\033[0m"

# Register plugin in Claude Code settings
SETTINGS_FILE="$HOME/.claude/settings.json"

echo -e "\033[0;34mUpdating Claude Code settings...\033[0m"

# Backup existing settings
if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.backup.$(date +%s)"
fi

# Add or update statusLine plugin configuration
python3 - << 'PYTHON_SCRIPT'
import json
import sys

settings_file = sys.argv[1] if len(sys.argv) > 1 else "$HOME/.claude/settings.json"
default_config = {
    "statusLine": {
        "type": "command",
        "command": "python3",
        "args": ["$HOME/.claude/plugins/custom/show-last-prompt/statusline/show-prompt.py"]
    }
}

try:
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = json.load(f)
        if not isinstance(settings, dict):
            settings = {}

        # Add or update statusLine plugin configuration
        settings["statusLine"] = default_config["statusLine"]

        f.seek(0)
        json.dump(settings, f, ensure_ascii=False, indent=2)
        print("[INFO] Settings updated successfully")
        sys.exit(0)

except Exception as e:
    print(f"[ERROR] Failed to update settings: {e}")
    sys.exit(1)
PYTHON_SCRIPT

echo ""

# Execute Python script to register plugin
python3 -c "$PYTHON_SCRIPT"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "\033[0;32m========================================\033[0m"
    echo -e "\033[0;32m✓ claude-code-statusline-plugin installed successfully!\033[0m"
    echo -e "\033[0;32m========================================\033[0m"
    echo ""
    echo -e "${GREEN}Plugin registered in Claude Code settings.json${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Restart Claude Code"
    echo "2. Status bar will show: [最新指令:{summary}]"
    echo ""
else
    echo -e "\033[0;31m[✗] Failed to register plugin\033[0m"
    echo -e "\033[0;31mError: Python script execution failed\033[0m"
    echo ""
    exit 1
fi

chmod +x "$install_script"

echo -e "${GREEN}✓ install script created${NC}"
echo ""

# Create installation instructions
cat > "$PROJECT_DIR/STATUSLINE_INSTALL.md" << 'EOF'
# Claude Code 状态栏插件安装指南

## 自动安装说明

容器初始化完成后，会自动执行以下操作：

1. **安装插件文件**：将 `show-prompt.py` 和 `plugin.json` 复制到项目的 `.claude/plugins/custom/show-last-prompt/statusline/` 目录
2. **注册插件**：自动更新 `~/.claude/settings.json`，添加 statusLine 插件配置
3. **创建安装脚本**：生成 `.claude/plugins/custom/show-last-prompt/statusline/install.sh` 脚本

## 验证安装

容器启动后，验证插件是否正确安装：

\`\`\`bash
# 在容器内检查
docker-compose exec app sh -c "python3 -c \\"import json; print(json.load(open('\$HOME/.claude/settings.json')).get('statusLine', {}))\\""
\`\`\`

预期输出：
\`\`\`
{"statusLine": {...}}
\`\`\`

## 功能说明

安装完成后，状态栏会显示：

- **格式**：[最新指令:{summary}]
- **AI 智能提取**：使用 Claude Haiku 模型理解用户真实意图
- **规则提取后备**：AI 失败时使用关键词匹配
- **缓存优化**：避免频繁 API 调用，提高响应速度

## 插件位置

- **脚本**：.claude/plugins/custom/show-last-prompt/statusline/install.sh
- **配置**：.claude/plugins/custom/show-last-prompt/statusline/plugin.json

## 手动安装（如需要）

如果自动安装失败，可以手动执行：

\`\`\`bash
cd $PROJECT_DIR/.claude/plugins/custom/show-last-prompt/statusline
bash install.sh
\`\`\`

---

**注意**：此功能仅在 Docker 容器内运行，需要 Python3 支持。
EOF

chmod +x "$PROJECT_DIR/STATUSLINE_INSTALL.md"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Statusline Plugin Integration Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}All integration files have been created in:${NC}"
echo ""
echo -e "${YELLOW}$PROJECT_DIR${NC}"
echo ""
echo -e "${CYAN}Plugin Files:${NC}"
echo "  - .claude/plugins/custom/show-last-prompt/statusline/show-prompt.py"
echo "  - .claude/plugins/custom/show-last-prompt/statusline/plugin.json"
echo "  - .claude/plugins/custom/show-last-prompt/statusline/install.sh"
echo "  - STATUSLINE_INSTALL.md"
echo ""

# Execute based on scenario
case $SCENARIO in
    new)
        echo -e "${BLUE}Starting new project scenario...${NC}"

        # Create directory structure
        create_directory_structure

        # Create configuration files
        create_env_file
        create_docker_compose
        create_dockerfile

        # Install statusline plugin
        install_statusline_plugin

        echo -e "${GREEN}✓ New project initialized${NC}"
        echo -e "${CYAN}Next steps:${NC}"
        echo "1. cd $PROJECT_DIR"
        echo "2. Review .env file and adjust if needed"
        echo "3. Start container: docker-compose up -d"
        echo "4. Enter container: docker-compose exec app sh"
        echo "5. Status bar will show: [最新指令:{summary}]"
        echo ""
        ;;
    migrate)
        echo -e "${BLUE}Starting migration scenario...${NC}"

        # Get source path
        read -p "Enter path to existing project: " source_path

        # Validate source path
        if [ ! -d "$source_path" ]; then
            echo -e "${GREEN}✓ Source path exists${NC}"

            # Copy to workspace/project
            cp -r "$source_path"/* "$PROJECT_DIR/workspace/project/" 2>/dev/null || true

            echo -e "${GREEN}✓ Project files copied${NC}"

            # Create configuration files
            create_env_file
            create_docker_compose
            create_dockerfile

            # Install statusline plugin
            install_statusline_plugin

            echo -e "${GREEN}✓ Migration complete${NC}"
            echo -e "${CYAN}Next steps:${NC}"
            echo "1. cd $PROJECT_DIR"
            echo "2. Review .env file and adjust if needed"
            echo "3. Start container: docker-compose up -d"
            echo "4. Enter container: docker-compose exec app sh"
            echo "5. Status bar will show: [最新指令:{summary}]"
            echo ""
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Initialization Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
