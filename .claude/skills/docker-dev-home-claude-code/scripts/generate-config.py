#!/usr/bin/env python3
"""
Generate Docker configuration files for various project types.
Supports Claude Code CLI installation in container.
"""

import os
import sys
from pathlib import Path


def create_dev_home_structure(dev_home_path="./dev-home"):
    """Create dev-home directory structure for persistent container home directory."""
    dev_home = Path(dev_home_path)

    # Create main directories
    directories = [
        dev_home / "root" / ".config",
        dev_home / "root" / ".cache",
        dev_home / "root" / ".local",
        dev_home / "logs",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"[+] Created directory: {directory}")

    # Create .gitignore
    gitignore_path = dev_home / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# Dev-home persistent data
# Ignore all runtime-generated files
*.[!m][!d]

# But keep this .gitignore file
!.gitignore
!README.md
"""
        gitignore_path.write_text(gitignore_content)
        print(f"[+] Created: {gitignore_path}")

    # Create README.md
    readme_path = dev_home / "README.md"
    if not readme_path.exists():
        readme_content = """# Dev-Home Directory

This directory contains persistent data from the Docker container's `/root` directory.

## Directory Structure

```
dev-home/
├── root/              # Container /root directory mount point
│   ├── .config/       # Configuration files
│   ├── .cache/        # Cache data
│   ├── .local/        # Local data
│   └── .ssh/          # SSH keys (if generated)
├── config/            # Claude Code specific configuration (optional)
├── logs/              # Log files
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Purpose

- **State Persistence**: Claude Code CLI state, configurations, and cache are preserved
- **Container Restart**: Data survives container restarts and rebuilds
- **Multi-Project Sharing**: Can be shared across multiple projects (see below)

## Multi-Project Sharing

To share dev-home across multiple projects:

1. Create a shared dev-home directory:
   ```
   cd ~/PycharmProjects
   mkdir dev-home
   ```

2. In each project's `.env` file, set:
   ```
   DEV_HOME_PATH=../dev-home
   ```

3. Restart containers:
   ```
   docker-compose down
   docker-compose up -d
   ```

**Benefits:**
- Shared Claude Code authentication state
- Shared configurations and preferences
- Reduced disk space usage

**Caveats:**
- Concurrent access may cause conflicts (rare)
- All projects share the same Claude Code context

## Backup and Restore

### Backup
```bash
# Create a timestamped backup
tar -czf dev-home-backup-$(date +%Y%m%d-%H%M%S).tar.gz dev-home/

# Or using rsync
rsync -av dev-home/ /path/to/backup/dev-home/
```

### Restore
```bash
# Extract backup
tar -xzf dev-home-backup-YYYYMMDD-HHMMSS.tar.gz

# Or using rsync
rsync -av /path/to/backup/dev-home/ dev-home/
```

## Cleanup

To clean cache and free disk space:

```bash
# Clean cache (safe to delete)
rm -rf dev-home/root/.cache/*

# Clean logs (safe to delete)
rm -rf dev-home/logs/*

# Clean all data (will reset Claude Code state)
rm -rf dev-home/root/*
```

**Warning**: Deleting `dev-home/root/.config/` will reset all Claude Code configurations.

## Troubleshooting

### Permission Issues
Files in `dev-home/root/` are owned by root (container user). This is normal on Linux/Mac.
To fix permissions for editing:

```bash
# Take ownership (Linux/Mac)
sudo chown -R $USER:$USER dev-home/root/

# Or use specific user/group
sudo chown -R 1000:1000 dev-home/root/
```

### Disk Space
Monitor dev-home size:

```bash
# Check size
du -sh dev-home/

# Check largest directories
du -sh dev-home/root/* | sort -hr
```

### Data Not Persisting
1. Check `.env` file has `DEV_HOME_PATH` set correctly
2. Verify docker-compose.yml volumes section includes dev-home mounts
3. Restart container: `docker-compose restart`
"""
        readme_path.write_text(readme_content)
        print(f"[+] Created: {readme_path}")


def get_project_name():
    """Get project name from current directory."""
    return Path.cwd().name.replace("_", "-").replace(" ", "-").lower()


def get_dockerfile_templates():
    """Return Dockerfile templates for each project type."""
    return {
        "claude": """FROM node:20-alpine

WORKDIR /app

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install common utilities
RUN apk add --no-cache \\
    git \\
    curl \\
    bash \\
    python3 \\
    py3-pip \\
    vim

# Copy project files
COPY . .

# Keep container running for interactive use
CMD ["/bin/sh"]
""",
        "python": """FROM python:3.11-slim

WORKDIR /app

# Install Node.js for Claude Code CLI
RUN apt-get update && apt-get install -y \\
    curl \\
    gnupg \\
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \\
    && apt-get install -y nodejs \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install Python dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy project files
COPY . .

# Default command
CMD ["/bin/bash"]
""",
        "node": """FROM node:20-alpine

WORKDIR /app

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install dependencies if package.json exists
RUN if [ -f package.json ]; then npm install; fi

# Copy project files
COPY . .

# Keep container running for interactive use
CMD ["/bin/sh"]
""",
        "go": """FROM golang:1.21-alpine

WORKDIR /app

# Install Node.js for Claude Code CLI
RUN apk add --no-cache nodejs npm

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install Go dependencies
RUN if [ -f go.mod ]; then go mod download; fi

# Copy project files
COPY . .

# Keep container running for interactive use
CMD ["/bin/sh"]
""",
        "java": """FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Install Node.js for Claude Code CLI
RUN apk add --no-cache nodejs npm

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Copy project files
COPY . .

# Keep container running for interactive use
CMD ["/bin/sh"]
""",
        "generic": """FROM alpine:latest

WORKDIR /app

# Install Node.js for Claude Code CLI
RUN apk add --no-cache nodejs npm

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install common utilities
RUN apk add --no-cache \\
    git \\
    curl \\
    bash \\
    python3 \\
    py3-pip

# Copy project files
COPY . .

# Keep container running for interactive use
CMD ["/bin/sh"]
""",
    }


def get_dockerignore_content():
    """Return .dockerignore content."""
    return """# Git
.git
.gitignore
.gitattributes

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Documentation
README.md
*.md

# IDE
.vscode
.idea
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.*.local

# Dependencies
node_modules
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build

# Logs
*.log
logs

# OS
.DS_Store
Thumbs.db

# Claude Code
.claude

# Dev-home
dev-home/
"""


def get_docker_compose_template():
    """Return docker-compose.yml template with persistent volumes."""
    return """version: '3.8'

services:
  app:
    build: .
    container_name: {project_name}-app
    ports:
      - "8080:8080"
    environment:
      - ENV=development
      - ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY}}
      - ANTHROPIC_BASE_URL=${{ANTHROPIC_BASE_URL}}
    volumes:
      - .:/app
      - /app/node_modules
      - /app/__pycache__
      - ${{DEV_HOME_PATH:-./dev-home}}/root:/root
      - ${{CLAUDE_CONFIG_PATH:-./dev-home}}/config:/root/.config/claude
    working_dir: /app
    stdin_open: true
    tty: true
    restart: unless-stopped
"""


def get_env_example():
    """Return .env.example content."""
    return """# Anthropic API Key for Claude Code CLI
# Get your API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_api_key_here

# Anthropic Base URL (optional)
# Use this for API proxy, custom endpoint, or compatibility service
# ANTHROPIC_BASE_URL=https://api.anthropic.com

# Environment
ENV=development

# Dev-home path (optional, default: ./dev-home)
# Use relative path for multi-project sharing: ../dev-home
# Use absolute path for custom location: /path/to/dev-home
DEV_HOME_PATH=./dev-home

# Claude config path (optional, default: ./dev-home)
# CLAUDE_CONFIG_PATH=./dev-home
"""


def generate_files(project_type="generic", dev_home_path="./dev-home"):
    """Generate all configuration files."""
    project_name = get_project_name()
    templates = get_dockerfile_templates()

    if project_type not in templates:
        print(f"[X] Unknown project type: {project_type}")
        print(f"    Valid types: {', '.join(templates.keys())}")
        sys.exit(1)

    # Create dev-home directory structure
    print("\n[*] Creating dev-home directory structure...")
    create_dev_home_structure(dev_home_path)

    # Generate Dockerfile
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        dockerfile_path.write_text(templates[project_type])
        print(f"[+] Created: Dockerfile ({project_type})")
    else:
        print(f"[~] Skipped: Dockerfile (already exists)")

    # Generate .dockerignore
    dockerignore_path = Path(".dockerignore")
    if not dockerignore_path.exists():
        dockerignore_path.write_text(get_dockerignore_content())
        print(f"[+] Created: .dockerignore")
    else:
        print(f"[~] Skipped: .dockerignore (already exists)")

    # Generate docker-compose.yml
    compose_path = Path("docker-compose.yml")
    if not compose_path.exists():
        compose_content = get_docker_compose_template().format(project_name=project_name)
        compose_path.write_text(compose_content)
        print(f"[+] Created: docker-compose.yml")
    else:
        print(f"[~] Skipped: docker-compose.yml (already exists)")

    # Generate .env.example
    env_example_path = Path(".env.example")
    if not env_example_path.exists():
        env_example_path.write_text(get_env_example())
        print(f"[+] Created: .env.example")
    else:
        print(f"[~] Skipped: .env.example (already exists)")

    # Generate .env if it doesn't exist
    env_path = Path(".env")
    if not env_path.exists():
        env_example_content = get_env_example()
        # Update with actual dev-home path
        env_content = env_example_content.replace(
            "DEV_HOME_PATH=./dev-home",
            f"DEV_HOME_PATH={dev_home_path}"
        )
        env_path.write_text(env_content)
        print(f"[+] Created: .env (with DEV_HOME_PATH={dev_home_path})")
    else:
        print(f"[~] Skipped: .env (already exists)")

    return project_name


def main():
    """Main entry point."""
    project_type = "generic"
    dev_home_path = "./dev-home"

    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in get_dockerfile_templates().keys():
            project_type = arg
            if len(sys.argv) > 2:
                dev_home_path = sys.argv[2]
        else:
            # Treat as dev-home path if not a known project type
            dev_home_path = arg

    print("[*] Generating Docker configuration files...")
    project_name = generate_files(project_type, dev_home_path)
    print(f"\n[!] Project name: {project_name}")
    print(f"[!] Dev-home path: {dev_home_path}")

    # Check if using shared dev-home
    if dev_home_path.startswith(".."):
        print("[!] Using shared dev-home (multi-project mode)")
    elif Path(dev_home_path).is_absolute():
        print(f"[!] Using custom dev-home path: {dev_home_path}")

    print("[+] Configuration files generated successfully")


if __name__ == "__main__":
    main()
