# HarvestFlow

本地化的 AI Agent 会话数据采集与审核系统：**采集 → 自动审核 → 人工复核 → 导出训练格式**。

[![CI](https://github.com/mcocdaa/HarvestFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/mcocdaa/HarvestFlow/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

- **采集 (Collector)**：扫描/监控目录，导入 JSON / JSONL 会话
- **自动审核 (Curator)**：插件化质量评分，高于阈值自动通过
- **人工审核 (Reviewer)**：可视化复核、批量操作、完整审计日志
- **导出 (Exporter)**：ShareGPT / Alpaca，支持筛选与版本历史
- **插件系统**：Collector / Curator / Reviewer / Service 四类插件，热插拔

## 快速开始（Docker，推荐）

前置：[Docker](https://docs.docker.com/get-docker/)（含 Compose v2）。

```bash
git clone https://github.com/mcocdaa/HarvestFlow.git
cd HarvestFlow
cp .env.example .env          # 可选：修改端口 / 鉴权 / 监控目录
docker compose up -d --build  # 首次构建需要几分钟
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8001 |
| 后端 API 文档 (Swagger) | http://localhost:3001/docs |

使用预构建镜像（跳过本地构建）：

```bash
cp .env.example .env
docker compose pull && docker compose up -d
```

> 预构建镜像发布在 GHCR：`ghcr.io/mcocdaa/harvestflow-backend`、`ghcr.io/mcocdaa/harvestflow-frontend`。
> `main` 分支为 `latest`（linux/amd64），`v*` 标签发布版本号（linux/amd64 + arm64）。

也可以使用一键脚本（等价，会自动创建 `.env`）：

```bash
./scripts/start.sh dev full   # 停止请用 ./scripts/stop.sh dev
```

### 不用 Compose：docker run

```bash
docker network create harvestflow

docker run -d --name harvestflow-backend --network harvestflow \
  -p 3001:3000 \
  -v "$PWD/backend/data:/app/data" \
  -v "$PWD/plugins:/app/plugins:ro" \
  ghcr.io/mcocdaa/harvestflow-backend:latest

docker run -d --name harvestflow-frontend --network harvestflow \
  -p 8001:8000 \
  ghcr.io/mcocdaa/harvestflow-frontend:latest
```

### 修改配置

```bash
vim .env                # 修改端口、鉴权、监控目录等
docker compose up -d    # 让配置生效
```

前端相关变量（`VITE_*`）在构建时注入，修改后需重建：`docker compose up -d --build`。

## 本地开发（源码模式）

前置：[uv](https://docs.astral.sh/uv/)（后端依赖管理）、Node.js 18+（推荐 24）。

```bash
./scripts/start.sh local full      # 后端 :3000 + 前端 :5173
./scripts/start.sh local backend   # 仅后端
./scripts/start.sh local frontend  # 仅前端
./scripts/stop.sh local            # 停止
```

首次启动会自动 `cp .env.example .env`，并按锁文件安装前后端依赖。

## 配置说明

完整配置见 [.env.example](.env.example)，常用项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `BACKEND_EXTERNAL_PORT` / `FRONTEND_EXTERNAL_PORT` | `3001` / `8001` | Docker 对外端口 |
| `PORT` | `3000` | 本地源码模式后端端口 |
| `HARVESTFLOW_API_KEY` / `VITE_API_KEY` | 空 | Bearer 鉴权，留空关闭；设置后需重建前端 |
| `WATCH_FOLDERS` | 空 | 自动采集目录，逗号分隔 |
| `OPENCLAW_AGENTS_DIR` | 空 | OpenClaw 导出数据目录（如 `./backend/data/test_sessions/agents`） |
| `CURATOR_ENABLED` / `AUTO_APPROVE_THRESHOLD` | `true` / `4` | 自动审核开关与自动通过阈值 |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `DATA_DIR` / `DB_PATH` / `PLUGINS_DIR` | `./backend/data` 等 | 本地路径；Docker 内部固定为 `/app/*` |

## API 概览

完整交互式文档：http://localhost:3001/docs

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/PATCH/DELETE | `/api/v1/sessions/{id}` | 会话详情 / 更新 / 删除 |
| GET | `/api/v1/stats` | 统计信息 |
| GET/POST | `/api/v1/collector/scan`、`import`、`import-all` | 采集与导入 |
| GET/POST | `/api/v1/curator/status`、`evaluate/{id}`、`evaluate-all` | 自动审核 |
| GET/POST | `/api/v1/reviewer/pending`、`approve/{id}`、`reject/{id}`、`batch-*` | 人工审核 |
| GET/POST | `/api/v1/exporter/formats`、`export`、`history` | 导出 |
| GET/POST | `/api/v1/plugins`、`enable`、`disable` | 插件管理 |

> 鉴权：设置 `HARVESTFLOW_API_KEY` 后，`/api/*` 需携带 `Authorization: Bearer <key>`；`/health` 不受限制。

## 插件开发

插件接口定义、开发指南与配置说明见 [plugins/README.md](plugins/README.md)；架构与 Hook 机制见 [docs/project/architecture_guide.md](docs/project/architecture_guide.md)。

## 项目结构

```
HarvestFlow/
├── backend/                 # FastAPI + SQLite（uv 管理依赖）
│   ├── api/v1/              # HTTP 路由
│   ├── core/                # 配置/数据库/插件/钩子等基础设施
│   ├── managers/            # 采集/审核/导出等业务逻辑
│   └── tests/               # pytest
├── frontend/                # React + Ant Design + Vite
├── plugins/                 # 采集/审核插件（独立于本体）
├── scripts/                 # start.sh / stop.sh
├── docker-compose.yml       # 单文件编排
└── .env.example             # 配置模板
```

## 许可证

[MIT](LICENSE)
