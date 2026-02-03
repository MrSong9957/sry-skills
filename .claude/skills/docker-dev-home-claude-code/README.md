# Docker Dev-Home + Claude Code

完整的 Docker 容器环境,让 Claude Code CLI 安全可靠地进行全自动开发。

## 为什么需要在容器里使用 Claude Code CLI?

### 宿主机直接使用的风险 ⚠️

```bash
# 在宿主机使用 Claude Code CLI
claude  # 危险!
```

**风险**:
- ❌ **无边界保护** - 可能修改系统文件、删除重要数据
- ❌ **不可逆操作** - `rm -rf`、`git reset --hard` 等操作难以回滚
- ❌ **环境污染** - 全局安装依赖、修改系统配置
- ❌ **难以控制** - 不知道 AI 会对你的系统做什么

### 容器内使用的优势 ✅

```bash
# 在容器内使用 Claude Code CLI
docker-compose exec app claude  # 安全!
```

**优势**:
- ✅ **完全隔离** - 容器是沙盒环境,乱来也不怕
- ✅ **无人值守全自动** - 放心让它运行,不用担心安全性
- ✅ **易于回滚** - 出问题直接 `docker-compose down && docker-compose up`
- ✅ **可预测行为** - 容器内环境完全可控
- ✅ **持久化开发** - dev-home 保留配置和缓存,重建容器也不丢失

**核心价值**: 让 Claude Code CLI 成为真正可信的全自动开发助手,而不是风险敞口。

## 快速开始

```bash
# 创建项目并初始化环境
mkdir my-project && cd my-project
/docker-dev-home-claude-code python

# 配置 API Key
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env

# 启动容器并进入开发
docker-compose up -d
docker-compose exec app sh
claude  # 安全的全自动开发
```

## 技能为你创建了什么

### 文件结构

```
your-project/
├── dev-home/                    # 持久化目录(核心特性)
│   ├── root/                    # 容器 /root 的映射
│   │   ├── .config/             # Claude Code 配置
│   │   ├── .cache/              # 缓存数据
│   │   └── .ssh/                # SSH 密钥
│   └── README.md
│
├── Dockerfile                   # 容器镜像定义
├── docker-compose.yml           # 容器编排配置
├── .dockerignore
├── .env.example
├── .env                         # API Key 配置
│
└── your-code/                   # 你的项目代码
```

### 容器配置

| 配置项 | 值 |
|--------|-----|
| 工作目录 | `/app` (挂载到项目根目录) |
| 默认用户 | `root` |
| 端口映射 | `8080:8080` |

### 已安装软件

| 项目类型 | 基础镜像 | 运行时 |
|---------|---------|--------|
| `python` | python:3.11-slim | Python 3.11 + Node.js 20 |
| `node` | node:20-alpine | Node.js 20 |
| `go` | golang:1.21-alpine | Go 1.21 + Node.js 20 |
| `java` | eclipse-temurin:21-jre-alpine | Java 21 + Node.js 20 |

**所有镜像包含**: Claude Code CLI, git, curl, bash, vim

### 卷挂载

```yaml
volumes:
  - .:/app                           # 项目代码实时同步
  - /app/node_modules                # 依赖保护
  - ./dev-home/root:/root            # Dev-home 持久化(核心)
  - ./dev-home/config:/root/.config/claude  # Claude 配置
```

### Dev-Home 持久化

**持久化内容**:
- Claude Code 配置和状态
- npm、pip、Go modules 缓存
- SSH 密钥、Git 配置

**数据验证**:
```bash
# 容器内创建文件
docker-compose exec app sh -c "echo 'test' > /root/.test"
# 宿主机查看
cat dev-home/root/.test
# 重启后仍在
docker-compose restart && docker-compose exec app cat /root/.test
```

## 实际开发需要做什么

### 必需配置

#### 1. 配置 API Key

```bash
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
docker-compose restart
docker-compose exec app printenv ANTHROPIC_API_KEY
```

获取密钥: https://console.anthropic.com/

#### 2. 安装项目依赖

```bash
# Python
docker-compose exec app pip install fastapi uvicorn

# Node.js
docker-compose exec app npm install express axios

# Go
docker-compose exec app go get github.com/gin-gonic/gin
```

### 推荐配置

#### 3. 配置端口映射

```yaml
ports:
  - "8080:8080"      # 前端
  - "3000:3000"      # 后端
```

#### 4. 配置热重载

```bash
# Node.js
docker-compose exec app npm install --save-dev nodemon
docker-compose exec app npm run dev

# Python
docker-compose exec app uvicorn main:app --reload --host 0.0.0.0
```

## 使用示例

### 安全的全自动开发

```bash
# 进入容器
docker-compose exec app sh

# 让 Claude Code 全自动开发
claude
# > 分析项目并优化性能
# > 添加单元测试
# > 重构代码结构
# > 即使操作有误,容器隔离也保证宿主机安全
```

### 多项目共享 dev-home

```bash
# 创建共享 dev-home
mkdir ~/dev-home

# 项目 A
cd frontend
/docker-dev-home-claude-code node ~/dev-home

# 项目 B
cd ../backend
/docker-dev-home-claude-code python ~/dev-home

# 共享 Claude Code 配置和缓存
```

### 团队协作

```bash
# 项目经理
git add Dockerfile docker-compose.yml .env.example
git commit -m "Add Docker configuration"

# 团队成员
git clone https://github.com/org/project.git
cd project
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
docker-compose up -d
```

## 常见问题

### 容器启动失败?

```bash
docker-compose logs
docker-compose build --no-cache
docker-compose up -d
```

### API Key 未生效?

```bash
docker-compose exec app printenv ANTHROPIC_API_KEY
# 检查 .env 文件格式(无空格、无引号)
```

### 代码更改不生效?

```bash
docker-compose exec app ls -la /app
docker-compose restart
```

## 相关资源

- [Claude Code CLI 文档](https://docs.anthropic.com/claude-code)
- [Docker 官方文档](https://docs.docker.com/)
- [examples/workflow.md](./examples/workflow.md)

## 许可证

MIT License
