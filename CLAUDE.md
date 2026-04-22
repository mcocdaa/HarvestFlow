# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HarvestFlow 是一个本地 AI Agent 会话数据采集与审核系统，用于：
1. 采集 Agent 对话文件（.json / .jsonl）
2. 自动审核打分、人工复核
3. 导出为 LoRA 训练格式（ShareGPT / Alpaca）
4. 分析 Agent 工作流改善空间

本体只实现基础功能框架，大部分实际逻辑在插件中实现。

## 启动与开发

```bash
# 安装依赖（在 backend/ 目录下）
cd backend && pip install -r requirements.txt

# 启动后端（从项目根目录运行，使 .env 和 plugins/ 路径正确）
cd /path/to/HarvestFlow
python backend/main.py

# 启动前端
cd frontend && npm install && npm run dev

# 带参数启动（覆盖 .env）
python backend/main.py --port 3001 --log-level DEBUG --watch-folders /path/to/sessions
```

环境配置：复制 `.env.example` 为 `.env` 并填写 `WATCH_FOLDERS`（逗号分隔的会话文件目录）。

## 架构：三层 + 插件

```
Core（基础设施）→ Managers（业务逻辑）→ API v1（HTTP 接口）
                                        ↑
                              plugins/（通过 Hook 注入）
```

### Core 层（`backend/core/`）

5 个单例模块，在 `main.py` 的 `init_app()` 中按顺序初始化：

| 模块 | 职责 |
|------|------|
| `setting_manager` | 加载 `.env` + 命令行参数，统一 `get(key)` 访问（key 自动大写） |
| `plugin_manager` | 读取 `plugins/plugins.yaml`，动态 import 插件的 `__init__.py` |
| `secrets_manager` | 密钥缓存，支持本地模式和可插拔远程 SDK（如 Infisical） |
| `database_manager` | SQLite 封装，所有 SQL 只在此层，外部调用具名方法 |
| `hook_manager` | 前置/后置钩子系统，`run()`（异步）和 `run_sync()`（同步）两套 |

初始化顺序严格：`setting → plugin → secrets → database → business managers`。

### Manager 层（`backend/managers/`）

5 个业务管理器，每个都实现 `register_arguments(parser)` + `init(args)` 接口：

- **collector_manager**：扫描文件夹，解析 `.json`/`.jsonl`，写入 DB
- **session_manager**：会话生命周期代理，也提供 `get_session_content()`
- **curator_manager**：自动评分（1-5分）+ 提取 tags/tools，状态改为 `curated`
- **reviewer_manager**：人工 approve/reject，写 audit_log，状态改为 `approved`/`rejected`
- **exporter_manager**：从 DB 取 `approved` 会话，转换为 ShareGPT/Alpaca，写 JSONL

会话状态流：`raw → curated → approved / rejected`，只有 `approved` 才能导出。

### API 层（`backend/api/v1/`）

`router_loader.py` 自动扫描 `api/v1/` 目录，发现有 `router` 属性的模块并挂载。每个 API 模块只调用对应 Manager，不直接操作 DB。

插件也可通过 `register_routes` hook（`hook_manager.run_sync("register_routes", app)`）注册额外路由。

## 插件系统

插件目录：`plugins/`，注册表：`plugins/plugins.yaml`。

**插件结构**（目录型插件，推荐）：
```
plugins/collectors/my_plugin/
├── plugin.yaml     # 清单：name, type, version, secrets[], config
├── __init__.py     # 入口，在模块级别用 @hook_manager.hook() 注册钩子
└── backend.py      # 可选，具体实现
```

**插件加载流程**：
1. `plugin_manager.register_hooks()` 在 `main()` 最开始调用（argparse 解析前）
2. 动态 `importlib` 导入 `__init__.py`，模块内的 `@hook_manager.hook()` 装饰器立即注册钩子
3. 插件钩子在对应 Manager 方法的 before/after 时机执行

**可用钩子点**（格式：`{manager}_{method}_before/after`）：
- `collector_manager_scan/parse/import/import_all_before/after`
- `curator_manager_evaluate/evaluate_all/mark_as_curated_before/after`
- `reviewer_manager_approve/reject/batch_approve/batch_reject_before/after`
- `exporter_manager_export/get_history_before/after`
- `app_lifespan_start/shutdown`（异步），`register_routes`（同步）

**插件密钥**：在 `plugin.yaml` 的 `secrets[]` 中声明，`secrets_manager` 会自动加载并提供缓存访问。

**可插拔密钥客户端**：在 `secrets_manager_init_before` 钩子中调用 `secrets_manager.set_client_class(MyClient)` 替换默认的本地客户端（参考 `plugins/services/infisical/`）。

## 关键约定

- **所有配置访问**用 `setting_manager.get("KEY")`，key 不区分大小写。
- **所有数据库操作**走 `database_manager` 的具名方法，禁止在外部写 raw SQL。
- **每个 Manager 都是模块级单例**，通过 `from managers.xxx import xxx_manager` 导入。
- **Core 模块间循环引用**：`hook_manager` 和 `setting_manager` 不依赖其他 core 模块；`plugin_manager` 依赖两者；`database_manager` 和 `secrets_manager` 依赖前两者。
- `wrap_hooks` 装饰器是同步/异步自动适配的，同步方法用 `run_sync`（只执行同步钩子），异步方法用 `run`（支持两者）。
