# Docker Claude Code - Auxiliary Scripts

Helper scripts for the `docker-claude-code` skill.

## Location

```
.claude/skills/docker-claude-code/
├── SKILL.md                    # Main skill documentation
├── scripts/                    # Auxiliary scripts
│   ├── detect-platform.sh       # Platform detection
│   ├── validate-config.sh       # Configuration validation
│   ├── diagnose-docker.sh       # Container diagnostics
│   └── init-docker-project.sh  # Project initialization
└── README.md                   # This file
```

## Available Scripts

### 1. detect-platform.sh

**Purpose:** Detect current platform and provide recommended configuration.

**Usage:**
```bash
cd .claude/skills/docker-claude-code
bash scripts/detect-platform.sh
```

**Output:**
- Platform detection table (macOS/Linux/Windows)
- Docker Desktop compatibility info
- Recommended ANTHROPIC_BASE_URL configuration
- Platform-specific action items
- Exports `DETECTED_PLATFORM` variable

**Example Output:**
```
========================================
Docker Claude Code - Platform Detection
========================================

Detected Platform: macOS

Platform Configuration:
┌───────────────────────────────────────────────────────────────────┐
│ Platform        │ Docker Desktop   │ host.docker.internal │ Extra Action    │
├─────────────────┼─────────────────┼─────────────────────┼─────────────────┤
│ macOS          │ Docker Desktop   │ host.docker.internal │ None           │
└───────────────────────────────────────────────────────────────────┘

Recommended ANTHROPIC_BASE_URL:
ANTHROPIC_BASE_URL=http://host.docker.internal:15721
(Default configuration works natively)
```

### 2. validate-config.sh

**Purpose:** Validate Docker configuration files and platform compatibility.

**Usage:**
```bash
cd .claude/skills/docker-claude-code
bash scripts/validate-config.sh
```

**Checks:**
- ✓ .env file exists
- ✓ docker-compose.yml exists
- ✓ Dockerfile exists
- ✓ ANTHROPIC_API_KEY is set
- ✓ ANTHROPIC_BASE_URL is configured
- ✓ host.docker.internal usage (platform-specific)
- ✓ stdin_open and tty are set
- ✓ Volume mounts are configured
- ✓ User permissions (multi-user support)

**Exit Codes:**
- `0` - All checks passed or warnings only
- `1` - Errors found (must fix)

### 3. diagnose-docker.sh

**Purpose:** Diagnose Docker environment issues using troubleshooting decision tree.

**Usage:**
```bash
cd .claude/skills/docker-claude-code
bash scripts/diagnose-docker.sh
```

**Diagnostic Flow:**
```
Container not working?
│
├─→ API connection fails? → Check ANTHROPIC_BASE_URL
├─→ Permission denied? → Switch to root user
├─→ Can't find host? → Verify platform-specific config
└─→ Config not persisting? → Check volume mounts
```

**Checks Performed:**
1. Docker daemon status
2. Container status (running/stopped/existing)
3. Environment variables (API_KEY, BASE_URL)
4. API proxy connectivity (from within container)
5. Volume mounts (workspace mounted?)
6. File permissions (write test)
7. Claude CLI installation

**Quick Fixes Provided:**
- Restart container: `docker-compose restart`
- Rebuild image: `docker-compose build && docker-compose up -d`
- View logs: `docker-compose logs -f`
- Enter as root: `docker-compose exec -u root app bash`

### 4. init-docker-project.sh

**Purpose:** Initialize new or migrate existing projects to Docker environment.

**Usage:**
```bash
cd .claude/skills/docker-claude-code
bash scripts/init-docker-project.sh
```

**Interactive Menu:**
```
Select initialization scenario:
1) New Project (create fresh Docker environment)
2) Migrate Existing Project (copy existing code to Docker)
3) Exit
```

**What It Creates:**
- Directory structure (workspace/project/)
- Configuration files (.env, docker-compose.yml, Dockerfile)
- .gitignore with proper exclusions
- Platform-aware configuration (adds extra_hosts for Linux)

**Scenarios:**

**Scenario A: New Project**
```bash
Enter project name [docker-claude-code]: my-project
# Creates fresh environment ready for development
```

**Scenario B: Migrate Existing Project**
```bash
Enter path to existing project: /path/to/existing/project
Enter new Docker project name [docker-claude-code]: my-docker-project
# Copies existing code to workspace/project/
# Creates Docker configuration for migration
```

## Typical Workflow

### For New Projects

```bash
# 1. Initialize project
cd .claude/skills/docker-claude-code
bash scripts/init-docker-project.sh
# Select: 1) New Project

# 2. Review and customize .env
vim .env  # or your preferred editor

# 3. Start container
docker-compose up -d

# 4. Validate configuration (optional)
bash scripts/validate-config.sh

# 5. Enter container and start working
docker-compose exec app sh
claude "Help me create a Node.js Express application"
```

### For Existing Projects

```bash
# 1. Initialize project
cd .claude/skills/docker-claude-code
bash scripts/init-docker-project.sh
# Select: 2) Migrate Existing Project

# 2. Start container
docker-compose up -d

# 3. Validate setup (optional)
bash scripts/validate-config.sh

# 4. Diagnose any issues (if needed)
bash scripts/diagnose-docker.sh

# 5. Enter container and continue development
docker-compose exec app sh
claude "Continue developing this project"
```

## Integration with Main Skill

These scripts are designed to work with the parent `docker-claude-code` skill:

1. **Platform Detection**: Run `detect-platform.sh` before setup to understand platform requirements
2. **Validation**: Use `validate-config.sh` after creating/modifying configuration files
3. **Diagnostics**: Run `diagnose-docker.sh` when troubleshooting issues
4. **Initialization**: Use `init-docker-project.sh` for quick project scaffolding

## Notes

- All scripts require Bash (GNU Bash or compatible)
- Scripts are designed for cross-platform compatibility (Windows/macOS/Linux)
- Run from within the skill directory for correct relative paths
- Scripts export environment variables for downstream use
- Exit codes follow standard conventions (0=success, 1=error)

## Related Documentation

- [SKILL.md](../SKILL.md) - Main skill documentation
- [Chinese Tutorial](../../../docs/docker-claude-code.md) - Detailed setup guide
