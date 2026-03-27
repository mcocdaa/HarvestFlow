---
title: Docker 部署规范
description: 前后端分离应用的 Docker 容器化规范
keywords: [docker, compose, secrets, 前后端分离, 部署规范]
version: "2.0"
---

# Docker 部署规范

> 适用于前后端分离应用的 Docker 容器化部署标准

## 1. 项目结构规范

```
project-root/
├── docker/                      # Docker 配置文件目录
│   ├── docker-compose.base.yml  # 基础服务定义
│   ├── docker-compose.backend.yml
│   ├── docker-compose.frontend.yml
│   └── docker-compose.full.yml
├── backend/
│   └── Dockerfile               # 后端 Dockerfile
├── frontend/
│   └── Dockerfile               # 前端 Dockerfile
├── scripts/                     # 启动/停止脚本
│   ├── start.sh
│   └── stop.sh
├── .env                         # 非敏感环境变量（不提交到 Git）
├── .env.example                 # 环境变量模板（提交到 Git）
└── secrets/                     # Docker Secrets 目录（不提交到 Git）
    ├── db_password.txt
    └── api_key.txt
```

## 2. Docker Compose 分层架构

采用分层 Compose 设计，支持灵活部署：

| 配置文件 | 用途 | 继承关系 |
|---------|------|---------|
| `docker-compose.base.yml` | 通用网络、卷定义 | 基础层 |
| `docker-compose.backend.yml` | 后端服务 | 继承 base |
| `docker-compose.frontend.yml` | 前端服务 | 继承 base |
| `docker-compose.full.yml` | 完整部署 | 继承 base + backend + frontend |

### 2.1 基础文件示例

```yaml
# docker-compose.base.yml
version: "3.8"

networks:
  app-network:
    driver: bridge

volumes:
  app-data:
    driver: local
```

### 2.2 服务配置示例

```yaml
# docker-compose.backend.yml
version: "3.8"

services:
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    ports:
      - "${BACKEND_PORT:-3000}:3000"
    environment:
      - NODE_ENV=${NODE_ENV:-production}
      - DATABASE_URL_FILE=/run/secrets/db_url
    secrets:
      - db_url
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

secrets:
  db_url:
    file: ../secrets/db_url.txt
```

## 3. 环境变量管理规范

### 3.1 分层管理原则

| 层级 | 存储位置 | 内容 | 敏感数据 |
|-----|---------|------|---------|
| 构建时 | Dockerfile ARG | 构建参数 | ❌ 禁止 |
| 运行时公开 | `.env` 文件 | 端口、日志级别等 | ❌ 禁止 |
| 运行时敏感 | Docker Secrets | 密码、密钥、Token | ✅ 必须 |

### 3.2 .env 文件规范

```bash
# ============================================
# 环境配置（非敏感）
# 复制 .env.example 为 .env 后修改
# ============================================

# 运行环境
NODE_ENV=production

# 服务端口（主机:容器）
BACKEND_PORT=3000
FRONTEND_PORT=8080

# 应用配置
LOG_LEVEL=info
API_VERSION=v1

# 数据目录
DATA_DIR=./data
```

**规则：**
- ✅ `.env.example` 提交到 Git（作为模板）
- ❌ `.env` 不提交到 Git（已在 .gitignore 中）
- ❌ 禁止在 `.env` 中存储密码、密钥等敏感信息

### 3.3 Docker Secrets 规范

敏感数据通过 Docker Secrets 注入：

```yaml
# docker-compose.yml
services:
  backend:
    secrets:
      - db_password
      - jwt_secret
    environment:
      # 通过 _FILE 后缀读取 secret 文件路径
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - JWT_SECRET_FILE=/run/secrets/jwt_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

**应用层读取示例（Node.js）：**

```javascript
// 从文件读取 secret
const fs = require('fs');

function getSecret(envName) {
  const filePath = process.env[`${envName}_FILE`];
  if (filePath && fs.existsSync(filePath)) {
    return fs.readFileSync(filePath, 'utf8').trim();
  }
  // 降级：直接从 env 读取（开发环境）
  return process.env[envName];
}

const dbPassword = getSecret('DB_PASSWORD');
```

**规则：**
- ✅ Secrets 文件存放在 `secrets/` 目录
- ❌ `secrets/` 目录不提交到 Git
- ✅ 生产环境使用 Docker Swarm Secrets 或外部 Secret 管理工具
- ✅ 应用代码支持 `_FILE` 后缀读取模式

## 4. 启动脚本规范

### 4.1 脚本位置

所有 Docker 相关的启动脚本统一放在 `scripts/` 目录：

```
scripts/
├── start.sh    # 启动服务
├── stop.sh     # 停止服务
└── init.sh     # 初始化（可选）
```

### 4.2 start.sh 规范

```bash
#!/bin/bash
# ============================================
# Docker 服务启动脚本
# 用法: ./start.sh [mode] [service]
#   mode:    dev | prod | test
#   service: backend | frontend | full
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

# 加载 .env
load_env() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    fi
}

# 检查 secrets 是否存在
check_secrets() {
    local secrets_dir="$PROJECT_ROOT/secrets"
    if [ ! -d "$secrets_dir" ]; then
        echo "❌ secrets/ 目录不存在"
        exit 1
    fi

    # 检查必需的秘密文件
    local required_secrets=("db_password" "jwt_secret")
    for secret in "${required_secrets[@]}"; do
        if [ ! -f "$secrets_dir/${secret}.txt" ]; then
            echo "⚠️  警告: ${secret}.txt 不存在"
        fi
    done
}

# 主逻辑
main() {
    local mode="${1:-dev}"
    local service="${2:-full}"

    load_env

    echo "========================================"
    echo "启动 Docker 服务"
    echo "========================================"
    echo "模式: $mode"
    echo "服务: $service"

    cd "$DOCKER_DIR"

    case "$mode" in
        dev)
            docker compose -f docker-compose.base.yml \
                          -f "docker-compose.${service}.yml" \
                          up --build -d
            ;;
        prod)
            check_secrets
            docker compose -f docker-compose.base.yml \
                          -f "docker-compose.${service}.yml" \
                          -f docker-compose.prod.yml \
                          up -d
            ;;
        *)
            echo "❌ 未知模式: $mode"
            exit 1
            ;;
    esac

    echo "✅ 服务已启动"
}

main "$@"
```

### 4.3 stop.sh 规范

```bash
#!/bin/bash
# ============================================
# Docker 服务停止脚本
# 用法: ./stop.sh [mode]
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

echo "========================================"
echo "停止 Docker 服务"
echo "========================================"

cd "$DOCKER_DIR"

docker compose -f docker-compose.base.yml \
               -f docker-compose.backend.yml \
               -f docker-compose.frontend.yml \
               down

echo "✅ 服务已停止"
```

### 4.4 脚本使用规范

| 命令 | 说明 |
|-----|------|
| `./scripts/start.sh dev backend` | 开发模式启动后端 |
| `./scripts/start.sh dev frontend` | 开发模式启动前端 |
| `./scripts/start.sh dev full` | 开发模式启动全部 |
| `./scripts/start.sh prod full` | 生产模式启动 |
| `./scripts/stop.sh` | 停止所有服务 |

## 5. Dockerfile 规范

### 5.1 后端 Dockerfile 示例

```dockerfile
# 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# 运行阶段
FROM node:20-alpine
WORKDIR /app

# 安全：使用非 root 用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --chown=nodejs:nodejs package.json ./

USER nodejs
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node healthcheck.js || exit 1

CMD ["node", "dist/main.js"]
```

### 5.2 前端 Dockerfile 示例

```dockerfile
# 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段（Nginx）
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 5.3 Dockerfile 规则

- ✅ 使用多阶段构建减小镜像体积
- ✅ 使用特定版本标签（禁止 `latest`）
- ✅ 使用非 root 用户运行
- ✅ 添加健康检查
- ❌ 禁止在 Dockerfile 中硬编码密钥
- ❌ 禁止将敏感数据作为 ARG 传入

## 6. 端口与网络规范

### 6.1 端口分配

| 服务 | 容器内端口 | 默认外部端口 | 配置项 |
|-----|-----------|-------------|-------|
| 后端 | 3000 | 3000 | `BACKEND_PORT` |
| 前端 | 80 | 8080 | `FRONTEND_PORT` |
| 数据库 | 5432 | 5432 | `DB_PORT` |

### 6.2 网络配置

```yaml
networks:
  frontend-network:
    driver: bridge
  backend-network:
    driver: bridge
    internal: true  # 不暴露到外部
```

## 7. 数据卷规范

```yaml
volumes:
  # 持久化数据
  - app-data:/app/data

  # 日志目录
  - ./logs:/app/logs

  # 配置文件（只读）
  - ./config:/app/config:ro
```

## 8. 安全规范

1. **密钥管理**
   - 所有敏感数据必须通过 Docker Secrets 注入
   - 应用代码通过 `_FILE` 环境变量读取
   - 支持本地开发时直接读取环境变量（降级方案）

2. **镜像安全**
   - 使用官方基础镜像
   - 定期更新基础镜像
   - 运行时使用非 root 用户

3. **网络安全**
   - 使用独立网络隔离服务
   - 数据库等内部服务不暴露端口
   - 生产环境启用 TLS

4. **Git 安全**
   ```gitignore
   # .gitignore
   .env
   secrets/
   *.key
   *.pem
   ```

## 9. 快速开始模板

### 9.1 初始化项目

```bash
# 1. 复制环境模板
cp .env.example .env

# 2. 创建 secrets 目录
mkdir -p secrets

# 3. 创建必需的秘密文件
echo "your-db-password" > secrets/db_password.txt
echo "your-jwt-secret" > secrets/jwt_secret.txt

# 4. 启动服务
./scripts/start.sh dev full
```

### 9.2 目录结构检查清单

- [ ] `docker/` 目录包含所有 compose 文件
- [ ] `scripts/` 目录包含 start.sh 和 stop.sh
- [ ] `.env.example` 已提交到 Git
- [ ] `.env` 在 `.gitignore` 中
- [ ] `secrets/` 在 `.gitignore` 中
- [ ] 应用代码支持 `_FILE` 后缀读取 secrets

## 10. 故障排查

| 问题 | 解决方案 |
|-----|---------|
| 端口被占用 | 修改 `.env` 中的端口配置 |
| 权限不足 | 检查 secrets 文件权限 `chmod 600 secrets/*` |
| 服务启动失败 | 查看日志 `docker compose logs -f [service]` |
| 密钥读取失败 | 确认 secret 文件存在且应用支持 `_FILE` 模式 |
