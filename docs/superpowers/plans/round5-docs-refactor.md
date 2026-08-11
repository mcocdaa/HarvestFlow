# Round 5 批次 4：文档优化与整理 — 实施计划

- 日期：2026-08-10
- 上游 spec：docs/superpowers/specs/2026-08-10-round5-docs-refactor.md（D1-D3）
- 执行方式：Task 1-3 顺序执行，独立提交；纯文档，无测试

## 概述

修正过期文档（hook 清单、架构笔记、CLAUDE.md、插件开发指南），新增架构指南，更新索引。
文档与代码可交叉验证。

## Task 1：D1 一致性修正

- **hook_points.md**：补全 hook 清单（grep 已收集）——
  - after-only 注册参数类 ×10（setting/secrets/database/plugin/session/collector/curator/
    reviewer/exporter 的 {manager}_register_arguments）
  - 生命周期：app_lifespan_start/shutdown、init_app_before/after、create_app_before/after、register_routes
  - 插件侧：collector_manager_parse_before、collector_manager_scan_after、
    secrets_manager_register_arguments、secrets_manager_init_before（openclaw/infisical 注册）
- **architecture_notes.md**：插件示例改为当前真实 plugins.yaml；方法名引用修正
  （load_plugin_registry → _load_registry 等）；过期内容更新或指引至 architecture_guide.md
- **CLAUDE.md**：架构小节补 BaseManager/parsers/common.py
- **plugin_development.md**：补 call_on_load 入口约定与 curators/openclaw 入口待实现提示
- **提交**：`docs: D1 修正 hook 清单/架构笔记/CLAUDE/插件开发指南与代码一致性`

## Task 2：D2 架构指南

- **新增**：docs/project/architecture_guide.md（结构见 spec D2：总览/目录职责/关键抽象约定/
  初始化流程/插件入口约定/依赖方向）
- **提交**：`docs: D2 新增架构指南（分层职责/抽象约定/依赖方向）`

## Task 3：D3 索引更新

- **docs/index.md**、**docs/project/index.md**：增加 architecture_guide.md
- **docs/notes/index.md**：保持或微调描述
- **验证**：所有链接路径存在（grep 检查）；hook 清单与代码 grep 一致
- **提交**：`docs: D3 索引更新（architecture_guide 收录）`
