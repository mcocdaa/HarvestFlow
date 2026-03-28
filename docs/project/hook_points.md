---
title: 内置Hook点
description: 系统内置Hook点列表
keywords: [hook, 钩子点, 内置]
version: "1.0"
---

# 内置 Hook 点列表

## Plugin Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `plugin_manager_construct_before` | 构造前 | 插件管理器实例化前 |
| `plugin_manager_construct_after` | 构造后 | 插件管理器实例化后 |
| `plugin_manager_init_before` | 初始化前 | 插件管理器初始化前 |
| `plugin_manager_init_after` | 初始化后 | 插件管理器初始化后 |

## Secrets Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `secrets_manager_construct_before` | 构造前 | 密钥管理器实例化前 |
| `secrets_manager_construct_after` | 构造后 | 密钥管理器实例化后 |
| `secrets_manager_init_before` | 初始化前 | 密钥管理器初始化前 |
| `secrets_manager_init_after` | 初始化后 | 密钥管理器初始化后 |

## Collector Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `collector_manager_construct_before` | 构造前 | 采集管理器实例化前 |
| `collector_manager_construct_after` | 构造后 | 采集管理器实例化后 |
| `collector_manager_init_before` | 初始化前 | 采集管理器初始化前 |
| `collector_manager_init_after` | 初始化后 | 采集管理器初始化后 |
| `collector_manager_scan_before` | 扫描前 | 扫描文件夹前 |
| `collector_manager_scan_after` | 扫描后 | 扫描文件夹后 |
| `collector_manager_parse_before` | 解析前 | 解析文件前 |
| `collector_manager_parse_after` | 解析后 | 解析文件后 |
| `collector_manager_import_before` | 导入前 | 导入会话前 |
| `collector_manager_import_after` | 导入后 | 导入会话后 |

## Reviewer Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `reviewer_manager_approve_before` | 批准前 | 批准会话前 |
| `reviewer_manager_approve_after` | 批准后 | 批准会话后 |
| `reviewer_manager_reject_before` | 拒绝前 | 拒绝会话前 |
| `reviewer_manager_reject_after` | 拒绝后 | 拒绝会话后 |
| `reviewer_manager_update_before` | 更新前 | 更新会话前 |
| `reviewer_manager_update_after` | 更新后 | 更新会话后 |

## Curator Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `curator_manager_evaluate_after` | 评估后 | 数据质量评估后 |
