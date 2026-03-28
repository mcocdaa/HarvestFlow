---
title: 插件开发指南
description: Hook插件开发完整指南
keywords: [plugin, 开发指南, 最佳实践]
version: "1.0"
---

# 插件开发指南

## 创建新插件

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

## 钩子函数规范

### 函数签名

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

### 参数访问

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

### 异步钩子

```python
@hook_manager.hook("async_hook_after")
async def async_hook(args, result):
    """异步钩子函数"""
    await some_async_operation()
```

## 优先级控制

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

## 错误处理

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
