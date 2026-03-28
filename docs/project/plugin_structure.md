---
title: 插件结构
description: Hook插件目录结构与配置文件
keywords: [plugin, 插件结构, 配置]
version: "1.0"
---

# 插件结构

## 目录结构

```
plugins/
├── plugins.yaml              # 插件注册表
├── collectors/               # 采集器插件
│   └── default/
│       ├── __init__.py
│       ├── plugin.yaml       # 插件清单
│       ├── hooks.py          # 钩子定义
│       └── backend.py        # 后端实现
├── curators/                 # 审核器插件
├── reviewers/                # 人工审核插件
└── services/                 # 服务插件
    └── infisical/
        ├── __init__.py
        ├── plugin.yaml
        └── hooks.py
```

## 插件注册表（plugins.yaml）

```yaml
plugins:
  collectors/default:
    enabled: true              # 是否启用

  collectors/openclaw:
    enabled: false

  services/infisical:
    enabled: true
```

## 插件清单（plugin.yaml）

```yaml
name: Plugin Name
type: collector               # 插件类型
version: 1.0.0
description: Plugin description
author: Author Name

# 密钥定义
secrets:
  - name: API_KEY
    description: API密钥
    level: required           # required | optional
    default: null

# 钩子声明
hooks:
  - collector_manager_scan_after
  - collector_manager_import_after

# 插件配置
config:
  backend_entry: backend.py   # 后端入口文件
```

## 插件入口（__init__.py）

```python
# @file plugins/collectors/default/__init__.py
# @brief 插件入口 - 导入钩子以注册

from plugins.collectors.default.hooks import *
```

## 钩子定义（hooks.py）

```python
# @file plugins/collectors/default/hooks.py
# @brief 默认采集器插件钩子

from core.hook_manager import hook_manager

@hook_manager.hook("collector_manager_scan_after")
def default_collector_scan(args, result):
    """默认采集器扫描钩子"""
    pass

@hook_manager.hook("collector_manager_import_after")
def default_collector_import(args, result):
    """默认采集器导入钩子"""
    pass
```
