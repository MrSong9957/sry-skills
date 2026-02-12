---
name: docker-claude-code
description: Use when setting up isolated Docker environments for Claude Code CLI with API proxy configuration, multi-user support, or needing clean workspace initialization across Windows/macOS/Linux platforms
---

# Docker Claude Code

## Overview

Create isolated, reproducible Docker development environments for Claude Code CLI with persistent storage, multi-user support (root and non-root), and seamless API proxy integration.

## When to Use

```
Need isolated Claude Code environment?
│
├─→ Local environment conflicts? → Use this skill
├─→ Need clean workspace per project? → Use this skill
├─→ Team collaboration standardization? → Use this skill
└─→ Testing with specific Claude versions? → Use this skill
```

**Use when:**
- Setting up isolated Claude Code CLI environments
- Need persistent workspace and configuration across container restarts
- Working with API proxy (CC Switch or similar)
- Team requires standardized development environments
- Testing projects without polluting host system

**Don't use for:**
- Production deployments (different security requirements)
- Simple CLI usage on host (use direct install instead)
- Non-Claude Code workloads

## Agent Orchestration

### Task Difficulty Assessment

```
Task Complexity?
│
├─→ Simple (single file, <50 lines) → Handle directly
├─→ Medium (multiple files, related changes) → Parallel sub-agents
└─→ Complex (cross-cutting concerns, architecture) → Agent team
```

### Parallel Sub-Agents (Medium Complexity)

**Use when:** Independent operations can run simultaneously

**Example:** Setting up Docker environment with multiple concerns
```markdown
Launch 3 sub-agents in parallel:
1. **Agent 1** (Role: Configuration Validator)
   - Task: Validate Docker configuration files syntax
   - Expected output: Validation report

2. **Agent 2** (Role: Platform Specialist)
   - Task: Check platform-specific settings (host.docker.internal)
   - Expected output: Platform configuration adjustments

3. **Agent 3** (Role: Connectivity Tester)
   - Task: Verify API proxy connectivity
   - Expected output: Connection test results
```

**Pattern:** Dispatch simultaneously, wait for all results, synthesize.

### Agent Team Creation (High Complexity)

**Use when:** Task requires specialists with coordination

**Example:** Migrating existing project to Docker environment
```markdown
Create agent team: docker-migration
Members:
- **migration-architect**: Analyzes project structure and dependencies
- **docker-configurer**: Creates Dockerfile/docker-compose.yml
- **platform-specialist**: Handles Windows/macOS/Linux differences
- **test-validator**: Verifies container startup and functionality
```

**Pattern:** Use TeamCreate, assign specialized roles, coordinate via Task tool.

### Automatic Skill Delegation

**Delegate to related skills:**
- **tdd-workflow** → Testing Docker environment setup
- **verification-loop** → Validating container functionality
- **security-review** → Reviewing container security before deployment
- **backend-patterns** → Setting up containerized API services

## Platform Configuration

### Quick Decision Table

| Platform | `host.docker.internal` | Extra Action |
|----------|------------------------|--------------|
| **Windows** (Docker Desktop) | ✅ Works | None |
| **macOS** (Docker Desktop) | ✅ Works | None |
| **Linux** | ⚠️ Needs config | Add `extra_hosts` |

### Platform-Specific Actions

**Windows/macOS:**
```bash
# Default configuration works
ANTHROPIC_BASE_URL=http://host.docker.internal:15721
```

**Linux:**
```bash
# Option 1: Use extra_hosts (recommended)
# docker-compose.yml includes:
extra_hosts:
  - "host.docker.internal:host-gateway"

# Option 2: Use host IP directly
hostname -I | awk '{print $1}'  # Get IP
ANTHROPIC_BASE_URL=http://<IP>:15721
```

**Detection Command:**
```bash
# Auto-detect platform
uname -s  # Darwin=macOS, Linux=Linux, MINGW*=Windows
```

## Core Pattern

### Before (Host Installation)
```bash
# Problems: Version conflicts, pollution, hard to reset
npm install -g @anthropic-ai/claude-code
# Global dependencies, hard to isolate per project
```

### After (Docker Environment)
```bash
# Clean, isolated, reproducible
docker-compose up -d
docker-compose exec app claude  # Non-root user
docker-compose exec -u root app bash  # Root user
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start container in background |
| `docker-compose exec app claude` | Enter as non-root user |
| `docker-compose exec -u root app bash` | Enter as root user |
| `docker-compose logs -f` | Follow container logs |
| `docker-compose down` | Stop and remove container |
| `docker-compose exec app workspace` | Show workspace path |

## Auxiliary Scripts

**Location:** `scripts/` directory within this skill

**Purpose:** Automated helpers for Docker environment setup, validation, and diagnostics.

### Available Scripts

| Script | Purpose | Usage |
|---------|---------|-------|
| `detect-platform.sh` | Detect platform and recommend configuration | `bash scripts/detect-platform.sh` |
| `validate-config.sh` | Validate Docker files and settings | `bash scripts/validate-config.sh` |
| `diagnose-docker.sh` | Diagnose container issues | `bash scripts/diagnose-docker.sh` |
| `init-docker-project.sh` | Initialize new or migrate existing project | `bash scripts/init-docker-project.sh` |

### Script Features

**Platform Detection** (`detect-platform.sh`):
- Auto-detects Windows/macOS/Linux using `uname -s`
- Displays platform configuration table
- Outputs recommended ANTHROPIC_BASE_URL
- Exports `DETECTED_PLATFORM` variable for downstream scripts

**Config Validation** (`validate-config.sh`):
- Checks for required files (.env, docker-compose.yml, Dockerfile)
- Validates environment variables
- Verifies platform-specific configurations
- Tests volume mounts and permissions
- Returns detailed report with error/warning counts

**Diagnostics** (`diagnose-docker.sh`):
- Follows troubleshooting decision tree
- Tests Docker daemon status
- Checks container status and environment variables
- Verifies API proxy connectivity
- Tests volume mounts and permissions
- Provides quick fix suggestions

**Project Initialization** (`init-docker-project.sh`):
- Interactive menu for new or migrate scenarios
- Creates directory structure automatically
- Generates configuration files (.env, docker-compose.yml, Dockerfile)
- Platform-aware setup (adds extra_hosts for Linux)
- Copies existing projects to workspace/project
- **Auto-installs statusline plugin** - Copies and configures claude-code-statusline-plugin

### Statusline Plugin Integration

The `init-docker-project.sh` script automatically integrates the claude-code-statusline-plugin:

**What it does:**
- Copies `show-prompt.py` to `.claude/plugins/custom/show-last-prompt/statusline/`
- Generates `install.sh` script for container setup
- Registers plugin in `~/.claude/settings.json`
- Creates `STATUSLINE_INSTALL.md` with instructions

**Status Bar Display:**
```
[最新指令:创建Django项目...]
```

**Features:**
- AI-powered task extraction using Claude Haiku
- Rule-based fallback for offline operation
- Cache optimization for consistent display
- Chinese and English support

**Plugin Location:** See repository root `claude-code-statusline-plugin/` directory

### Usage Examples

**Initialize new project:**
```bash
cd .claude/skills/docker-claude-code
bash scripts/init-docker-project.sh
# Select: 1) New Project
```

**Validate existing setup:**
```bash
cd .claude/skills/docker-claude-code
bash scripts/validate-config.sh
```

**Diagnose issues:**
```bash
cd .claude/skills/docker-claude-code
bash scripts/diagnose-docker.sh
```

## Implementation

### Directory Structure

```
project/
├── .env                    # Environment variables
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Image build instructions
├── workspace/             # Development workspace (git ignored)
└── dev-home/              # Persistent Claude config (git ignored)
    ├── claude/            # Claude home directory
    └── config/            # Claude config directory
```

### Configuration Files

**See [Dockerfile](#dockerfile), [docker-compose.yml](#docker-compose-yml), [.env.example](#env-example) below**

**Detailed configuration files:** See [Chinese tutorial](../../../docs/docker-claude-code.md):
- Section 2.1: `.env` with API proxy setup
- Section 2.2: `docker-compose.yml` with platform compatibility
- Section 2.3: `Dockerfile` with multi-user support

### Environment Variables

Required in `.env`:

```bash
# API Configuration
ANTHROPIC_API_KEY=dummy  # Uses host's key via proxy
ANTHROPIC_BASE_URL=http://host.docker.internal:15721

# Paths (optional, with defaults)
WORKSPACE_PATH=./workspace
DEV_HOME_PATH=./dev-home/claude
CLAUDE_CONFIG_PATH=./dev-home/config
```

### Multi-User Access

```bash
# Non-root user (claude) - recommended for development
docker-compose exec app claude

# Root user - for system-level operations
docker-compose exec -u root app bash
docker-compose exec -u root app claude  # Run claude as root
```

## Supporting Files

### Dockerfile

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-slim

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Create non-root user
RUN groupadd -r claude && useradd -r -g claude -G sudo -m -s /bin/bash claude

# Set up sudo for non-root user
RUN echo "claude ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create workspace directory
RUN mkdir -p /workspace && chown -R claude:claude /workspace

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER claude

# Default command
CMD ["bash"]
```

### docker-compose.yml

```yaml
services:
  app:
    build: .
    container_name: docker-claude-code-app
    ports:
      - "8080:8000"  # Optional: for any web services
    environment:
      - ENV=development
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL:-http://host.docker.internal:15721}
    volumes:
      # Project files (read-only to prevent hot-reload issues)
      - .:/app:ro
      # Development workspace (read-write)
      - ${WORKSPACE_PATH:-./workspace}:/workspace
      # Claude home directory (persistent config)
      - ${DEV_HOME_PATH:-./dev-home/claude}:/home/claude
      # Claude config directory
      - ${CLAUDE_CONFIG_PATH:-./dev-home/config}:/home/claude/.config/claude
    working_dir: /workspace
    stdin_open: true  # docker run -i
    tty: true         # docker run -t
    restart: unless-stopped
```

### .env.example

```bash
# Claude Code CLI Configuration
# dummy 表示沿用宿主机的 API KEY
ANTHROPIC_API_KEY=dummy

# 端口要与 CC Switch 本地代理端口一致
ANTHROPIC_BASE_URL=http://host.docker.internal:15721

# Optional: Custom paths (defaults shown)
# WORKSPACE_PATH=./workspace
# DEV_HOME_PATH=./dev-home/claude
# CLAUDE_CONFIG_PATH=./dev-home/config
```

### .gitignore

```gitignore
# Environment variables
.env

# Docker volumes
workspace/
dev-home/
```

## Troubleshooting

### Diagnostic Decision Tree

```
Container not working?
│
├─→ API connection fails? → Check ANTHROPIC_BASE_URL
├─→ Permission denied? → Switch to root user
├─→ Can't find host? → Verify platform-specific config
└─→ Config not persisting? → Check volume mounts
```

### Common Issues

| Symptom | Diagnosis | Fix |
|----------|-----------|-----|
| `ENOTFOUND host.docker.internal` | Linux without extra_hosts | Add `extra_hosts` to docker-compose.yml |
| Permission denied writing files | Non-root user needs elevated access | `docker-compose exec -u root app bash` |
| Config lost on restart | Volume not mounted | Check `volumes:` section |
| CLI can't reach API | Wrong proxy port | Match port to CC Switch (default 15721) |

### Platform-Specific Fixes

**Linux only:**
```bash
# Test host.docker.internal resolution
docker-compose exec app nslookup host.docker.internal
```

**All platforms:**
```bash
# Verify environment variables
docker-compose exec app sh -c 'echo $ANTHROPIC_API_KEY && echo $ANTHROPIC_BASE_URL'
```

## Common Mistakes

### Mistake 1: Not Using `host.docker.internal`

```yaml
# WRONG: Won't work from container
ANTHROPIC_BASE_URL=http://localhost:15721

# CORRECT: Special DNS name for host access
ANTHROPIC_BASE_URL=http://host.docker.internal:15721
```

### Mistake 2: Mounting Project Files Read-Write

```yaml
# WRONG: Causes hot-reload scanning issues
volumes:
  - .:/app

# CORRECT: Read-only mount for config
volumes:
  - .:/app:ro
```

### Mistake 3: Forgetting `stdin_open` and `tty`

```yaml
# WRONG: Won't allow interactive CLI
# Missing stdin_open and tty

# CORRECT: Required for interactive sessions
stdin_open: true
tty: true
```

### Mistake 4: Not Persisting Claude Config

```yaml
# WRONG: Loses config on container restart
# No volume mounts for /home/claude

# CORRECT: Persist Claude home and config
volumes:
  - ./dev-home/claude:/home/claude
  - ./dev-home/config:/home/claude/.config/claude
```

### Mistake 5: Using Only Root User

```bash
# RISKY: Running everything as root
docker-compose exec -u root app bash

# BETTER: Use non-root user for development
docker-compose exec app claude

# ROOT: Only for system operations
docker-compose exec -u root app bash  # Install system packages
```

## Real-World Impact

**Benefits:**
- Isolation: Project dependencies don't conflict
- Reproducibility: Team uses identical environments
- Clean slate: Reset workspace by deleting volume
- Version control: Dockerfile tracks CLI version
- Multi-user: Safe development (non-root) + admin access (root)

**Use Cases:**
- Node.js projects with conflicting dependencies
- Python environments requiring specific Claude versions
- Team onboarding: `docker-compose up` and ready
- Testing: Isolate breaking changes from main environment
