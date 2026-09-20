# HarvestFlow — Notes for Coding Agents

本文件面向在 HarvestFlow 仓库中工作的 AI Coding Agent。用户文档见 [README.md](README.md)，架构与规范文档见 [docs/](docs/)。

## 1. Read First (必读指引)

1. 阅读 [通用规范文档](docs/rules/index.md)（包含代码规范、API 规范、文档规范与 Docker 规范）与 [docs/project/](docs/project/)。
2. HarvestFlow 核心是**本地化 Agent 会话数据采集与审核**：状态机严格保证 `raw → curated → approved/rejected` 状态闭环流转，所有人工修改必须写审计日志。
3. 服务端插件系统（Collector / Curator / Reviewer / Service）具备 before/after 钩子机制，修改打分算法或数据格式需保证插件兼容性。

## 2. Repository Rules & Constraints (核心契约与安全规则)

- **本地优先**：FastAPI + SQLite + 本地持久化文件，不引入对不可控外部云服务的硬依赖。
- **依赖管理**：后端依赖统一通过 `uv` 管理（单一数据源 `backend/pyproject.toml`，锁文件 `backend/uv.lock`）。
- **敏感信息隔离**：不要提交 `.env`、`data/`、SQLite 数据库文件或真实抓取的敏感会话数据。
- **统一脚本**：使用 `scripts/start.sh`（支持 `local` 源码模式与 `dev` Docker Compose 模式）和 `scripts/stop.sh` 控制服务生命周期。

## 3. Essential Commands (核心研发命令)

```bash
# 后端 (uv 管理)
cd backend
uv run pytest -v                       # 运行后端单元测试
uv run ruff check .                    # 代码规范检查

# 前端 (React 19 + Ant Design 5)
cd ../frontend
npm test                               # Vitest 单元测试
npm run lint                           # ESLint 检查
npm run build                          # 前端生产构建

# 启动与运行
cd ..
./scripts/start.sh local full          # 本地源码启动全部服务
./scripts/start.sh dev full            # Docker Compose 模式启动
```

## 4. Verification Checklist (提交前自检)

- [ ] 后端 uv run pytest 全量通过
- [ ] 前端 npm run lint & npm run build 全绿
- [ ] 修改涉及数据模型时，确认状态机跃迁与审计日志落盘无破坏
- [ ] `git status` 确认未跟踪新增临时会话或数据文件
