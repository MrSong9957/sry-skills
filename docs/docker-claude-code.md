# docker-claude-code SKILL 技能

## 目标
使用 Docker 创建一个可持久化、可实时同步的开发环境，使宿主机与容器之间的文件保持实时更新，并确保 Claude Code CLI 与状态栏插件在容器中可用。

---

## 验收标准

本项目必须完全符合以下标准：

### 双向同步
- ✅ 宿主机修改代码 → 容器立刻可见
- ✅ 容器内修改文件 → 宿主机立刻同步
- 实现：通过 Docker volume 挂载项目根目录

### 持久化
- ✅ 数据存储在宿主机 `Docker/workspace/.claude/`
- ✅ 删除容器：数据不丢失
- ✅ 重启容器：自动从宿主机同步最新数据
- ❌ 数据不应存储在容器内部

### Claude Code 版本
- ✅ 容器内安装最新版本 Claude Code CLI
- ✅ 使用 `claude doctor` 命令验证

### 状态栏插件
- ✅ Claude Code 更新后安装状态栏插件
- ✅ 插件源码位置：`.claude/skills/docker-claude-code/claude-code-statusline-plugin/`
- ✅ 使用 `init-docker-project.sh` 脚本自动安装

### Python 环境
- ✅ 容器内预装 Python 3
- ✅ 可执行 `python3` 命令
- ✅ 用于运行状态栏插件

### 配置文件隔离
- ✅ 容器配置持久化到：`Docker/workspace/.claude/`（项目目录下）
- ✅ 宿主机配置位置：`C:\Users\<用户>\.claude/` (Windows) 或 `~/.claude/` (Unix)（用户目录）
- ✅ 两者完全独立，互不干扰

### 目录结构
- ✅ 项目根目录只保留一个 `Docker/` 文件夹
- ✅ 所有容器相关文件集中管理

---

## 核心原则

1. 持久化优先
   - `.claude` 配置必须持久化
   - 容器内的工作区必须持久化

2. 挂载项目根目录
   - 宿主机项目根目录挂载到容器内，即可实现实时同步
   - 不需要额外同步工具

3. 结构简洁
   - 项目根目录只保留一个 `Docker/` 文件夹
   - 所有容器相关文件集中管理

4. 容器内开发无权限问题
   - 非 root 用户必须能正常开发
   - root 用户仅用于维护操作

5. Claude Code CLI + 状态栏插件 + Python 必须可用
   - 容器内安装最新版 Claude Code
   - 使用 `claude doctor` 验证
   - 安装 SKILL 目录下的 `claude-code-statusline-plugin` 状态栏插件
   - 容器内预装 Python 3 用于运行插件

6. 配置文件隔离
   - 容器配置存储在 `Docker/workspace/.claude/`
   - 与宿主机的 `~/.claude/` 完全独立
   - 互不干扰，独立管理

---

## 目录结构要求

```
project-root/                              # 项目根目录
  Docker/                                  # 唯一的容器相关文件夹
    Dockerfile
    docker-compose.yml
    .env
    workspace/
      .claude/                             # 容器 Claude 配置持久化（与宿主机隔离）
  .claude/                                 # 宿主机 Claude 配置（独立，与容器隔离）
    skills/
      docker-claude-code/                  # SKILL 定义
        SKILL.md
        README.md
        docs/
        scripts/
          init-docker-project.sh
          test-docker.sh
          diagnose-docker.sh
        claude-code-statusline-plugin/     # 状态栏插件
          .claude-plugin/
            plugin.json
          install.sh                       # Linux/macOS 安装脚本
          install.ps1                      # Windows 安装脚本
          statusline/
            show-prompt.py                 # 插件主程序
```

**关键点：**
- 项目根目录只保留一个 `Docker/` 文件夹
- 容器配置存储在 `Docker/workspace/.claude/`
- 宿主机配置存储在项目根目录下的 `.claude/`
- SKILL 脚本和插件源码在项目根目录 `.claude/skills/` 下，不在 `Docker/` 内
- 容器和宿主机配置完全独立，互不干扰

---

## 必要配置

### `.env`
```
ANTHROPIC_API_KEY=dummy
ANTHROPIC_BASE_URL=http://host.docker.internal:15721
```

---

## docker-compose.yml（核心：挂载 + 持久化）

```yaml
name: docker-claude-code

services:
  app:
    build: .
    container_name: docker-app
    ports:
      - "8080:8000"
    environment:
      - ENV=development
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ANTHROPIC_BASE_URL=http://host.docker.internal:15721
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      # 项目根目录实时同步
      - ..:/workspace/project
      # Claude 配置持久化（与宿主机隔离）
      - ./workspace/.claude:/workspace/.claude
    working_dir: /workspace/project
    stdin_open: true
    tty: true
    restart: unless-stopped
```

**关键配置说明：**
- `..:/workspace/project` - 项目根目录双向同步
- `./workspace/.claude:/workspace/.claude` - 容器配置持久化到宿主机 Docker 目录

---

## 进入容器

| 用户 | 命令 |
|------|------|
| 非 root 用户 | `docker-compose exec app sh` |
| root 用户 | `docker-compose exec --user root app sh` |

要求：
- 非 root 用户必须能完成所有开发任务，无权限问题

---

## Claude Code 安装要求

### 安装最新版 Claude Code CLI
- 在容器内执行安装
- 使用 `claude doctor` 验证版本是否为最新

```bash
# 在容器内执行
npm install -g @anthropic-ai/claude-code
claude doctor
```

---

## 状态栏插件安装

### 插件位置
```
.claude/skills/docker-claude-code/claude-code-statusline-plugin/
├── .claude-plugin/
│   └── plugin.json
├── install.sh          # Linux/macOS 安装脚本
├── install.ps1         # Windows 安装脚本
└── statusline/
    └── show-prompt.py  # 插件主程序
```

**说明**：插件源码位于项目根目录的 `.claude/skills/` 下，不在 `Docker/` 文件夹内。

### 自动安装（推荐）
运行 `init-docker-project.sh` 脚本时会自动安装插件。

### 手动安装
```bash
# 在容器内执行
cd /workspace/project/.claude/skills/docker-claude-code/claude-code-statusline-plugin
bash install.sh
```

### 验证安装
```bash
# 检查插件是否注册
cat ~/.claude/settings.json | grep statusLine
```

预期输出：
```json
"statusLine": {
  "type": "command",
  "command": "python3 ~/.claude/plugins/custom/show-last-prompt/statusline/show-prompt.py"
}
```

---

## Python 环境配置

### Python 版本
容器基于 `node:20-slim` 镜像，自带 Python 3。

### 验证 Python 可用性
```bash
# 在容器内执行
python3 --version
```

预期输出：`Python 3.x.x`

### 用途
- 运行状态栏插件 `show-prompt.py`
- 执行 Python 相关工具和脚本

---

## 配置文件隔离机制

### 双配置架构

| 配置类型 | 宿主机路径 | 容器内路径 | 用途 |
|---------|-----------|-----------|------|
| 宿主机 Claude 配置 | `C:\Users\sry27\.claude\` (用户目录) | - | 宿主机 Claude Code 使用 |
| 容器 Claude 配置 | `Docker/workspace\.claude\` (项目目录) | `/workspace/.claude/` | 容器内 Claude Code 使用 |

### 数据流向

```
宿主机 Claude Code                容器内 Claude Code
       ↓                                   ↓
C:\Users\sry27\.claude\      Docker/workspace/.claude\
       ↓                                   ↓
   （独立存储）                        （独立存储）
       ↓                                   ↓
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    ↓
            互不干扰，完全隔离
```

### 持久化机制

容器内的 `~/.claude/` 通过 volume 挂载到宿主机的 `Docker/workspace/.claude/`：

```yaml
volumes:
  - ./workspace/.claude:/workspace/.claude
```

### 验证隔离

```bash
# 在宿主机查看容器配置持久化目录
ls Docker/workspace/.claude/

# 在容器内查看（容器内 ~/.claude 挂载自 Docker/workspace/.claude）
docker-compose exec app sh -c "ls ~/.claude/"
```

**说明**：宿主机的 `C:\Users\sry27\.claude\` (用户目录) 和项目的 `Docker/workspace/.claude\` 是两个完全独立的目录。

### 优势
- ✅ 容器和宿主机使用不同的 SKILL、插件和设置
- ✅ 容器配置可独立定制
- ✅ 删除容器不影响宿主机配置
- ✅ 便于测试和调试

---

## 验证测试步骤

### 1. 双向同步测试
```bash
# 宿主机创建文件
echo "test" > test.txt

# 容器内查看
docker-compose exec app sh -c "cat test.txt"
# 预期输出：test

# 容器内修改
docker-compose exec app sh -c "echo 'modified' > test.txt"

# 宿主机查看
cat test.txt
# 预期输出：modified
```

### 2. 持久化测试
```bash
# 容器内创建配置
docker-compose exec app sh -c "echo 'container config' > ~/.claude/test.txt"

# 宿主机查看持久化
cat Docker/workspace/.claude/test.txt
# 预期输出：container config

# 重启容器
docker-compose restart
docker-compose exec app sh -c "cat ~/.claude/test.txt"
# 预期输出：container config（数据未丢失）
```

### 3. Claude Code 版本测试
```bash
docker-compose exec app sh -c "claude doctor"
# 预期输出：显示 Claude Code 版本信息，确认是最新版本
```

### 4. 状态栏插件测试
```bash
docker-compose exec app sh -c "cat ~/.claude/settings.json | grep statusLine"
# 预期输出：statusLine 配置存在
```

### 5. Python 测试
```bash
docker-compose exec app sh -c "python3 --version"
# 预期输出：Python 3.x.x
```

### 6. 配置隔离测试
```bash
# 宿主机配置路径（用户目录，Windows 示例）
# 注意：这是宿主机用户自己的 Claude 配置，与容器无关
dir "C:\Users\sry27\.claude"

# 容器配置持久化路径（项目目录下）
# 注意：这是容器配置持久化到宿主机的位置
dir Docker\workspace\.claude

# 两者内容应该不同，完全独立
```

### 7. 目录结构测试
```bash
# 项目根目录应只有一个 Docker/ 文件夹
ls -la | grep -E '^d.*Docker'

# 确认没有其他容器相关目录（如 workspace/、dev-home/ 在根目录）
ls -la | grep -E 'workspace|dev-home'
# 预期：应该没有输出（或只有 ./Docker/workspace）
```

### 8. 运行完整测试脚本
```bash
cd Docker
bash .claude/skills/docker-claude-code/scripts/test-docker.sh
```
