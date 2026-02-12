#!/bin/bash
# Platform Detection Script for Docker Claude Code
# Detects current platform and provides recommended configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Docker Claude Code - Platform Detection${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Detect platform
OS_TYPE=$(uname -s)

case "$OS_TYPE" in
    Darwin)
        PLATFORM="macOS"
        PLATFORM_ID="macos"
        DOCKER_DESKTOP="Docker Desktop"
        HOST_ALIAS="host.docker.internal"
        EXTRA_ACTION="None (native support)"
        ;;
    Linux)
        PLATFORM="Linux"
        PLATFORM_ID="linux"
        DOCKER_DESKTOP="Docker Engine / Podman"
        HOST_ALIAS="host.docker.internal (requires extra_hosts)"
        EXTRA_ACTION="Add 'extra_hosts: - \"host.docker.internal:host-gateway\"' to docker-compose.yml"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM="Windows"
        PLATFORM_ID="windows"
        DOCKER_DESKTOP="Docker Desktop"
        HOST_ALIAS="host.docker.internal"
        EXTRA_ACTION="None (native support)"
        ;;
    *)
        PLATFORM="Unknown"
        PLATFORM_ID="unknown"
        DOCKER_DESKTOP="Unknown"
        HOST_ALIAS="localhost"
        EXTRA_ACTION="Check Docker documentation"
        ;;
esac

# Output results
echo -e "${YELLOW}Detected Platform:${NC} $PLATFORM"
echo ""

# Display platform information table
echo -e "${GREEN}Platform Configuration:${NC}"
echo "┌───────────────────────────────────────────────────────────────────────────┐"
echo "│ Platform        │ Docker Desktop   │ host.docker.internal │ Extra Action    │"
echo "├─────────────────┼─────────────────┼─────────────────────┼─────────────────┤"
echo "│ $PLATFORM        │ $DOCKER_DESKTOP  │ $HOST_ALIAS      │ $EXTRA_ACTION │"
echo "└───────────────────────────────────────────────────────────────────────────┘"
echo ""

# Recommended .env configuration
echo -e "${GREEN}Recommended ANTHROPIC_BASE_URL:${NC}"
echo ""

if [ "$PLATFORM_ID" = "macos" ] || [ "$PLATFORM_ID" = "windows" ]; then
    echo -e "${GREEN}ANTHROPIC_BASE_URL=http://host.docker.internal:15721${NC}"
    echo -e "${YELLOW}(Default configuration works natively)${NC}"
elif [ "$PLATFORM_ID" = "linux" ]; then
    echo -e "${YELLOW}Option 1 (Recommended):${NC}"
    echo -e "${GREEN}ANTHROPIC_BASE_URL=http://host.docker.internal:15721${NC}"
    echo "Add to docker-compose.yml:"
    echo "  extra_hosts:"
    echo "    - \"host.docker.internal:host-gateway\""
    echo ""
    echo -e "${YELLOW}Option 2 (Alternative):${NC}"
    echo -e "${GREEN}ANTHROPIC_BASE_URL=http://\$(hostname -I | awk '{print \\\$1}'):15721${NC}"
    echo "(Get host IP with: hostname -I | awk '{print \$1}')"
else
    echo -e "${RED}Platform: $PLATFORM${NC}"
    echo "Please check Docker documentation for platform-specific configuration"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Detection Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Export platform ID for use in other scripts
export DETECTED_PLATFORM="$PLATFORM_ID"
echo ""
echo -e "${YELLOW}Exported variable:${NC} DETECTED_PLATFORM=$PLATFORM_ID"
