---
title: 内置Hook点
description: 系统内置Hook点列表
keywords: [hook, 钩子点, 内置]
version: "2.0"
---

# 内置 Hook 点列表

> 以下清单由代码中的 `@hook_manager.wrap_hooks(...)` 与 `@hook_manager.hook(...)`
> 自动生成式核对（Round 5 批次 4 校准）。

## 应用生命周期（backend/main.py）

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `init_app_before` / `init_app_after` | 应用初始化前后 | 包住 `init_app()`（manager 初始化） |
| `create_app_before` / `create_app_after` | 应用创建前后 | 包住 `create_app()`（FastAPI 实例） |
| `app_lifespan_start` | 启动时 | FastAPI lifespan 启动段（`hook_manager.run`） |
| `app_lifespan_shutdown` | 关闭时 | FastAPI lifespan 关闭段（`hook_manager.run`） |
| `register_routes` | 路由注册后 | `hook_manager.run_sync` 调用（供插件追加路由） |

## 核心层（backend/core/）

### Setting Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `setting_manager_construct_before` / `setting_manager_construct_after` | 构造前后 | 设置管理器实例化前后 |
| `setting_manager_init_before` / `setting_manager_init_after` | 初始化前后 | 设置管理器初始化前后 |
| `setting_manager_register_arguments` | 参数注册后（after-only） | 追加 argparse 参数 |

### Secrets Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `secrets_manager_construct_before` / `secrets_manager_construct_after` | 构造前后 | 密钥管理器实例化前后 |
| `secrets_manager_init_before` / `secrets_manager_init_after` | 初始化前后 | 密钥管理器初始化前后 |
| `secrets_manager_register_arguments` | 参数注册后（after-only） | 追加密钥相关参数（Infisical 插件注册于此） |

### Database Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `database_manager_construct_before` / `database_manager_construct_after` | 构造前后 | 数据库管理器实例化前后 |
| `database_manager_initialize_before` / `database_manager_initialize_after` | 初始化前后 | 数据库初始化前后 |
| `database_manager_register_arguments` | 参数注册后（after-only） | 追加数据库参数 |

### Plugin Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `plugin_manager_construct_before` / `plugin_manager_construct_after` | 构造前后 | 插件管理器实例化前后 |
| `plugin_manager_init_before` / `plugin_manager_init_after` | 初始化前后 | 插件管理器初始化前后 |
| `plugin_manager_register_arguments` | 参数注册后（after-only） | 追加插件参数 |

## 业务层（backend/managers/）

### Session Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `session_manager_construct_before` / `session_manager_construct_after` | 构造前后 | 会话管理器实例化前后 |
| `session_manager_init_before` / `session_manager_init_after` | 初始化前后 | 初始化前后 |
| `session_manager_register_arguments` | 参数注册后（after-only） | 追加会话参数 |
| `session_manager_create_before` / `session_manager_create_after` | 创建前后 | 创建会话 |
| `session_manager_get_before` / `session_manager_get_after` | 获取前后 | 获取会话 |
| `session_manager_list_before` / `session_manager_list_after` | 列表前后 | 会话列表查询 |
| `session_manager_update_before` / `session_manager_update_after` | 更新前后 | 更新会话（含状态流转校验） |
| `session_manager_delete_before` / `session_manager_delete_after` | 删除前后 | 删除会话 |
| `session_manager_content_get_before` / `session_manager_content_get_after` | 内容获取前后 | 获取会话内容 |
| `session_manager_stats_get_before` / `session_manager_stats_get_after` | 统计前后 | 获取统计信息 |

### Collector Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `collector_manager_construct_before` / `collector_manager_construct_after` | 构造前后 | 采集管理器实例化前后 |
| `collector_manager_init_before` / `collector_manager_init_after` | 初始化前后 | 初始化前后 |
| `collector_manager_register_arguments` | 参数注册后（after-only） | 追加采集参数 |
| `collector_manager_scan_before` / `collector_manager_scan_after` | 扫描前后 | 扫描文件夹 |
| `collector_manager_parse_before` / `collector_manager_parse_after` | 解析前后 | 解析会话文件（openclaw 插件短路于此） |
| `collector_manager_import_before` / `collector_manager_import_after` | 导入前后 | 导入单个会话 |
| `collector_manager_import_all_before` / `collector_manager_import_all_after` | 批量导入前后 | 导入全部会话 |

### Curator Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `curator_manager_construct_before` / `curator_manager_construct_after` | 构造前后 | 审核器管理器实例化前后 |
| `curator_manager_init_before` / `curator_manager_init_after` | 初始化前后 | 初始化前后 |
| `curator_manager_register_arguments` | 参数注册后（after-only） | 追加审核参数 |
| `curator_manager_evaluate_before` / `curator_manager_evaluate_after` | 评估前后 | 评估单个会话 |
| `curator_manager_evaluate_all_before` / `curator_manager_evaluate_all_after` | 批量评估前后 | 评估全部会话 |

### Reviewer Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `reviewer_manager_construct_before` / `reviewer_manager_construct_after` | 构造前后 | 评审管理器实例化前后 |
| `reviewer_manager_init_before` / `reviewer_manager_init_after` | 初始化前后 | 初始化前后 |
| `reviewer_manager_register_arguments` | 参数注册后（after-only） | 追加评审参数 |
| `reviewer_manager_approve_before` / `reviewer_manager_approve_after` | 批准前后 | 人工批准 |
| `reviewer_manager_reject_before` / `reviewer_manager_reject_after` | 拒绝前后 | 人工拒绝 |
| `reviewer_manager_update_before` / `reviewer_manager_update_after` | 更新前后 | 更新会话 |
| `reviewer_manager_batch_approve_before` / `reviewer_manager_batch_approve_after` | 批量批准前后 | 批量批准 |
| `reviewer_manager_batch_reject_before` / `reviewer_manager_batch_reject_after` | 批量拒绝前后 | 批量拒绝 |
| `reviewer_manager_get_pending_before` / `reviewer_manager_get_pending_after` | 待审列表前后 | 获取待审列表 |
| `reviewer_manager_get_audit_logs_before` / `reviewer_manager_get_audit_logs_after` | 审计日志前后 | 获取审计日志 |

### Exporter Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `exporter_manager_construct_before` / `exporter_manager_construct_after` | 构造前后 | 导出管理器实例化前后 |
| `exporter_manager_init_before` / `exporter_manager_init_after` | 初始化前后 | 初始化前后 |
| `exporter_manager_register_arguments` | 参数注册后（after-only） | 追加导出参数 |
| `exporter_manager_export_before` / `exporter_manager_export_after` | 导出前后 | 执行导出 |
| `exporter_manager_get_history_before` / `exporter_manager_get_history_after` | 历史查询前后 | 获取导出历史 |

## 插件注册的 Hook 点（plugins/）

| Hook 点 | 插件 | 说明 |
|---------|------|------|
| `collector_manager_scan_after` | collectors/openclaw | 合并 OpenClaw 扫描到的 jsonl 文件 |
| `collector_manager_parse_before` | collectors/openclaw | 短路内置解析，改由 OpenClaw 采集器解析 |
| `secrets_manager_register_arguments` | services/infisical | 追加 Infisical SDK 参数 |
| `secrets_manager_init_before` | services/infisical | 配置凭证时启用 Infisical 密钥客户端 |
