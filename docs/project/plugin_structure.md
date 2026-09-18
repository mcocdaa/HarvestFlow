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
├── common.py                 # 插件公共辅助（call_on_load 等）
├── collectors/               # 采集器插件
│   └── openclaw/             # OpenClaw JSONL 采集器（已启用）
│       ├── __init__.py
│       ├── plugin.yaml       # 插件清单
│       ├── hooks.py          # 钩子定义
│       └── backend.py        # 后端实现
├── curators/                 # 自动审核插件
│   └── openclaw/             # OpenClaw 评分（curator_manager_score_before 窄钩子，已启用）
├── reviewers/                # 人工审核插件（预留，v1.1 落地）
├── services/                 # 服务插件
│   └── infisical/
│       ├── __init__.py
│       ├── plugin.yaml
│       └── hooks.py
├── examples/                 # 插件示例模板（collector/curator/reviewer/service 各一）
│   └── collector_example/
│       ├── __init__.py
│       ├── plugin.yaml
│       ├── hooks.py
│       └── backend.py
└── plugin-openclaw-to-harvestflow/   # OpenClaw 扩展（git submodule，非后端插件）
```

## 插件注册表（plugins.yaml）

```yaml
plugins:
  collectors/openclaw:
    enabled: true

  curators/openclaw:
    enabled: true

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

统一入口约定：

1. 有 hooks.py 的插件，`__init__.py` 必须导入其钩子：
   ```python
   from plugins.{path}.hooks import *  # 注册钩子
   ```
2. 有 `on_load` 初始化入口的插件（backend.py 中定义），通过公共辅助安全调用：
   ```python
   from plugins.{path}.backend import on_load
   from plugins.common import call_on_load
   call_on_load(on_load, "[{Name}]")
   ```
3. 无 `on_load` 的插件不调用 `call_on_load`。

`plugins/common.py` 提供：
- `call_on_load(on_load_func, log_prefix)`：调用插件 on_load，
  失败仅记录 `{log_prefix} 调用 on_load 失败：{e}` 日志，不中断插件导入。

示例（openclaw 采集器）：

```python
# @file plugins/collectors/openclaw/__init__.py
# @brief OpenClaw 采集器插件入口

from plugins.collectors.openclaw.hooks import *
from plugins.collectors.openclaw.backend import on_load
from plugins.common import call_on_load

call_on_load(on_load, "[OpenClaw]")
```

> 说明：`curators/openclaw` 已通过 `curator_manager_score_before` 窄钩子接入
> （只接管评分算法，校验与回写由 `CuratorManager` 模板负责），详见
> [plugin_development.md](plugin_development.md)。`reviewers/` 为预留目录，
> 加载约定与前端扩展字段规划于 v1.1。

## 钩子定义（hooks.py）

```python
# @file plugins/collectors/default/hooks.py
# @brief 默认采集器插件钩子

from core.hook_manager import hook_manager

@hook_manager.hook("collector_manager_scan_after")
def default_collector_scan(result, self, folder_path=None):
    """扫描后钩子：返回非 None 时替换扫描结果"""
    return result

@hook_manager.hook("collector_manager_import_after")
def default_collector_import(result, self, file_path):
    """导入后钩子：返回非 None 时替换导入结果"""
    return result
```
