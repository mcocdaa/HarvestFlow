---
title: Hook插件开发规范
description: Hook插件系统架构与开发指南
keywords: [hook, plugin, 插件, 钩子]
version: "1.0"
---

# HarvestFlow Hook 插件开发规范

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

## Hook Manager API

### 装饰器：注册钩子

```python
from core.hook_manager import hook_manager

@hook_manager.hook("hook_name", priority=100)
def my_hook(args, result):
    """钩子函数

    Args:
        args: 被装饰方法的参数
        result: 方法返回值（仅 after 钩子有效）
    """
    pass
```

参数说明：
- `hook_name`：钩子点名称
- `priority`：优先级（数字越小越先执行，默认 100）

### 装饰器：包装方法

```python
from core import hook_manager

class MyManager:
    @hook_manager.wrap_hooks("method_before", "method_after")
    async def my_method(self, arg1, arg2):
        """方法实现"""
        pass
```

参数说明：
- `before`：方法执行前的钩子点名称（可选）
- `after`：方法执行后的钩子点名称（可选）

### 手动注册

```python
from core.hook_manager import hook_manager

def my_callback(args, result):
    pass

hook_manager.register("hook_name", my_callback, priority=50)
```

### 执行钩子

异步执行：
```python
errors = await hook_manager.run("hook_name", *args, **kwargs)
```

同步执行：
```python
errors = hook_manager.run_sync("hook_name", *args, **kwargs)
```

返回值：错误列表 `[(callback_name, exception), ...]`

## 插件结构

### 目录结构

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

### 插件注册表（plugins.yaml）

```yaml
plugins:
  collectors/default:
    enabled: true              # 是否启用

  collectors/openclaw:
    enabled: false

  services/infisical:
    enabled: true
```

### 插件清单（plugin.yaml）

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

### 插件入口（__init__.py）

```python
# @file plugins/collectors/default/__init__.py
# @brief 插件入口 - 导入钩子以注册

from plugins.collectors.default.hooks import *
```

### 钩子定义（hooks.py）

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

## 插件开发指南

### 创建新插件

**步骤 1：创建插件目录**

```bash
mkdir -p plugins/collectors/my_collector
```

**步骤 2：创建插件清单（plugin.yaml）**

```yaml
name: My Collector
type: collector
version: 1.0.0
description: Custom data collector
author: Your Name

secrets: []

hooks:
  - collector_manager_scan_after

config:
  backend_entry: backend.py
```

**步骤 3：创建入口文件（__init__.py）**

```python
from plugins.collectors.my_collector.hooks import *
```

**步骤 4：创建钩子文件（hooks.py）**

```python
import logging
from core.hook_manager import hook_manager

logger = logging.getLogger(__name__)

@hook_manager.hook("collector_manager_scan_after", priority=50)
def my_collector_scan(args, result):
    """自定义扫描钩子"""
    logger.info(f"扫描完成，发现 {len(result)} 个文件")
```

**步骤 5：创建后端实现（backend.py）**

```python
from typing import List, Dict

class MyCollector:
    name = "my_collector"
    description = "Custom data collector"

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def scan(self) -> List[str]:
        """扫描逻辑"""
        return []

    def parse(self, file_path: str) -> Dict:
        """解析逻辑"""
        return {}

collector_plugin = MyCollector()

def get_collector():
    return collector_plugin
```

**步骤 6：注册插件（plugins.yaml）**

```yaml
plugins:
  collectors/my_collector:
    enabled: true
```

### 钩子函数规范

#### 函数签名

```python
def hook_function(args, result):
    """
    钩子函数标准签名

    Args:
        args: 被装饰方法的参数
              - 单个参数：直接传递
              - 多个参数：元组形式 (arg1, arg2, ...)
        result: 方法返回值（仅 after 钩子有效）

    Returns:
        None（钩子函数不应返回值）
    """
    pass
```

#### 参数访问

```python
@hook_manager.hook("manager_method_after")
def my_hook(args, result):
    # 访问单个参数
    if not isinstance(args, tuple):
        args = (args,)

    first_arg = args[0] if len(args) > 0 else None

    # 访问返回值
    if result:
        process_result(result)
```

#### 异步钩子

```python
@hook_manager.hook("async_hook_after")
async def async_hook(args, result):
    """异步钩子函数"""
    await some_async_operation()
```

### 优先级控制

```python
# 优先级 10 - 最先执行
@hook_manager.hook("hook_name", priority=10)
def first_hook(args, result):
    pass

# 优先级 50 - 中等优先级
@hook_manager.hook("hook_name", priority=50)
def medium_hook(args, result):
    pass

# 优先级 100 - 默认优先级
@hook_manager.hook("hook_name")
def default_hook(args, result):
    pass

# 优先级 200 - 最后执行
@hook_manager.hook("hook_name", priority=200)
def last_hook(args, result):
    pass
```

### 错误处理

```python
@hook_manager.hook("hook_name")
def safe_hook(args, result):
    try:
        # 可能出错的操作
        risky_operation()
    except Exception as e:
        logger.error(f"钩子执行失败: {e}", exc_info=True)
        # 错误会被 HookManager 捕获，不影响其他钩子
```

## 内置 Hook 点列表

### Plugin Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `plugin_manager_construct_before` | 构造前 | 插件管理器实例化前 |
| `plugin_manager_construct_after` | 构造后 | 插件管理器实例化后 |
| `plugin_manager_init_before` | 初始化前 | 插件管理器初始化前 |
| `plugin_manager_init_after` | 初始化后 | 插件管理器初始化后 |

### Secrets Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `secrets_manager_construct_before` | 构造前 | 密钥管理器实例化前 |
| `secrets_manager_construct_after` | 构造后 | 密钥管理器实例化后 |
| `secrets_manager_init_before` | 初始化前 | 密钥管理器初始化前 |
| `secrets_manager_init_after` | 初始化后 | 密钥管理器初始化后 |

### Collector Manager

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

### Reviewer Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `reviewer_manager_approve_before` | 批准前 | 批准会话前 |
| `reviewer_manager_approve_after` | 批准后 | 批准会话后 |
| `reviewer_manager_reject_before` | 拒绝前 | 拒绝会话前 |
| `reviewer_manager_reject_after` | 拒绝后 | 拒绝会话后 |
| `reviewer_manager_update_before` | 更新前 | 更新会话前 |
| `reviewer_manager_update_after` | 更新后 | 更新会话后 |

### Curator Manager

| Hook 点 | 时机 | 说明 |
|---------|------|------|
| `curator_manager_evaluate_after` | 评估后 | 数据质量评估后 |

## 最佳实践

### 命名规范

- **钩子点命名**：`{manager}_{method}_{timing}`
- **钩子函数命名**：`{plugin_name}_{action}`
- **插件目录命名**：小写字母，下划线分隔

### 性能优化

```python
@hook_manager.hook("hook_name", priority=100)
def optimized_hook(args, result):
    # 快速检查，避免不必要的处理
    if not should_process(result):
        return

    # 执行核心逻辑
    process_result(result)
```

### 日志记录

```python
import logging

logger = logging.getLogger(__name__)

@hook_manager.hook("hook_name")
def logged_hook(args, result):
    logger.debug(f"钩子开始执行: hook_name")
    try:
        # 处理逻辑
        logger.info(f"处理完成: {result}")
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
```

### 避免副作用

```python
@hook_manager.hook("hook_name")
def safe_hook(args, result):
    # 不要修改原始数据
    # result['modified'] = True  # ❌ 错误

    # 创建副本进行修改
    modified_result = result.copy()
    modified_result['modified'] = True  # ✅ 正确
```

## 完整示例

### 服务插件示例（Infisical）

**plugin.yaml**：
```yaml
name: Infisical Service
type: service
version: 1.0.0
description: Infisical SDK integration for secrets management

secrets:
  - name: INFISICAL_CLIENT_ID
    description: Infisical Client ID
    level: optional
  - name: INFISICAL_CLIENT_SECRET
    description: Infisical Client Secret
    level: optional

hooks:
  - secrets_manager_init_after
```

**hooks.py**：
```python
import logging
from core.hook_manager import hook_manager
from core import secrets_manager

logger = logging.getLogger(__name__)

@hook_manager.hook("secrets_manager_init_after")
def register_infisical_client(args, result):
    """注册 Infisical SDK 客户端"""
    if result and hasattr(secrets_manager, 'client'):
        logger.info("Infisical hook: 客户端已就绪")
```

### 采集器插件示例

**plugin.yaml**：
```yaml
name: JSON Collector
type: collector
version: 1.0.0
description: JSON file collector

secrets: []

hooks:
  - collector_manager_scan_after
  - collector_manager_import_after

config:
  backend_entry: backend.py
```

**hooks.py**：
```python
import logging
from core.hook_manager import hook_manager

logger = logging.getLogger(__name__)

@hook_manager.hook("collector_manager_scan_after", priority=50)
def log_scan_results(args, result):
    """记录扫描结果"""
    if result:
        logger.info(f"扫描完成: 发现 {len(result)} 个 JSON 文件")

@hook_manager.hook("collector_manager_import_after", priority=50)
def validate_import(args, result):
    """验证导入结果"""
    if result:
        logger.info(f"成功导入会话: {result}")
```

## 调试与故障排查

### 查看已注册钩子

```python
from core.hook_manager import hook_manager

# 查看所有钩子
for hook_name, callbacks in hook_manager._hooks.items():
    print(f"{hook_name}:")
    for priority, callback in callbacks:
        print(f"  - {callback.__name__} (priority: {priority})")
```

### 测试钩子执行

```python
import asyncio
from core.hook_manager import hook_manager

# 测试钩子执行
errors = asyncio.run(hook_manager.run("test_hook", "arg1", "arg2"))
if errors:
    for name, error in errors:
        print(f"钩子 {name} 失败: {error}")
```

### 清除钩子（测试用）

```python
from core.hook_manager import hook_manager

# 清除所有钩子
hook_manager.clear()
```

## 参考资料

- Hook Manager 源码：`backend/core/hook_manager.py`
- Plugin Manager 源码：`backend/core/plugin_manager.py`
- Hook Manager 测试：`backend/tests/test_hook_manager.py`
- 插件示例：`plugins/` 目录
