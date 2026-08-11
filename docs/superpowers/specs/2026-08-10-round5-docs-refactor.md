# Round 5 批次 4：文档优化与整理 — 设计规格

- 日期：2026-08-10
- 状态：待用户审阅
- 上游设计：docs/superpowers/specs/2026-08-10-round5-refactor-design.md（第 7 节）
- 类型：纯文档，无代码/测试要求

## 1. 背景与目标

docs/ 结构完整（rules/project/notes/superpowers），但存在与代码事实不符的内容：

1. **docs/notes/architecture_notes.md 严重过期**：引用不存在的插件（rating/knowflow_openclaw）、
   不存在的接口名（`load_plugin_registry`/`register_secrets`/`setup_settings`/`initialize`），
   与当前实现（`_load_registry`/init、plugins.yaml 的 collectors/openclaw 等）不符
2. **docs/project/hook_points.md**：部分 hook 点缺失（after-only 注册参数类、生命周期类、
   app_lifespan_start/shutdown、register_routes 等）
3. **CLAUDE.md**：架构描述未反映 Round 5 批次 1 的重构（BaseManager、core/parsers、
   api/v1/common.py）
4. **docs/project/plugin_development.md / plugin_structure.md**：未反映插件批次改动
   （plugins/common.py 的 call_on_load、入口约定）
5. 缺一份面向新开发者的"架构指南"

**目标**：文档与代码可交叉验证（引用真实、描述一致），新增架构指南，更新索引。

## 2. 范围

### In-scope

- D1 一致性修正：hook_points.md、architecture_notes.md、CLAUDE.md、plugin_development.md
- D2 新增 docs/project/architecture_guide.md
- D3 索引更新：docs/index.md、docs/project/index.md、docs/notes/index.md

### Out-of-scope

- 不改 docs/rules/*（通用规范，与代码无关）
- 不改 docs/superpowers/*（流程产物）
- 不重写全部文档（仅修正过期事实 + 新增架构指南）
- 不改 README.md（前端批次已完成，README 未列入本轮范围；如需同步另行处理）

## 3. 逐项设计

### D1-1 hook_points.md 修正

以代码事实为准（grep 已收集全部 wrap_hooks 与 @hook_manager.hook 名称），补充：
- after-only 注册参数类：`{manager}_register_arguments`（setting/secrets/database/plugin/
  session/collector/curator/reviewer/exporter 各一）
- 生命周期类：`app_lifespan_start`/`app_lifespan_shutdown`、`init_app_before`/`init_app_after`、
  `create_app_before`/`create_app_after`、`register_routes`
- 插件注册类：`collector_manager_parse_before`、`collector_manager_scan_after`、
  `secrets_manager_register_arguments`、`secrets_manager_init_before`（来自 openclaw/infisical 插件）
- 修正/删除与实际不符的条目（如有）

### D1-2 architecture_notes.md 修正

- 更新插件注册表示例为当前真实内容（collectors/openclaw、curators/openclaw、services/infisical）
- 更新方法名引用（`_load_registry` 等）
- 标注历史决策与当前实现的差异（如密钥解析优先级仍适用则保留）
- 若某节内容已由新架构指南覆盖，保留简短指引指向 architecture_guide.md

### D1-3 CLAUDE.md 同步

- 架构小节补充：BaseManager 统一生命周期接口、core/parsers 解析职责、api/v1/common.py 辅助
- 初始化顺序描述保持准确（CORE → BUSINESS managers）

### D1-4 plugin_development.md 同步

- 插件开发流程补充 plugins/common.py call_on_load 用法与入口约定（三件套 + 入口标准）
- 说明 curators/openclaw 入口待实现（避免误导开发者）

### D2 architecture_guide.md（新增）

结构：
1. 总览：三层 + 插件（ASCII 图）
2. 目录职责：backend/core、backend/managers、backend/api、frontend/src 各层职责与依赖方向
3. 关键抽象与约定：
   - BaseManager 生命周期接口（register_arguments/init + hook 包装命名规范）
   - hook 系统语义（before 短路 / after 链式 / run vs run_sync）
   - core/parsers 解析职责边界
   - api/v1/common.py 响应辅助（ok/not_found/bad_request）
   - 前端 services/types/hooks 约定（useAsyncData、ApiResponse 收窄模式）
4. 初始化与启动流程（main.py 顺序）
5. 插件开发入口约定（指向 plugin_development.md 详细版）
6. 依赖方向规则（api → managers → core；插件仅依赖 core.*）

### D3 索引更新

- docs/index.md：项目专用规范区增加 architecture_guide.md
- docs/project/index.md：文件列表增加 architecture_guide.md
- docs/notes/index.md：描述保持（若架构笔记标题含义变化则微调）

## 4. 验收标准

1. 每个文档中的文件引用路径真实存在
2. hook 点清单与代码 grep 结果一致（新增 0 条遗漏）
3. 文档中不再出现不存在的接口/插件名
4. docs/project/index.md 与 docs/index.md 链接完整
5. 无测试要求；提交按 D1-D3 分 task
