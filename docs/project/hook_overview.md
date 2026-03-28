---
title: Hook插件概述
description: Hook插件系统架构概述与核心组件
keywords: [hook, plugin, 概述, 架构]
version: "1.0"
---

# Hook 插件概述

## 概述

HarvestFlow 采用基于 Hook（钩子）的插件架构，允许开发者在不修改核心代码的情况下扩展系统功能。

### 核心特性

- **非侵入式扩展**：通过钩子机制在特定时机注入自定义逻辑
- **优先级控制**：支持多个钩子按优先级顺序执行
- **异步支持**：同时支持同步和异步钩子函数
- **错误隔离**：单个钩子失败不影响其他钩子执行

## 核心组件

### Hook Manager（钩子管理器）

位置：`backend/core/hook_manager.py`

负责：
- 注册和管理所有钩子
- 在特定时机触发钩子执行
- 处理钩子的优先级排序
- 提供错误隔离和日志记录

### Hook Point（钩子点）

命名规范：`{manager_name}_{method_name}_{timing}`

timing 类型：
- `before`：方法执行前
- `after`：方法执行后

示例：
- `collector_manager_scan_before`：采集器扫描前
- `secrets_manager_init_after`：密钥管理器初始化后

### 插件类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `collector` | 数据采集插件 | 扫描文件夹、解析文件 |
| `curator` | 数据审核插件 | 质量评估、过滤筛选 |
| `reviewer` | 人工审核插件 | 审批流程、审计日志 |
| `exporter` | 数据导出插件 | 格式转换、数据导出 |
| `service` | 服务插件 | 密钥管理、外部集成 |
