#!/bin/bash
# Configuration Validation Script for Docker Claude Code
# Validates Docker configuration files and platform compatibility

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
CHECKS=0

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Docker Claude Code - Config Validator${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to print check result
print_result() {
    CHECKS=$((CHECKS + 1))
    local status=$1
    local message=$2

    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}[✓]${NC} $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}[!]${NC} $message"
        WARNINGS=$((WARNINGS + 1))
    elif [ "$status" = "ERROR" ]; then
        echo -e "${RED}[✗]${NC} $message"
        ERRORS=$((ERRORS + 1))
    fi
}

# Detect current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Scanning configuration files in:${NC}"
echo "$PROJECT_DIR"
echo ""

# Check 1: .env file exists
if [ -f "$PROJECT_DIR/.env" ]; then
    print_result "OK" ".env file exists"
else
    print_result "ERROR" ".env file not found"
fi

# Check 2: docker-compose.yml exists
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    print_result "OK" "docker-compose.yml exists"
elif [ -f "$PROJECT_DIR/docker-compose.yaml" ]; then
    print_result "WARN" "docker-compose.yaml found (should be .yml for consistency)"
else
    print_result "ERROR" "docker-compose.yml not found"
fi

# Check 3: Dockerfile exists
if [ -f "$PROJECT_DIR/Dockerfile" ]; then
    print_result "OK" "Dockerfile exists"
else
    print_result "ERROR" "Dockerfile not found"
fi

echo ""
echo -e "${BLUE}Platform Compatibility Checks:${NC}"
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

print_result "OK" "Platform detected: $PLATFORM_NAME"

# Check 4: Validate .env content if exists
if [ -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo -e "${BLUE}Environment Variable Checks:${NC}"

    # Check for ANTHROPIC_API_KEY
    if grep -q "ANTHROPIC_API_KEY" "$PROJECT_DIR/.env" 2>/dev/null; then
        print_result "OK" "ANTHROPIC_API_KEY is set"
    else
        print_result "ERROR" "ANTHROPIC_API_KEY not found in .env"
    fi

    # Check for ANTHROPIC_BASE_URL
    if grep -q "ANTHROPIC_BASE_URL" "$PROJECT_DIR/.env" 2>/dev/null; then
        print_result "OK" "ANTHROPIC_BASE_URL is set"

        # Check if using host.docker.internal
        if grep -q "host.docker.internal" "$PROJECT_DIR/.env" 2>/dev/null; then
            if [ "$PLATFORM_ID" = "linux" ]; then
                # Linux needs extra_hosts for host.docker.internal
                if [ -f "$PROJECT_DIR/docker-compose.yml" ] && grep -q "extra_hosts" "$PROJECT_DIR/docker-compose.yml" 2>/dev/null; then
                    print_result "OK" "Linux with extra_hosts configured"
                else
                    print_result "ERROR" "Linux platform needs extra_hosts in docker-compose.yml"
                fi
            else
                print_result "OK" "Using host.docker.internal (correct for $PLATFORM_NAME)"
            fi
        elif grep -q "localhost:15721" "$PROJECT_DIR/.env" 2>/dev/null; then
            print_result "ERROR" "Using localhost (won't work from container)"
        fi
    else
        print_result "WARN" "ANTHROPIC_BASE_URL not set"
    fi
fi

# Check 5: Validate docker-compose.yml if exists
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    echo ""
    echo -e "${BLUE}Docker Compose Configuration Checks:${NC}"

    # Check for stdin_open and tty
    if grep -q "stdin_open: true" "$PROJECT_DIR/docker-compose.yml" 2>/dev/null; then
        print_result "OK" "stdin_open: true (required for interactive CLI)"
    else
        print_result "ERROR" "Missing stdin_open: true"
    fi

    if grep -q "tty: true" "$PROJECT_DIR/docker-compose.yml" 2>/dev/null; then
        print_result "OK" "tty: true (required for interactive CLI)"
    else
        print_result "ERROR" "Missing tty: true"
    fi

    # Check for working_dir
    if grep -q "working_dir:" "$PROJECT_DIR/docker-compose.yml" 2>/dev/null; then
        print_result "OK" "working_dir is set"
    else
        print_result "WARN" "working_dir not set (container may start in wrong directory)"
    fi

    # Check for volume mounts
    if grep -q "volumes:" "$PROJECT_DIR/docker-compose.yml" 2>/dev/null; then
        print_result "OK" "volumes are configured"
    else
        print_result "ERROR" "No volumes found (config won't persist)"
    fi
fi

# Check 6: Validate Dockerfile if exists
if [ -f "$PROJECT_DIR/Dockerfile" ]; then
    echo ""
    echo -e "${BLUE}Dockerfile Checks:${NC}"

    # Check for USER instruction
    if grep -q "USER" "$PROJECT_DIR/Dockerfile" 2>/dev/null; then
        print_result "OK" "User is set (multi-user support)"
    else
        print_result "WARN" "No USER instruction (running as root)"
    fi

    # Check for WORKDIR
    if grep -q "WORKDIR" "$PROJECT_DIR/Dockerfile" 2>/dev/null; then
        print_result "OK" "WORKDIR is set"
    else
        print_result "WARN" "No WORKDIR set"
    fi
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Validation Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Total Checks: ${BLUE}$CHECKS${NC}"
echo -e "${GREEN}Passed:${NC} $((CHECKS - ERRORS - WARNINGS))"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Errors:${NC} $ERRORS"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Configuration is valid.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation passed with warnings. Review recommended.${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed! Please fix errors above.${NC}"
    exit 1
fi
