---
title: Hook API
description: Hook Manager API 文档
keywords: [hook, api, 钩子管理器]
version: "1.0"
---

# Hook Manager API

## 装饰器：注册钩子

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

## 装饰器：包装方法

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

## 手动注册

```python
from core.hook_manager import hook_manager

def my_callback(args, result):
    pass

hook_manager.register("hook_name", my_callback, priority=50)
```

## 执行钩子

异步执行：
```python
errors = await hook_manager.run("hook_name", *args, **kwargs)
```

同步执行：
```python
errors = hook_manager.run_sync("hook_name", *args, **kwargs)
```

返回值：错误列表 `[(callback_name, exception), ...]`

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
- Hook Manager 测试：`backend/tests/test_hook_manager.py`
