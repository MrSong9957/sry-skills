# **Docker-Claude-Code 技能（完整版）**

## **项目概述**

这是一个为 **Claude Code CLI** 设计的 Docker 开发环境。它提供一个**独立、可持久化、极简实用**的容器，您可以在容器内使用 Claude Code CLI 完成整个项目的开发工作。

**核心特点：**
- ✅ 单容器，单卷挂载，结构清晰
- ✅ 支持新建项目和迁移已有项目
- ✅ 内置最新版 Claude Code CLI
- ✅ 配置自动持久化，无需手动管理
- ✅ 支持 root 和非 root 两种权限进入

---

## **1. 项目文件结构**

在您的宿主机上创建以下目录结构：

```
docker-claude-code/
├── .env                    # 环境变量配置
├── docker-compose.yml      # Docker 编排文件
├── Dockerfile              # 容器构建文件
├── workspace/              # 核心工作区（容器内 /workspace）
│   ├── project/            # 项目代码目录
│   └── .claude/            # Claude 配置目录
│       ├── config/         # CLI 配置
│       └── history/        # 会话历史
└── README.md               # 本文件（可选）
```

---

## **2. 配置文件内容**

### **2.1 .env 文件**
```env
# Claude Code CLI Configuration
# dummy 表示沿用宿主机的 API KEY
ANTHROPIC_API_KEY=dummy

# 端口要与 CC Switch 本地代理端口一致
ANTHROPIC_BASE_URL=http://host.docker.internal:15721

# 工作区路径（可选自定义）
# WORKSPACE_PATH=./workspace
```

**说明：**
- `ANTHROPIC_API_KEY`：设置为 `dummy` 时，容器会尝试使用宿主机的环境变量。如果宿主机没有设置，需要替换为真实的 API Key。
- `ANTHROPIC_BASE_URL`：必须与您的 **Claude Code Switch** 本地代理端口一致（默认 15721）。

### **2.1.1 平台注意事项**

| 平台 | `host.docker.internal` 支持 | 额外配置 |
|------|---------------------------|---------|
| **Windows** (Docker Desktop) | ✅ 原生支持 | 无 |
| **macOS** (Docker Desktop) | ✅ 原生支持 | 无 |
| **Linux** | ⚠️ 不原生支持 | 已通过 `extra_hosts` 配置兼容 |

**Linux 用户说明**：
- 文档中的 `docker-compose.yml` 已包含 `extra_hosts: "host.docker.internal:host-gateway"` 配置
- 此配置在 Windows/macOS 上会被自动忽略，不影响使用
- 如果仍无法连接，可使用宿主机 IP 替代：
  ```bash
  # 获取宿主机 IP
  hostname -I | awk '{print $1}'
  # 然后在 .env 中使用
  ANTHROPIC_BASE_URL=http://<宿主机IP>:15721
  ```

### **2.2 docker-compose.yml 文件**
```yaml
services:
  app:
    build: .
    container_name: docker-claude-code-app
    ports:
      # 容器内应用端口映射（如有 Web 服务需要）
      - "8080:8000"
    environment:
      - ENV=development
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}
    extra_hosts:
      # Linux 兼容：使容器能访问宿主机服务
      # Windows/Mac (Docker Desktop) 会自动忽略此配置
      - "host.docker.internal:host-gateway"
    volumes:
      # 核心：单卷挂载，包含项目和配置
      - ${WORKSPACE_PATH:-./workspace}:/workspace
    working_dir: /workspace/project  # 关键：容器启动后直接进入项目目录
    stdin_open: true
    tty: true
    restart: unless-stopped
```

### **2.3 Dockerfile 文件**
```dockerfile
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

# 切换到非 root 用户（安全最佳实践）
USER claude-user

# 暴露端口（根据 docker-compose.yml 调整）
EXPOSE 8000

# 默认启动 shell
CMD ["/bin/sh"]
```

---

## **3. 使用指南**

### **3.1 初始化项目**

#### **场景一：新建项目**
```bash
# 1. 创建项目目录结构
mkdir -p docker-claude-code/workspace/project
cd docker-claude-code

# 2. 启动容器
docker-compose up -d

# 3. 进入容器（默认非 root 用户）
docker-compose exec app sh

# 4. 在容器内，您已经在 /workspace/project 目录
#    可以直接开始使用 Claude Code CLI
claude "帮我创建一个简单的 Node.js Express 应用"
```

#### **场景二：迁移已有项目**
```bash
# 1. 将现有项目复制到 workspace/project
mkdir -p docker-claude-code/workspace/project
cp -r /path/to/your/actual/project/* docker-claude-code/workspace/project/

# 2. 进入项目目录
cd docker-claude-code

# 3. 启动容器
docker-compose up -d

# 4. 进入容器
docker-compose exec app sh

# 5. 在容器内，您已经在 /workspace/project 目录
#    可以继续使用 Claude Code CLI 开发
claude "继续开发这个项目，实现 XX 功能"
```

### **3.2 进入容器的命令**

- **使用非 root 用户（推荐，更安全）**：
  ```bash
  docker-compose exec app sh
  ```
  进入后，您位于 `/workspace/project` 目录。

- **使用 root 用户（需要系统权限时）**：
  ```bash
  docker-compose exec --user root app sh
  ```
  进入后，您位于 `/workspace/project` 目录。

### **3.3 在容器内使用 Claude Code CLI**

1. 进入容器后，您已经在 `/workspace/project` 目录。
2. 直接运行 `claude` 命令：
   ```bash
   claude "帮我分析当前目录结构"
   ```
3. 配置已自动加载（通过环境变量），历史记录保存在 `/workspace/.claude`。

### **3.4 文件管理与持久化**

- **项目代码**：位于 `workspace/project/`，与容器内 `/workspace/project` 实时同步。
  - 在宿主机编辑：使用 VS Code、Vim 等编辑 `workspace/project/` 中的文件。
  - 在容器内编辑：在容器内使用任何编辑器（如 Vim）修改 `/workspace/project` 中的文件。

- **Claude 配置**：位于 `workspace/.claude/`，自动持久化。
  - 容器重启后，配置和历史记录保留。
  - 如需重置，删除 `workspace/.claude/` 目录即可。

### **3.5 停止与清理**

```bash
# 停止容器（保留容器，不删除）
docker-compose stop

# 停止并删除容器（保留数据卷）
docker-compose down

# 停止并删除容器及卷（**谨慎使用**，会删除 workspace 目录！）
docker-compose down -v
```

---

## **4. 目录结构详解**

### **workspace/**
- **project/**：您的项目代码目录。所有开发工作在此进行。
- **.claude/**：Claude Code CLI 的配置和历史记录。
  - `config/`：CLI 配置文件。
  - `history/`：会话历史记录。

### **为什么这样设计？**
1. **单卷但结构清晰**：虽然只有一个挂载卷，但内部通过子目录明确区分项目和配置。
2. **工作目录明确**：`working_dir` 直接指向 `/workspace/project`，进入容器即可开始工作。
3. **配置隔离**：`.claude` 是隐藏目录，不会干扰项目代码。
4. **易于备份/迁移**：整个 `workspace` 目录就是完整的工作环境，复制即迁移。

---

## **5. 常见问题与解决**

### **Q1: Claude Code CLI 无法连接到 API**
**检查：**
1. 确保 `ANTHROPIC_BASE_URL` 端口与宿主机的 Claude Code Switch 代理端口一致。
2. 在容器内检查环境变量：
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $ANTHROPIC_BASE_URL
   ```
3. 如果使用 `dummy`，确保宿主机已设置 `ANTHROPIC_API_KEY` 环境变量。

### **Q2: 文件权限问题**
**解决：**
- 在容器内创建文件时，如果遇到权限问题，可以临时切换到 root：
  ```bash
  docker-compose exec --user root app sh
  chown -R 1001:1001 /workspace/project  # UID 应与 Dockerfile 中的用户一致
  ```
  然后退出，重新以非 root 用户进入。

### **Q3: 如何更新 Claude Code CLI？**
**解决：**
```bash
# 进入容器（root 用户）
docker-compose exec --user root app sh

# 使用官方推荐更新 CLI
claude install

# 退出容器，重启
exit
docker-compose restart
```

### **Q4: 如何扩展容器功能（如安装其他工具）？**
**解决：**
在 `Dockerfile` 中添加安装命令，然后重建镜像：
```bash
# 修改 Dockerfile，添加工具安装
# 例如：RUN apk add --no-cache git curl

# 重建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

---

## **6. 进阶配置**

### **6.1 自定义端口**
如果需要更改 Web 服务端口（例如容器内运行一个 Web 应用）：
1. 修改 `docker-compose.yml` 中的 `ports` 部分。
2. 确保容器内应用监听相应端口。

---

## **7. 最佳实践提示**

1. **版本控制**：在 `workspace/project` 中初始化 Git，跟踪项目代码。
2. **配置管理**：将重要的配置（如数据库连接）放在 `.env` 或环境变量中。
3. **定期备份**：定期备份整个 `workspace` 目录。
4. **清理历史**：定期清理 `workspace/.claude/history/` 中的旧会话文件。
5. **镜像构建**：如果需要在多个机器上使用，考虑将镜像推送到 Docker Registry。

---

## 8. 与 Claude Code 技能集成

### 8.1 技能自动激活

当您在使用 Claude Code CLI 时，`docker-claude-code` 技能会自动激活，如果：

- 您提到需要设置 Docker 环境
- 需要配置 API 代理（如 CC Switch）
- 需要跨平台支持（Windows/macOS/Linux）
- 需要多用户支持（root 和非 root）

### 8.2 Agent 编排

`docker-claude-code` 技能包含智能任务难度评估：

**简单任务**（单文件修改）
- 直接处理，无需启动其他 agent

**中等任务**（多个相关文件）
- 启动 3 个并行子代理：
  1. 配置验证器 - 验证 Docker 文件语法
  2. 平台专家 - 检查平台特定设置
  3. 连接性测试器 - 验证 API 代理连接

**复杂任务**（跨领域关注点）
- 创建 agent 团队：
  - migration-architect - 分析项目结构
  - docker-configurer - 创建 Dockerfile/docker-compose.yml
  - platform-specialist - 处理平台差异
  - test-validator - 验证容器功能

### 8.3 自动技能委托

`docker-claude-code` 技能会自动委托给相关技能：

- **tdd-workflow** → 测试 Docker 环境设置
- **verification-loop** → 验证容器功能
- **security-review** → 部署前审查容器安全
- **backend-patterns** → 设置容器化 API 服务

### 8.4 技能参考

快速参考和诊断流程图请参见：[docker-claude-code 技能](../.claude/skills/docker-claude-code/SKILL.md)

技能文件包含：
- 平台特定配置表格
- 诊断故障排除决策树
- Agent 编排逻辑
- 常见错误模式

---

## 9. 辅助脚本使用指南

### 9.1 脚本目录结构

`docker-claude-code` 技能包含一组辅助脚本，位于技能目录下的 `scripts/` 文件夹：

```
.claude/skills/docker-claude-code/
├── SKILL.md                    # 主要技能文件
├── scripts/                    # 辅助脚本
│   ├── detect-platform.sh       # 平台检测
│   ├── validate-config.sh       # 配置验证
│   ├── diagnose-docker.sh       # 诊断脚本
│   ├── init-docker-project.sh  # 项目初始化
│   └── README.md             # 脚本使用说明
└── ...
```

### 9.2 可用脚本

#### 1. 平台检测脚本 (detect-platform.sh)

**用途**：自动检测当前平台并提供推荐配置

**使用方法**：
```bash
cd .claude/skills/docker-claude-code
bash scripts/detect-platform.sh
```

**输出内容**：
- 平台检测表格（macOS/Linux/Windows）
- Docker Desktop 兼容性信息
- 推荐的 ANTHROPIC_BASE_URL 配置
- 平台特定操作项
- 导出 `DETECTED_PLATFORM` 环境变量供其他脚本使用

#### 2. 配置验证脚本 (validate-config.sh)

**用途**：验证 Docker 配置文件和平台兼容性

**使用方法**：
```bash
cd .claude/skills/docker-claude-code
bash scripts/validate-config.sh
```

**验证项目**：
- ✓ .env 文件存在
- ✓ docker-compose.yml 存在
- ✓ Dockerfile 存在
- ✓ ANTHROPIC_API_KEY 已设置
- ✓ ANTHROPIC_BASE_URL 已配置
- ✓ host.docker.internal 使用（平台特定）
- ✓ stdin_open 和 tty 已设置
- ✓ 卷挂载已配置
- ✓ 用户权限（多用户支持）

**退出代码**：
- `0` - 所有检查通过或仅有警告
- `1` - 发现错误（需要修复）

#### 3. 诊断脚本 (diagnose-docker.sh)

**用途**：使用故障排除决策树诊断 Docker 环境问题

**使用方法**：
```bash
cd .claude/skills/docker-claude-code
bash scripts/diagnose-docker.sh
```

**诊断流程**：
```
容器不工作？
│
├─→ API 连接失败？ → 检查 ANTHROPIC_BASE_URL
├─→ 权限被拒绝？ → 切换到 root 用户
├─→ 找不到主机？ → 验证平台特定配置
└─→ 配置不持久？ → 检查卷挂载
```

**执行检查**：
1. Docker 守护进程状态
2. 容器状态（运行/停止/存在）
3. 环境变量（API_KEY, BASE_URL）
4. API 代理连接性（从容器内测试）
5. 卷挂载（workspace 已挂载？）
6. 文件权限（写入测试）
7. Claude CLI 安装

**提供的快速修复**：
- 重启容器：`docker-compose restart`
- 重建镜像：`docker-compose build && docker-compose up -d`
- 查看日志：`docker-compose logs -f`
- 以 root 身份进入：`docker-compose exec -u root app bash`

#### 4. 项目初始化脚本 (init-docker-project.sh)

**用途**：初始化新项目或将现有项目迁移到 Docker 环境

**使用方法**：
```bash
cd .claude/skills/docker-claude-code
bash scripts/init-docker-project.sh
```

**交互式菜单**：
```
选择初始化场景：
1) 新项目（创建全新的 Docker 环境）
2) 迁移现有项目（复制现有代码到 Docker）
3) 退出
```

**创建内容**：
- 目录结构（workspace/project/）
- 配置文件（.env, docker-compose.yml, Dockerfile）
- .gitignore 文件（包含适当的排除项）
- 平台感知配置（为 Linux 自动添加 extra_hosts）

### 9.3 典型工作流

#### 新建项目

```bash
# 1. 初始化项目
cd .claude/skills/docker-claude-code
bash scripts/init-docker-project.sh
# 选择：1) 新项目

# 2. 查看并自定义 .env
vim .env  # 或您偏好的编辑器

# 3. 启动容器
docker-compose up -d

# 4. 验证配置（可选）
bash scripts/validate-config.sh

# 5. 进入容器并开始工作
docker-compose exec app sh
claude "帮我创建一个 Node.js Express 应用"
```

#### 迁移现有项目

```bash
# 1. 初始化项目
cd .claude/skills/docker-claude-code
bash scripts/init-docker-project.sh
# 选择：2) 迁移现有项目

# 2. 启动容器
docker-compose up -d

# 3. 验证设置（可选）
bash scripts/validate-config.sh

# 4. 诊断任何问题（如需要）
bash scripts/diagnose-docker.sh

# 5. 进入容器并继续开发
docker-compose exec app sh
claude "继续开发这个项目"
```

### 9.4 脚本集成说明

**快速参考**：完整的脚本文档请参见 [scripts/README.md](../.claude/skills/docker-claude-code/scripts/README.md)

**技能集成**：这些脚本设计为与主 `docker-claude-code` 技能协同工作：

1. **平台检测**：在设置前运行 `detect-platform.sh` 以了解平台需求
2. **验证**：在创建/修改配置文件后使用 `validate-config.sh`
3. **诊断**：故障排除时运行 `diagnose-docker.sh`
4. **初始化**：使用 `init-docker-project.sh` 进行快速项目脚手架

---

## 10. 验收标准

### 10.1 完整验收清单

使用 `docker-claude-code` 技能创建容器后，应该满足以下验收标准：

#### ✅ 标准 1：最简单的容器进入命令

**要求**：用户能够使用最简单的命令进入容器

**验证命令**：
```bash
docker-compose exec app sh
```

**预期结果**：
- ✅ 成功进入容器
- ✅ 工作目录为 `/workspace/project`
- ✅ 用户为 `claude-user`（UID 1001）
- ✅ 无任何错误信息

#### ✅ 标准 2：Claude Code 开箱即用

**要求**：容器启动后，Claude Code CLI 立即可用，无需额外配置

**验证命令**：
```bash
# 1. 启动容器
docker-compose up -d

# 2. 进入容器
docker-compose exec app sh

# 3. 测试 Claude CLI
claude --version
```

**预期结果**：
- ✅ Claude Code CLI 已安装
- ✅ 显示版本号（如 `claude-code version x.x.x`）
- ✅ API 代理配置正确（`ANTHROPIC_BASE_URL`）
- ✅ 无配置错误

**附加检查 - 状态栏插件**：
```bash
# 检查插件是否已注册
docker-compose exec app sh -c 'python3 -c "import json; print(json.load(open(\"~/.claude/settings.json\")).get(\"statusLine\", {}))"'
```

**预期结果**：
- ✅ `statusLine` 配置存在
- ✅ 指向 `show-prompt.py` 脚本
- ✅ 状态栏显示：`[最新指令:{summary}]`

#### ✅ 标准 3：容器实现持久化和实时更新

**要求**：容器重启后，配置和代码更改保持持久

**验证项目**：

**3.1 工作空间持久化**：
```bash
# 1. 在容器内创建文件
docker-compose exec app sh -c "echo 'test content' > /workspace/test.txt"

# 2. 重启容器
docker-compose restart

# 3. 检查文件是否仍然存在
docker-compose exec app sh -c "cat /workspace/test.txt"
```

**预期结果**：
- ✅ 输出：`test content`
- ✅ 文件在容器重启后仍然存在

**3.2 Claude 配置持久化**：
```bash
# 1. 设置 Claude 配置
docker-compose exec app sh -c "echo 'test-config' > ~/.claude/config/test.conf"

# 2. 重启容器
docker-compose restart

# 3. 检查配置是否持久
docker-compose exec app sh -c "cat ~/.claude/config/test.conf"
```

**预期结果**：
- ✅ 输出：`test-config`
- ✅ 配置在容器重启后仍然存在

**3.3 实时更新**：
```bash
# 在容器内编辑项目文件
docker-compose exec app sh -c "echo 'updated content' > /workspace/project/readme.md"

# 在宿主机上验证文件已更新
cat workspace/project/readme.md
```

**预期结果**：
- ✅ 宿主机和容器内文件内容同步
- ✅ 修改立即生效

#### ✅ 标准 4：无任何报错

**要求**：整个工作流程中无错误信息

**验证检查清单**：

**4.1 Docker 守护进程状态**：
```bash
docker info
```

**预期结果**：
- ✅ Docker 守护进程正在运行
- ✅ 无错误信息

**4.2 容器启动日志**：
```bash
docker-compose logs app
```

**预期结果**：
- ✅ 无 ERROR 级别日志
- ✅ 无 CRITICAL 级别日志
- ✅ 无异常堆栈跟踪

**4.3 API 连接测试**：
```bash
# 测试 API 代理连接
docker-compose exec app sh -c "curl -s -o /dev/null -w '%{http_code}' $ANTHROPIC_BASE_URL/v1/messages || echo 'failed'"
```

**预期结果**：
- ✅ 返回 `401`（需要认证）或 `200`（成功）
- ❌ 不是 `000`（连接失败）
- ❌ 不是 `ENOTFOUND`（主机未找到）

**4.4 环境变量验证**：
```bash
docker-compose exec app sh -c 'echo "API_KEY: $ANTHROPIC_API_KEY" && echo "BASE_URL: $ANTHROPIC_BASE_URL"'
```

**预期结果**：
- ✅ `ANTHROPIC_API_KEY=dummy`
- ✅ `ANTHROPIC_BASE_URL=http://host.docker.internal:15721`（或平台特定 URL）
- ✅ 无空值

### 10.2 快速验证脚本

运行以下脚本进行自动验证：

```bash
#!/bin/bash
# 快速验证脚本

echo "========================================="
echo "Docker Claude Code - 验收测试"
echo "========================================="
echo ""

PASS=0
FAIL=0

# 测试 1: 容器状态
echo "测试 1: 检查容器状态..."
if docker ps --format '{{.Names}}' | grep -q "docker-claude-code-app"; then
    echo "✓ PASS: 容器正在运行"
    PASS=$((PASS + 1))
else
    echo "✗ FAIL: 容器未运行"
    FAIL=$((FAIL + 1))
fi
echo ""

# 测试 2: 进入容器
echo "测试 2: 测试容器访问..."
if docker-compose exec app sh -c "echo 'container access OK'" >/dev/null 2>&1; then
    echo "✓ PASS: 可以进入容器"
    PASS=$((PASS + 1))
else
    echo "✗ FAIL: 无法进入容器"
    FAIL=$((FAIL + 1))
fi
echo ""

# 测试 3: Claude CLI 版本
echo "测试 3: 检查 Claude CLI..."
VERSION=$(docker-compose exec app claude --version 2>/dev/null || echo "not found")
if [ "$VERSION" != "not found" ]; then
    echo "✓ PASS: Claude CLI 已安装 - $VERSION"
    PASS=$((PASS + 1))
else
    echo "✗ FAIL: Claude CLI 未安装"
    FAIL=$((FAIL + 1))
fi
echo ""

# 测试 4: 环境变量
echo "测试 4: 验证环境变量..."
API_KEY=$(docker-compose exec app sh -c 'echo $ANTHROPIC_API_KEY' 2>/dev/null)
BASE_URL=$(docker-compose exec app sh -c 'echo $ANTHROPIC_BASE_URL' 2>/dev/null)

if [ "$API_KEY" = "dummy" ] && [ -n "$BASE_URL" ]; then
    echo "✓ PASS: 环境变量配置正确"
    echo "  API_KEY: $API_KEY"
    echo "  BASE_URL: $BASE_URL"
    PASS=$((PASS + 1))
else
    echo "✗ FAIL: 环境变量配置错误"
    FAIL=$((FAIL + 1))
fi
echo ""

# 测试 5: 状态栏插件
echo "测试 5: 检查状态栏插件..."
if docker-compose exec app sh -c 'python3 -c "import json; print(json.load(open(\"~/.claude/settings.json\")).get(\"statusLine\", {}) != {})"' >/dev/null 2>&1; then
    echo "✓ PASS: 状态栏插件已注册"
    PASS=$((PASS + 1))
else
    echo "✗ FAIL: 状态栏插件未注册"
    FAIL=$((FAIL + 1))
fi
echo ""

# 测试 6: 文件持久化
echo "测试 6: 测试文件持久化..."
docker-compose exec app sh -c "echo 'persistence-test' > /workspace/.persistence-test" 2>/dev/null
sleep 2
RESULT=$(docker-compose exec app sh -c "cat /workspace/.persistence-test" 2>/dev/null)
if [ "$RESULT" = "persistence-test" ]; then
    echo "✓ PASS: 文件持久化正常"
    PASS=$((PASS + 1))
else
    echo "✗ FAIL: 文件持久化失败"
    FAIL=$((FAIL + 1))
fi
echo ""

# 总结
echo "========================================="
echo "测试结果汇总"
echo "========================================="
echo "通过: $PASS"
echo "失败: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✓ 所有测试通过！"
    exit 0
else
    echo "✗ 有 $FAIL 个测试失败"
    exit 1
fi
```

### 10.3 常见问题排查

| 问题 | 诊断 | 解决方案 |
|------|------|----------|
| 容器无法启动 | Dockerfile 语法错误 | 运行 `docker-compose build` 查看错误 |
| API 连接失败 | `ANTHROPIC_BASE_URL` 配置错误 | 检查 `.env` 文件和平台配置 |
| 文件未持久化 | 卷挂载配置错误 | 检查 `docker-compose.yml` 中的 `volumes:` 部分 |
| 状态栏不显示 | 插件未安装 | 运行 `.claude/plugins/custom/show-last-prompt/statusline/install.sh` |
| 权限被拒绝 | 用户权限问题 | 使用 `docker-compose exec -u root app bash` |

### 10.4 最终确认

所有标准满足后：

1. ✅ 用户可以使用 `docker-compose exec app sh` 进入容器
2. ✅ Claude Code CLI 开箱即用，已注册状态栏插件
3. ✅ 容器实现持久化和实时更新
4. ✅ 无任何报错

**验收通过！** 🎉

---

**相关文档**：
- [SKILL.md](../.claude/skills/docker-claude-code/SKILL.md) - 技能文件
- [scripts/README.md](../.claude/skills/docker-claude-code/scripts/README.md) - 脚本文档
- [ACCEPTANCE_CRITERIA.md](../.claude/skills/docker-claude-code/ACCEPTANCE_CRITERIA.md) - 验收标准
