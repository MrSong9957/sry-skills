# Docker Claude Code 技能 - 验收标准

## 概述

本文档定义了 `docker-claude-code` 技能的完整验收标准，确保用户能够开箱即用 Claude Code CLI 在 Docker 容器中。

---

## 验收标准

### ✅ 标准 1：最简单的容器进入命令

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

**失败条件**：
- ❌ 容器未运行
- ❌ 权限被拒绝
- ❌ 工作目录不正确

---

### ✅ 标准 2：Claude Code 开箱即用

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
- ✅ API 代理配置正确（ANTHROPIC_BASE_URL）
- ✅ 无配置错误

**附加检查 - 状态栏插件**：
```bash
# 检查插件是否已注册
cat ~/.claude/settings.json | grep -A 3 "statusLine"
```

**预期结果**：
- ✅ `statusLine` 配置存在
- ✅ 指向 `show-prompt.py` 脚本
- ✅ 状态栏显示：`[最新指令:{summary}]`

---

### ✅ 标准 3：容器实现持久化和实时更新

**要求**：容器重启后，配置和代码更改保持持久

**验证项目**：

#### 3.1 工作空间持久化
```bash
# 1. 在容器内创建文件
docker-compose exec app sh -c "echo 'test content' > /workspace/test.txt"

# 2. 重启容器
docker-compose restart

# 3. 等待容器重启完成
sleep 5

# 4. 检查文件是否仍然存在
docker-compose exec app sh -c "cat /workspace/test.txt"
```

**预期结果**：
- ✅ 输出：`test content`
- ✅ 文件在容器重启后仍然存在

#### 3.2 Claude 配置持久化
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

#### 3.3 实时更新
```bash
# 在容器内编辑项目文件
docker-compose exec app sh -c "echo 'updated content' > /workspace/project/readme.md"

# 在宿主机上验证文件已更新
cat workspace/project/readme.md
```

**预期结果**：
- ✅ 宿主机和容器内文件内容同步
- ✅ 修改立即生效

---

### ✅ 标准 4：无任何报错

**要求**：整个工作流程中无错误信息

**验证检查清单**：

#### 4.1 Docker 守护进程状态
```bash
docker info
```

**预期结果**：
- ✅ Docker 守护进程正在运行
- ✅ 无错误信息

#### 4.2 容器启动日志
```bash
docker-compose logs app
```

**预期结果**：
- ✅ 无 ERROR 级别日志
- ✅ 无 CRITICAL 级别日志
- ✅ 无异常堆栈跟踪

#### 4.3 API 连接测试
```bash
# 测试 API 代理连接
docker-compose exec app sh -c "curl -s -o /dev/null -w '%{http_code}' $ANTHROPIC_BASE_URL/v1/messages || echo 'failed'"
```

**预期结果**：
- ✅ 返回 `401`（需要认证）或 `200`（成功）
- ❌ 不是 `000`（连接失败）
- ❌ 不是 `ENOTFOUND`（主机未找到）

#### 4.4 环境变量验证
```bash
docker-compose exec app sh -c 'echo "API_KEY: $ANTHROPIC_API_KEY" && echo "BASE_URL: $ANTHROPIC_BASE_URL"'
```

**预期结果**：
- ✅ `ANTHROPIC_API_KEY=dummy`
- ✅ `ANTHROPIC_BASE_URL=http://host.docker.internal:15721`（或平台特定 URL）
- ✅ 无空值

---

## 快速验证脚本

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

---

## 常见问题排查

| 问题 | 诊断 | 解决方案 |
|------|------|----------|
| 容器无法启动 | Dockerfile 语法错误 | 运行 `docker-compose build` 查看错误 |
| API 连接失败 | ANTHROPIC_BASE_URL 配置错误 | 检查 `.env` 文件和平台配置 |
| 文件未持久化 | 卷挂载配置错误 | 检查 `docker-compose.yml` 中的 `volumes:` 部分 |
| 状态栏不显示 | 插件未安装 | 运行 `.claude/plugins/custom/show-last-prompt/statusline/install.sh` |
| 权限被拒绝 | 用户权限问题 | 使用 `docker-compose exec -u root app bash` |

---

## 最终确认

所有标准满足后：

1. ✅ 用户可以使用 `docker-compose exec app sh` 进入容器
2. ✅ Claude Code CLI 开箱即用，已注册状态栏插件
3. ✅ 容器实现持久化和实时更新
4. ✅ 无任何报错

**验收通过！** 🎉
