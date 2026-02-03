# Docker Dev-Home + Claude Code 工作流示例

本文档展示如何使用 `docker-dev-home-claude-code` 技能创建带持久化 dev-home 的开发环境。

## 完整工作流

### 1. 创建新项目

```bash
# 创建项目目录
mkdir my-claude-app
cd my-claude-app

# 初始化 Docker + Claude Code 环境(带独立 dev-home)
/docker-dev-home-claude-code claude
```

### 2. 配置 API Key

```bash
# 编辑 .env 文件,添加你的 API Key
# ANTHROPIC_API_KEY=sk-ant-xxxxx...
```

### 3. 启动开发容器

```bash
# 构建并启动容器(已在 setup 中自动执行)
docker-compose up -d

# 查看容器日志
docker-compose logs -f
```

### 4. 进入容器并使用 Claude Code

```bash
# 进入容器
docker-compose exec app sh

# 在容器内启动 Claude Code
claude

# 或直接在宿主机执行
docker-compose exec app claude
```

## Dev-Home 配置说明

### 默认模式: 项目独立 Dev-Home

每个项目拥有独立的 dev-home 目录:

```bash
cd ~/projects/project-a
/docker-dev-home-claude-code python

# 生成结构:
# project-a/
# ├── dev-home/
# │   ├── root/         # 持久化容器 /root
# │   ├── logs/
# │   └── README.md
# ├── Dockerfile
# ├── docker-compose.yml
# └── .env
```

### 共享模式: 多项目共享 Dev-Home

多个项目共享同一个 dev-home 目录:

```bash
# 1. 在父目录创建共享 dev-home
cd ~/PycharmProjects
mkdir dev-home

# 2. 在项目 A 中使用
cd project-a
/docker-dev-home-claude-code python ../dev-home

# 3. 在项目 B 中使用
cd ../project-b
/docker-dev-home-claude-code node ../dev-home

# 目录结构:
# PycharmProjects/
# ├── dev-home/         # 共享的 dev-home
# │   ├── root/
# │   ├── logs/
# │   └── README.md
# ├── project-a/
# │   ├── Dockerfile
# │   ├── docker-compose.yml  # DEV_HOME_PATH=../dev-home
# │   └── .env
# └── project-b/
#     ├── Dockerfile
#     ├── docker-compose.yml  # DEV_HOME_PATH=../dev-home
#     └── .env
```

### 自定义路径: 使用绝对路径

```bash
mkdir my-custom-project
cd my-custom-project

# 使用绝对路径
/docker-dev-home-claude-code go /opt/shared/dev-home

# 或在 .env 中配置
# DEV_HOME_PATH=/opt/shared/dev-home
```

### 修改 Dev-Home 路径

在项目创建后修改 dev-home 路径:

```bash
# 编辑 .env 文件
vim .env

# 修改 DEV_HOME_PATH
# DEV_HOME_PATH=/new/path/to/dev-home

# 重启容器
docker-compose down
docker-compose up -d
```

## Dev-Home 管理命令

### 查看持久化状态

```bash
# 检查 dev-home 目录内容
ls -la dev-home/root/

# 检查磁盘使用情况
du -sh dev-home/
du -sh dev-home/root/*

# Windows PowerShell
Get-ChildItem -Recurse dev-home/root | Measure-Object -Property Length -Sum
```

### 备份 Dev-Home

```bash
# 创建时间戳备份
tar -czf dev-home-backup-$(date +%Y%m%d-%H%M%S).tar.gz dev-home/

# 使用 rsync 备份(Linux/Mac)
rsync -av dev-home/ /path/to/backup/dev-home/

# Windows PowerShell
Compress-Archive -Path dev-home -DestinationPath dev-home-backup.zip
```

### 恢复 Dev-Home

```bash
# 解压备份
tar -xzf dev-home-backup-YYYYMMDD-HHMMSS.tar.gz

# 使用 rsync 恢复
rsync -av /path/to/backup/dev-home/ dev-home/

# Windows PowerShell
Expand-Archive -Path dev-home-backup.zip -DestinationPath .
```

### 清理 Dev-Home

```bash
# 清理缓存(安全,不会影响配置)
rm -rf dev-home/root/.cache/*

# 清理日志(安全)
rm -rf dev-home/logs/*

# 清理临时文件
rm -rf dev-home/root/.local/share/claude-code/tmp/*

# 清理所有数据(会重置 Claude Code 状态)
rm -rf dev-home/root/*
```

**警告**: 删除 `dev-home/root/.config/` 会重置所有 Claude Code 配置。

### 监控 Dev-Home 大小

```bash
# 查看总大小
du -sh dev-home/

# 查看各子目录大小
du -sh dev-home/root/* | sort -hr

# 查看最大的文件
find dev-home/root/ -type f -exec du -h {} + | sort -hr | head -20
```

## 多项目工作流示例

### 微服务项目共享配置

```bash
# 1. 创建共享 dev-home
cd ~/microservices
mkdir dev-home

# 2. 创建用户服务
cd user-service
/docker-dev-home-claude-code node ../dev-home
cat > package.json << EOF
{
  "name": "user-service",
  "version": "1.0.0",
  "main": "server.js"
}
EOF

# 3. 创建订单服务
cd ../order-service
/docker-dev-home-claude-code node ../dev-home
cat > package.json << EOF
{
  "name": "order-service",
  "version": "1.0.0",
  "main": "server.js"
}
EOF

# 4. 两个服务共享 Claude Code 认证状态和配置
# 只需要在一个服务中配置一次 API Key
```

### Monorepo 项目

```bash
# Monorepo 结构
my-monorepo/
├── dev-home/           # 共享 dev-home
├── packages/
│   ├── frontend/
│   │   └── .env        # DEV_HOME_PATH=../../dev-home
│   ├── backend/
│   │   └── .env        # DEV_HOME_PATH=../../dev-home
│   └── shared/
└── docker-compose.yml

# 初始化 monorepo
cd my-monorepo
/docker-dev-home-claude-code generic ./dev-home

# 在子包中创建相对的 .env 配置
```

### 相关项目共享认证状态

```bash
# 实验项目和主项目共享认证
cd ~/projects
mkdir dev-home

# 主项目
cd main-project
/docker-dev-home-claude-code python ../dev-home

# 实验项目
cd ../experiment-project
/docker-dev-home-claude-code python ../dev-home

# 两个项目共享 Claude Code 的登录状态和 API 配置
```

## 迁移指南

### 从旧版 Named Volumes 迁移

如果你之前使用 `docker-claude-setup`(使用 named volumes):

#### 1. 备份现有数据

```bash
# 查看现有 volumes
docker volume ls | grep claude

# 备份 claude-config volume
docker run --rm \
  -v claude-config:/data \
  -v $(pwd):/backup \
  alpine tar -czf /backup/claude-config-backup.tar.gz -C /data .

# 备份 claude-cache volume
docker run --rm \
  -v claude-cache:/data \
  -v $(pwd):/backup \
  alpine tar -czf /backup/claude-cache-backup.tar.gz -C /data .
```

#### 2. 停止并移除旧容器

```bash
cd old-project
docker-compose down
```

#### 3. 运行新技能生成配置

```bash
# 使用新技能
/docker-dev-home-claude-code [project-type]

# 或手动创建 dev-home 目录
mkdir -p dev-home/root/.config
mkdir -p dev-home/root/.cache
```

#### 4. 恢复数据到 dev-home

```bash
# 恢复配置
mkdir -p dev-home/root/.config
tar -xzf claude-config-backup.tar.gz -C dev-home/root/.config/

# 恢复缓存
mkdir -p dev-home/root/.cache
tar -xzf claude-cache-backup.tar.gz -C dev-home/root/.cache/

# 调整权限(Linux/Mac)
sudo chown -R $USER:$USER dev-home/root/
```

#### 5. 启动新容器

```bash
docker-compose up -d

# 验证数据迁移成功
docker-compose exec app claude --version
```

#### 6. 清理旧 Volumes(可选)

```bash
# 确认新容器正常工作后删除旧 volumes
docker volume rm claude-config claude-cache
```

### 从其他开发环境迁移

从本地开发环境迁移到 Docker dev-home:

```bash
# 1. 导出现有 Claude Code 配置
# 在本地环境运行
claude config export > claude-config-backup.json

# 2. 创建 Docker 项目
/docker-dev-home-claude-code claude

# 3. 导入配置
docker-compose exec app claude config import < claude-config-backup.json
```

## 不同项目类型示例

### Python + Claude Code

```bash
mkdir my-python-service
cd my-python-service

# 初始化 Python 环境
/docker-dev-home-claude-code python

# 创建 requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
EOF

# 重新构建容器
docker-compose up -d --build
```

### Node.js + Claude Code

```bash
mkdir my-node-api
cd my-node-api

# 初始化 Node.js 环境
/docker-dev-home-claude-code node

# 创建 package.json
cat > package.json << EOF
{
  "name": "my-node-api",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "node server.js"
  }
}
EOF

# 重新构建容器
docker-compose up -d --build
```

### Go + Claude Code

```bash
mkdir my-go-service
cd my-go-service

# 初始化 Go 环境
/docker-dev-home-claude-code go

# 初始化 Go module
docker-compose exec app go mod init my-go-service

# 创建 main.go
cat > main.go << EOF
package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
}
EOF
```

## 常用操作

### 容器管理

```bash
# 查看容器状态
docker-compose ps

# 停止容器
docker-compose stop

# 启动容器
docker-compose start

# 重启容器
docker-compose restart

# 完全移除容器
docker-compose down
```

### 日志查看

```bash
# 查看所有日志
docker-compose logs

# 实时跟踪日志
docker-compose logs -f

# 查看特定服务的日志
docker-compose logs -f app
```

### 资源监控

```bash
# 查看容器资源使用
docker stats

# 进入容器 Shell
docker-compose exec app sh

# 在容器中执行命令
docker-compose exec app ls -la
docker-compose exec app node --version
docker-compose exec app python --version
```

## 完整开发工作流

### 1. 初始化项目

```bash
mkdir my-claude-project
cd my-claude-project
/docker-dev-home-claude-code claude
```

### 2. 配置环境

```bash
# .env 已自动生成,编辑添加 API Key
vim .env
# ANTHROPIC_API_KEY=sk-ant-xxxxx...
```

### 3. 验证安装

```bash
# 验证脚本会自动在 setup 中运行
# 或手动运行验证
docker-compose exec app claude --version

# 验证 dev-home 挂载
ls -la dev-home/root/
```

### 4. 开始开发

```bash
# 进入容器
docker-compose exec app sh

# 启动 Claude Code 交互模式
claude

# 或直接让 Claude Code 读取项目文件
docker-compose exec app claude read /app
```

### 5. 测试状态持久化

```bash
# 在容器内创建文件
docker-compose exec app sh -c "echo 'test' > /root/.test-file"

# 在宿主机验证文件存在
ls dev-home/root/.test-file

# 重启容器
docker-compose restart

# 验证文件仍然存在
docker-compose exec app cat /root/.test-file
```

## 故障排查

### 容器无法启动

```bash
# 检查日志
docker-compose logs

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### Dev-Home 目录不存在

**错误**: dev-home 目录不存在: ./dev-home/root

**解决**:
```bash
# 重新创建 dev-home 结构
python3 scripts/generate-config.py [project-type] [dev-home-path]

# 或手动创建
mkdir -p dev-home/root/.config
mkdir -p dev-home/root/.cache
mkdir -p dev-home/root/.local
```

### 数据未持久化

**检查**:
```bash
# 1. 确认 .env 文件中 DEV_HOME_PATH 设置正确
cat .env | grep DEV_HOME_PATH

# 2. 验证 docker-compose.yml volumes 部分包含 dev-home 挂载
cat docker-compose.yml | grep -A 5 volumes:

# 3. 检查挂载是否生效
docker-compose exec app df -h | grep root

# 4. 重启容器
docker-compose restart
```

### 文件权限问题(Linux/Mac)

**现象**: 宿主机上无法编辑 `dev-home/root/` 中的文件

**原因**: 容器以 root 用户运行,创建的文件属于 root

**解决**:
```bash
# 获取文件所有权
sudo chown -R $USER:$USER dev-home/root/

# 或使用特定用户/组
sudo chown -R 1000:1000 dev-home/root/

# 避免权限问题: 在容器内编辑文件
docker-compose exec app vim /root/config.json
```

### 磁盘空间不足

**检查**:
```bash
# 查看 dev-home 大小
du -sh dev-home/

# 查看最大目录
du -sh dev-home/root/* | sort -hr

# 查看 Docker 总磁盘使用
docker system df
```

**解决**:
```bash
# 清理缓存
rm -rf dev-home/root/.cache/*

# 清理日志
rm -rf dev-home/logs/*

# 清理 Docker 未使用的资源
docker system prune -a
```

### Claude Code CLI 无法访问

```bash
# 检查 CLI 是否安装
docker-compose exec app which claude

# 检查 Node.js 是否安装
docker-compose exec app node --version

# 手动安装 CLI
docker-compose exec app npm install -g @anthropic-ai/claude-code
```

### API Key 未生效

```bash
# 检查环境变量
docker-compose exec app printenv ANTHROPIC_API_KEY

# 确保 .env 文件在正确位置
ls -la .env

# 重启容器使环境变量生效
docker-compose restart
```

## 生产部署

### 更新 Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

# 安装 Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# 安装依赖
COPY package*.json ./
RUN npm ci --only=production

# 复制应用文件
COPY . .

# 生产模式启动
CMD ["node", "server.js"]
```

### 更新 docker-compose.yml

```yaml
services:
  app:
    build: .
    container_name: myapp-prod
    ports:
      - "80:8080"
    environment:
      - NODE_ENV=production
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - .:/app
      - ${DEV_HOME_PATH:-./dev-home}/root:/root
    restart: always
```

### 部署

```bash
# 构建生产镜像
docker-compose build

# 启动生产容器
docker-compose up -d

# 健康检查
curl http://localhost:8080/health
```

## 高级用法

### 多容器应用

```yaml
# docker-compose.yml
services:
  app:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgres://db:5432/myapp
    volumes:
      - .:/app
      - ${DEV_HOME_PATH:-./dev-home}/root:/root
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=secret
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

### 开发工具集成

```dockerfile
# 在 Dockerfile 中添加开发工具
RUN apk add --no-cache \
    git \
    vim \
    curl \
    htop \
    strace \
    tcpdump
```

### 自定义 Dev-Home 挂载选项

```yaml
# docker-compose.yml
services:
  app:
    volumes:
      # 只读挂载(防止意外修改)
      - ${DEV_HOME_PATH:-./dev-home}/config:/root/.config/claude:ro

      # 读写挂载
      - ${DEV_HOME_PATH:-./dev-home}/root:/root

      # 使用命名卷作为中间层
      - dev-home-data:/root
```

## 最佳实践

### 1. 定期备份 Dev-Home

```bash
# 创建定时备份脚本
cat > backup-dev-home.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
tar -czf "$BACKUP_DIR/dev-home-$TIMESTAMP.tar.gz" dev-home/

# 保留最近 7 天的备份
find "$BACKUP_DIR" -name "dev-home-*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup-dev-home.sh

# 添加到 crontab(Linux/Mac)
# 0 2 * * * /path/to/backup-dev-home.sh
```

### 2. 使用 .gitignore 忽略 Dev-Home

```bash
# 项目根目录的 .gitignore
dev-home/

# 或保留 README
dev-home/*
!dev-home/README.md
!dev-home/.gitignore
```

### 3. 文档化 Dev-Home 配置

在项目 README.md 中说明 dev-home 配置:

```markdown
## Dev-Home 配置

本项目使用独立的 dev-home 目录。如需与其他项目共享,请修改 `.env` 文件中的 `DEV_HOME_PATH`:

```bash
# 默认: 项目独立
DEV_HOME_PATH=./dev-home

# 多项目共享
DEV_HOME_PATH=../dev-home
```
```

### 4. 监控 Dev-Home 大小

```bash
# 创建监控脚本
cat > check-dev-home.sh << 'EOF'
#!/bin/bash
SIZE=$(du -sm dev-home/ | cut -f1)
THRESHOLD=1000  # 1GB

if [ $SIZE -gt $THRESHOLD ]; then
    echo "警告: dev-home 大小超过 ${THRESHOLD}MB (当前: ${SIZE}MB)"
    echo "最大目录:"
    du -sh dev-home/root/* | sort -hr | head -5
fi
EOF

chmod +x check-dev-home.sh
```

### 5. 多项目共享时的注意事项

- 避免同时运行多个使用同一 dev-home 的容器
- 定期备份共享 dev-home
- 使用版本控制管理 `.env` 配置(不包含 API Key)
- 在团队中共享 dev-home 路径约定
