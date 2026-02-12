#!/bin/bash
# Diagnostic Script for Docker Claude Code
# Diagnoses Docker environment issues following troubleshooting decision tree

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Docker Claude Code - Diagnostics${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Detect current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR" || exit 1

echo -e "${BLUE}Working Directory:${NC} $PROJECT_DIR"
echo ""

# Decision Tree: Container not working?
echo -e "${CYAN}Diagnostic Decision Tree:${NC}"
echo "Container not working?"
echo "├─→ API connection fails? → Check ANTHROPIC_BASE_URL"
echo "├─→ Permission denied? → Switch to root user"
echo "├─→ Can't find host? → Verify platform-specific config"
echo "└─→ Config not persisting? → Check volume mounts"
echo ""

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

echo -e "${CYAN}Platform:${NC} $PLATFORM_NAME"
echo ""

# Check 1: Docker daemon is running
echo -e "${BLUE}Check 1: Docker Daemon Status${NC}"
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}[✓]${NC} Docker daemon is running"
else
    echo -e "${RED}[✗]${NC} Docker daemon is NOT running"
    echo -e "${YELLOW}Fix:${NC} Start Docker Desktop or Docker Engine"
    echo ""
    exit 1
fi
echo ""

# Check 2: Container status
echo -e "${BLUE}Check 2: Container Status${NC}"
CONTAINER_NAME="docker-claude-code-app"

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${GREEN}[✓]${NC} Container '$CONTAINER_NAME' is running"
    RUNNING=true
elif docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}[!]${NC} Container exists but is STOPPED"
    echo -e "${YELLOW}Fix:${NC} docker-compose up -d"
    RUNNING=false
else
    echo -e "${RED}[✗]${NC} Container '$CONTAINER_NAME' does NOT exist"
    echo -e "${YELLOW}Fix:${NC} Run: docker-compose up -d"
    RUNNING=false
fi
echo ""

# Only continue checks if container is running
if [ "$RUNNING" = true ]; then
    # Check 3: Environment variables in container
    echo -e "${BLUE}Check 3: Environment Variables${NC}"

        API_KEY=$(docker-compose exec -T app sh -c 'echo $ANTHROPIC_API_KEY' 2>/dev/null || echo "")
        BASE_URL=$(docker-compose exec -T app sh -c 'echo $ANTHROPIC_BASE_URL' 2>/dev/null || echo "")

    if [ -n "$API_KEY" ]; then
        echo -e "${GREEN}[✓]${NC} ANTHROPIC_API_KEY is set"
    else
        echo -e "${RED}[✗]${NC} ANTHROPIC_API_KEY is NOT set"
        echo -e "${YELLOW}Fix:${NC} Check .env file and restart container"
    fi

    if [ -n "$BASE_URL" ]; then
        echo -e "${GREEN}[✓]${NC} ANTHROPIC_BASE_URL is set to: $BASE_URL"

        # Check if using host.docker.internal
        if echo "$BASE_URL" | grep -q "host.docker.internal"; then
            echo -e "${GREEN}[✓]${NC} Using host.docker.internal (correct)"

            # Platform-specific check for Linux
            if [ "$PLATFORM_ID" = "linux" ]; then
                echo -e "${YELLOW}[!]${NC} Linux platform detected"
                # Test if host.docker.internal resolves
                if docker-compose exec -T app nslookup host.docker.internal >/dev/null 2>&1; then
                    echo -e "${GREEN}[✓]${NC} host.docker.internal resolves correctly (extra_hosts working)"
                else
                    echo -e "${RED}[✗]${NC} host.docker.internal does NOT resolve"
                    echo -e "${YELLOW}Fix:${NC} Add to docker-compose.yml:"
                    echo "  extra_hosts:"
                    echo "    - \"host.docker.internal:host-gateway\""
                fi
            fi
        elif echo "$BASE_URL" | grep -q "localhost:15721"; then
            echo -e "${RED}[✗]${NC} Using localhost (won't work from container)"
            echo -e "${YELLOW}Fix:${NC} Change to host.docker.internal in .env"
        fi
    else
        echo -e "${RED}[✗]${NC} ANTHROPIC_BASE_URL is NOT set"
        echo -e "${YELLOW}Fix:${NC} Check .env file and restart container"
    fi
    echo ""

    # Check 4: API connectivity test
    echo -e "${BLUE}Check 4: API Proxy Connectivity${NC}"

    # Extract host and port from BASE_URL
    if echo "$BASE_URL" | grep -q "http://"; then
        PROXY_HOST=$(echo "$BASE_URL" | sed 's|http://||' | sed 's|:.*||')
        PROXY_PORT=$(echo "$BASE_URL" | sed 's|.*:||')

        echo -e "Testing connection to: ${CYAN}$PROXY_HOST:$PROXY_PORT${NC}"

        # Test from within container
        if docker-compose exec -T app sh -c "nc -z -w5 $PROXY_HOST $PROXY_PORT" 2>/dev/null; then
            echo -e "${GREEN}[✓]${NC} API proxy is reachable from container"
        else
            echo -e "${RED}[✗]${NC} API proxy is NOT reachable"
            echo -e "${YELLOW}Possible causes:${NC}"
            echo "1. CC Switch is not running on host"
            echo "2. Wrong port configured (default: 15721)"
            echo "3. Firewall blocking connection"
            echo ""
            echo -e "${YELLOW}Fix:${NC}"
            echo "- Ensure CC Switch is running on host machine"
            echo "- Verify port: $PROXY_PORT matches CC Switch configuration"
        fi
    fi

    # Check 5: Volume mounts
    echo ""
    echo -e "${BLUE}Check 5: Volume Mounts${NC}"

    if docker inspect "$CONTAINER_NAME" --format '{{json .Mounts}}' | grep -q "workspace"; then
        echo -e "${GREEN}[✓]${NC} Workspace volume is mounted"
    else
        echo -e "${RED}[✗]${NC} Workspace volume is NOT mounted"
        echo -e "${YELLOW}Fix:${NC} Check volumes: section in docker-compose.yml"
    fi

    # Check 6: Permission test
    echo ""
    echo -e "${BLUE}Check 6: File Permissions${NC}"

    # Test write permission
    if docker-compose exec -T app sh -c 'touch /workspace/.test_write 2>/dev/null && rm /workspace/.test_write'; then
        echo -e "${GREEN}[✓]${NC} Write permissions are OK"
    else
        echo -e "${RED}[✗]${NC} Write permission DENIED"
        echo -e "${YELLOW}Fix:${NC}"
        echo "- Switch to root user: docker-compose exec -u root app bash"
        echo "- Or fix permissions: docker-compose exec -u root app chown -R claude-user:claude-user /workspace"
    fi

    # Check 7: Claude CLI installation
    echo ""
    echo -e "${BLUE}Check 7: Claude CLI Installation${NC}"

    CLI_VERSION=$(docker-compose exec -T app sh -c 'claude --version 2>/dev/null || echo "not installed"' 2>/dev/null || echo "not installed")

    if [ "$CLI_VERSION" != "not installed" ]; then
        echo -e "${GREEN}[✓]${NC} Claude CLI is installed: $CLI_VERSION"
    else
        echo -e "${RED}[✗]${NC} Claude CLI is NOT installed"
        echo -e "${YELLOW}Fix:${NC} Rebuild Docker image: docker-compose build"
    fi
else
    echo -e "${YELLOW}Skipping container checks - container is not running${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Diagnostic Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Common quick fixes
echo -e "${CYAN}Common Quick Fixes:${NC}"
echo ""
echo "1. ${YELLOW}Restart container:${NC}"
echo "   docker-compose restart"
echo ""
echo "2. ${YELLOW}Rebuild image:${NC}"
echo "   docker-compose build"
echo "   docker-compose up -d"
echo ""
echo "3. ${YELLOW}View logs:${NC}"
echo "   docker-compose logs -f"
echo ""
echo "4. ${YELLOW}Enter container as root:${NC}"
echo "   docker-compose exec -u root app bash"
echo ""
echo "5. ${YELLOW}Enter container as non-root:${NC}"
echo "   docker-compose exec app sh"
echo ""
