# @file backend/core/hook_manager.py
# @brief Hook 管理器 - 实现动作钩子模式
# @create 2026-03-26

from collections import defaultdict
import asyncio
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


class HookManager:
    def __init__(self):
        self._hooks = defaultdict(list)

    def clear(self):
        """清除所有钩子（用于测试）"""
        self._hooks.clear()

    def register(self, hook_name: str, callback: Callable, priority: int = 100):
        """手动注册钩子（priority 越小越先执行）"""
        self._hooks[hook_name].append((priority, callback))
        self._hooks[hook_name].sort(key=lambda x: x[0])

    async def run(self, hook_name: str, *args, **kwargs):
        """执行所有已注册的钩子"""
        errors = []
        for _, cb in self._hooks.get(hook_name, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(*args, **kwargs)
                else:
                    cb(*args, **kwargs)
            except Exception as e:
                errors.append((cb.__name__, e))
                logger.error(f"钩子执行失败 [{hook_name}]: {cb.__name__} - {e}", exc_info=True)
        return errors

    def run_sync(self, hook_name: str, *args, **kwargs):
        """同步执行钩子（给同步包装器用）"""
        errors = []
        for _, cb in self._hooks.get(hook_name, []):
            try:
                # 只执行同步钩子（同步环境不能调用异步）
                if not asyncio.iscoroutinefunction(cb):
                    cb(*args, **kwargs)
                else:
                    msg = "异步钩子不能在同步环境中执行"
                    logger.warning(f"[{hook_name}]: {cb.__name__} - {msg}")
            except Exception as e:
                errors.append((cb.__name__, e))
                logger.error(f"钩子执行失败 [{hook_name}]: {cb.__name__} - {e}", exc_info=True)
        return errors

    def hook(self, hook_name: str, priority: int = 100):
        """装饰器：自动注册钩子

        用法：
            @hook_manager.hook("secrets_init_before", priority=10)
            def my_hook(ctx):
                ctx.add_provider(MyProvider())
        """
        def decorator(callback: Callable):
            self.register(hook_name, callback, priority)
            return callback
        return decorator

    def wrap_hooks(self, before: str = None, after: str = None):
        """装饰器：给核心服务的方法加钩子，自动在方法前后执行

        用法：
            class SecretsManager:
                @hook_manager.wrap_hooks(before="secrets_init_before", after="secrets_init_after")
                async def init(self):
                    self._init_clients()
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if before:
                    await self.run(before, *args, **kwargs)
                result = await func(*args, **kwargs)
                if after:
                    await self.run(after, *args, **kwargs)
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if before:
                    self.run_sync(before, *args, **kwargs)

                result = func(*args, **kwargs)

                if after:
                    self.run_sync(after, *args, **kwargs)
                return result

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return decorator


hook_manager = HookManager()
