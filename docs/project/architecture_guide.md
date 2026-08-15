---
title: 架构指南
description: HarvestFlow 分层架构、目录职责、抽象约定与依赖方向
keywords: [架构, architecture, 分层, 依赖]
version: "1.0"
---

# HarvestFlow 架构指南

> Round 5 批次 4 新增。本文是理解与扩展 HarvestFlow 代码库的入口。

## 1. 总览：三层 + 插件

```
┌─────────────────────────────────────────────────────┐
│  frontend/  (React + TS + antd)                     │
│  services → types → hooks → pages/components        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (REST, /api/v1)
┌──────────────────────▼──────────────────────────────┐
│  backend/api/v1/  (FastAPI 路由层)                  │
│  统一响应辅助: common.ok() / not_found() / bad_request() │
└──────────────────────┬──────────────────────────────┘
┌──────────────────────▼──────────────────────────────┐
│  backend/managers/  (业务层, 继承 BaseManager)      │
│  session / collector / curator / reviewer / exporter │
└──────────────────────┬──────────────────────────────┘
┌──────────────────────▼──────────────────────────────┐
│  backend/core/  (基础设施层, 单例模块)              │
│  setting / secrets / database / hook / plugin / parsers │
└──────────────────────┬──────────────────────────────┘
                       ▲
        plugins/ 通过 Hook 注入（collectors/curators/reviewers/services）
```

依赖方向（单向）：`api → managers → core`；`plugins → core.*`（不反向依赖业务层）。

## 2. 目录职责

### backend/core/（基础设施层）

| 模块 | 职责 | 关键接口 |
|------|------|----------|
| `setting_manager` | 加载 `.env` + 命令行参数 | `get(key)`（key 不区分大小写）、`init(args)`、`register_arguments(parser)` |
| `plugin_manager` | 插件注册表加载与插件导入 | `_load_registry()`、`register_hooks()`、`get_plugin_secrets()`、`set_enabled()` |
| `secrets_manager` | 密钥缓存 + 可插拔客户端 | `init(args, plugin_secrets)`、`set_client_class(cls)` |
| `database_manager` | SQLite 封装（唯一 SQL 层） | `session_get/session_create/...` 具名方法 |
| `hook_manager` | 钩子系统 | `hook()`、`wrap_hooks()`、`run()`（异步）、`run_sync()`（同步） |
| `parsers` | 会话文件解析 | `parse_jsonl_file(path)`、`parse_json_file(path)` |
| `constants` | 全局枚举与通用常量 | `SessionStatus`/`ExportFormat`（StrEnum）、`MAX_PAGE_SIZE` 等 |

### backend/managers/（业务层）

5 个业务管理器，统一继承 `managers/base.py` 的 `BaseManager`，模块级单例模式：

| 管理器 | 职责 |
|--------|------|
| `collector_manager` | 扫描文件夹、解析文件（委托 `core.parsers`）、导入会话 |
| `session_manager` | 会话生命周期代理、状态流转校验、统计 |
| `curator_manager` | 自动评分（1-5）、提取 tags/tools、状态 raw → curated |
| `reviewer_manager` | 人工 approve/reject、批量操作、审计日志 |
| `exporter_manager` | 导出 approved 会话为 ShareGPT/Alpaca |

生命周期接口（所有 manager 一致）：
```python
def register_arguments(self, parser: argparse.ArgumentParser): ...  # 注册 CLI 参数
def init(self, args: argparse.Namespace): ...                        # 初始化
```
hook 包装命名规范：`{manager}_{method}_before/after`（如 `collector_manager_parse_before`）。

### backend/api/v1/（路由层）

- `router_loader.py` 自动扫描目录中的 `router` 对象并挂载，前缀 `/api`
- 每个模块只调用对应 Manager，不直接操作 DB
- 响应统一辅助（`api/v1/common.py`）：
  - `ok(**data)` → `{"success": true, ...}`
  - `not_found(detail)` / `bad_request(detail)` → 404/400 HTTPException
- 路由注册顺序：`register_routers(app)` → `hook_manager.run_sync("register_routes", app)`

### frontend/src/（前端）

| 目录 | 职责 |
|------|------|
| `services/` | axios 实例（`client.ts` 含 Bearer 头与错误拦截器）+ 各 API 封装 |
| `types/` | 领域类型 + `api.ts`（ApiResponse/ListResponse/ErrorDetail 统一包装） |
| `hooks/` | `useAsyncData`（通用加载）、`useKeyboardShortcut` |
| `utils/` | `dom.ts`（isEditableTarget）、`score.ts`、`status.ts`、`string.ts`、`clipboard.ts` |
| `pages/` | 路由页面；`components/` 业务组件；`layouts/` 布局 |

## 3. 关键抽象与约定

### Hook 语义（v2）

- **before**：签名与被包装方法一致（实例方法含 self）。返回非 None 时短路
  （跳过原方法，该值作为方法结果返回）
- **after**：签名 `(result, *被包装方法参数)`。返回非 None 时替换 result，
  多个钩子按 priority 升序链式传递
- `run()` 异步执行（await 异步钩子）；`run_sync()` 同步执行（跳过异步钩子并警告）
- 完整 hook 清单见 `hook_points.md`

### 会话解析职责边界

- 内置解析统一在 `core/parsers.py`（jsonl 逐行 / json 兜底 + session_id 生成）
- `collector_manager.parse_session_file` 仅做格式分派
- 插件可通过 `collector_manager_parse_before` 短路内置解析（如 openclaw）

### 前端数据加载约定

- 页面数据加载统一 `useAsyncData<T>(fetcher, deps)`（内置竞态保护，fetcher 内联安全）
- API 响应收窄模式：`(res.data.plugins as Plugin[] | undefined) ?? []`，
  避免硬断言 `as Plugin[]`

## 4. 初始化与启动流程

```
main()
 ├─ plugin_manager.register_hooks()        # 导入插件 __init__，注册钩子
 ├─ register_all_arguments(parser)         # 核心 + 业务 manager 逐个注册参数
 ├─ init_app(args)                         # 包 init_app_before/after 钩子
 │   ├─ setting_manager.init
 │   ├─ plugin_manager.init
 │   ├─ secrets_manager.init(args, plugin_secrets)
 │   ├─ database_manager.init
 │   └─ BUSINESS_MANAGERS 逐个 init
 ├─ create_app()                           # 包 create_app_before/after 钩子
 │   ├─ CORS 中间件（allow_credentials 与 * 互斥处理）
 │   ├─ register_routers(app)              # 自动扫描 api/v1
 │   └─ hook_manager.run_sync("register_routes", app)
 └─ uvicorn.run(host/port/log_level)
```

lifespan：启动时 `hook_manager.run("app_lifespan_start", app)`；
关闭时 `_shutdown(app)`（`app_lifespan_shutdown` 钩子 + 关闭数据库连接）。

## 5. 插件开发入口

插件 = `plugins/{type}/{name}/` 目录，三件套：`plugin.yaml`（清单）、`hooks.py`（钩子注册）、
`backend.py`（实现），入口 `__init__.py`：

```python
from plugins.{path}.hooks import *          # 注册钩子（必选）
from plugins.{path}.backend import on_load  # 初始化入口（可选）
from plugins.common import call_on_load

call_on_load(on_load, "[{Name}]")
```

详细开发指南见 `plugin_development.md`；结构说明见 `plugin_structure.md`。

> `plugins/curators/openclaw/` 已接入：`curator_manager_evaluate_before` 短路钩子
> 接管自动审核评分（参考 `plugin_development.md`「短路钩子」小节）。

## 6. 依赖方向规则（红线）

1. `api → managers → core`，禁止反向
2. 所有 SQL 只在 `database_manager`，外部禁止 raw SQL
3. 所有配置访问走 `setting_manager.get(key)`，禁止散落的默认值（main/setting 除外）
4. 插件只依赖 `core.*` 与 `plugins/common.py`，不依赖业务层实现
5. 每个 Manager 是模块级单例，通过 `from managers.xxx import xxx_manager` 导入
6. 路由层不写业务逻辑，只做参数解析与响应包装
