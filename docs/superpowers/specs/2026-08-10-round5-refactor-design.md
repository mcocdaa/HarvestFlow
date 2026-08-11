# Round 5 代码优化与整理 — 总体设计

- 日期：2026-08-10
- 状态：已批准（用户确认）
- 深度：中等重构（行为零变化，测试全绿）
- 覆盖：文档 / 插件 / 后端 / 前端

## 1. 背景与目标

HarvestFlow 经过多轮迭代（Round 2 优化、Round 3 审查、Round 4 前端审查），功能稳定、测试充分
（后端 100+、前端 66），但存在可观察的结构问题：

- 后端 manager 接口约定靠文档而非代码强制（`register_arguments`/`init` 手写）
- `collector_manager` 内嵌 ~50 行 jsonl 解析，与 openclaw 插件解析逻辑职责不清
- `import_session` 与 `import_all` 存在重复的会话记录构造/错误处理
- `plugin_manager._load_registry` 过长（~130 行），模块名构造重复 3 次
- `hook_manager.run`/`run_sync` 两套几乎相同的执行循环
- API 层每个 router 手写 `{"success": True, ...}` 与 `HTTPException`
- 插件入口 `__init__.py` 的 on_load 样板在多个插件间重复
- 前端 services 缺少统一响应类型，页面 loading/error 模式重复，store 目录为空

**目标**：在不改变任何外部行为（API 响应形状、hook 语义、数据模型、插件协议）的前提下，
提升代码复用性、清晰度与架构的可扩展性/灵活性。

## 2. 批次划分与顺序

四个独立批次，每批独立走 spec → plan → implement 循环，独立分支 + PR，验收通过才进入下一批：

```
批次1 后端  →  批次2 插件  →  批次3 前端  →  批次4 文档
```

顺序理由：后端优化确立抽象与接口约定（影响插件协议边界），插件跟进对齐，
前端最后对接服务契约，文档最后统一收尾。

## 3. 贯穿原则（所有批次）

1. **行为零变化**：不改 API 响应形状、hook 语义、数据模型、插件协议、CLI 参数。
2. **测试先行确认**：引入抽象前先确认既有测试覆盖，新抽象补单测。
3. **验收标准**：`pytest`/`vitest` 全绿、`eslint`/`tsc` 0 error、ruff 通过、CI 通过。
4. **提交纪律**：每个 task 完成即提交，提交信息标注批次与 task 号。
5. **不动项**：`.gstack/`、`dist/`、`node_modules/`；store 空目录在批次 3 删除（F4）。

## 4. 批次 1：后端（backend/）

| # | 优化项 | 方案 |
|---|--------|------|
| B1 | Manager 抽象基类 | `backend/managers/base.py` 新增 `BaseManager`（`register_arguments`/`init` 默认空实现，docstring 约定 hook 包装），5 个业务 manager 继承；core 单例暂不强改 |
| B2 | 会话解析职责拆分 | 新增 `backend/core/parsers.py`：`parse_jsonl_file(path)`、`parse_json_file(path)`；`collector_manager.parse_session_file` 改为委托调用（jsonl 分支短路逻辑保留） |
| B3 | import 重复逻辑 | `collector_manager` 提取 `_build_session_record(file_path, data)` 与 `_create_session(record)`，`import_session`/`import_all` 共用 |
| B4 | plugin_manager 瘦身 | 提取 `_module_name(key)`、`_read_yaml(path)`、`_read_manifest(path)`；`_load_registry` 拆分 `_load_entry(key, cfg)` |
| B5 | hook_manager 去重 | 提取 `_dispatch(hook_name, args, kwargs, *, allow_async)` 共享执行循环，`run`/`run_sync` 调用之 |
| B6 | API 统一辅助 | 新增 `backend/api/v1/common.py`：`ok(data=None)`、`not_found(detail)`、`conflict(detail)` 辅助；各 router 改用，响应形状完全不变 |
| B7 | main.py 整理 | 常量分组（APP/CORE/BUSINESS/LOG）、lifespan 分解 `_log_startup`/`_shutdown` 私有函数 |
| B8 | 补测试 | BaseManager 接口、parsers 单元、common 辅助、plugin_manager 新方法（module_name/yaml 读取） |

**风险控制**：单例实例化方式不变（`xxx_manager = XxxManager()` 保留，测试直接 import 单例不受影响）；
先锁 API 响应形状测试再改 router 实现。

## 5. 批次 2：插件（plugins/）

| # | 优化项 | 方案 |
|---|--------|------|
| P1 | 入口样板统一 | 新增 `plugins/common.py`：`load_plugin(module_path, log_prefix)`（内部 on_load try/except 模式）；openclaw/infisical/examples 的 `__init__.py` 统一使用 |
| P2 | 结构对齐 | 真实插件与示例插件统一 backend.py/hooks.py/plugin.yaml 三件套约定；`plugins.yaml` 注释补充各插件类型说明 |
| P3 | 补测试 | 插件加载流程、`plugins.common` 辅助 |

**约束**：不改 hooks 语义、不改 plugin.yaml 字段结构、保持插件可独立于 backend 部署的约定
（插件仅依赖 `core.*` 已有方式）。

## 6. 批次 3：前端（frontend/src/）

| # | 优化项 | 方案 |
|---|--------|------|
| F1 | services 统一类型 | 新增 `types/api.ts`：`ApiResponse<T>`、分页响应、`ErrorDetail`；5 个 API 文件统一返回类型，移除 `as any` 滥用 |
| F2 | 数据加载 hook | 新增 `hooks/useAsyncData.ts`：loading/error/data + 重试，Dashboard/Sessions/Review/Plugins 收敛 |
| F3 | 快捷键 hook 整理 | `useKeyboardShortcut` 内联判断提取 `isEditableTarget` 常量/工具，类型收紧 |
| F4 | 类型/目录整理 | `types/` 统一出口；空 store 目录删除（无状态需求，避免空壳） |
| F5 | 补测试 | `useAsyncData`、`isEditableTarget`、统一类型编译验证 |

**约束**：不改 API 契约（前端消费的字段名不变）；antd 版本与既有模式保持一致。

## 7. 批次 4：文档（docs/）

| # | 优化项 | 方案 |
|---|--------|------|
| D1 | 一致性修正 | 修正 docs/project/* 与重构后代码不一致的内容（hook 点清单、插件结构、manager 接口描述）；同步 CLAUDE.md |
| D2 | 架构指南 | 新增 `docs/project/architecture_guide.md`：三层+插件架构、目录职责、依赖方向、约定（manager 接口、parser 使用、API 辅助使用、插件开发约定） |
| D3 | 索引更新 | `docs/index.md`、`docs/project/index.md`、AGENTS.md 引用更新 |

**验收**：文档与代码可交叉验证（引用路径真实存在、描述与实现一致），无测试要求。

## 8. 风险与验收总览

| 风险 | 缓解 |
|------|------|
| 基类化影响测试 mock | 保持单例实例化方式；基类只收敛接口不改变初始化流程 |
| API 辅助遗漏响应形状 | 先用现有测试锁定形状，再改实现；响应字段逐字比对 |
| jsonl 解析提取改变插件短路语义 | 提取仅限内置 collector 内部委托，openclaw 插件 parse_before 短路不变 |
| 批次间耦合 | 批次 1 完成后即验收再开始批次 2，插件协议文档随批次 4 固化 |

验收标准（每批）：全部测试通过、lint/type 0 error、CI 通过、无未提交变更。
