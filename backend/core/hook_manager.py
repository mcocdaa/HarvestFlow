# @file backend/core/hook_manager.py
# @brief Hook 管理器 - 实现动作钩子模式
# @create 2026-03-26

from collections import defaultdict
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, List, Tuple

logger = logging.getLogger(__name__)

HookResult = Tuple[List[Any], List[Tuple[str, Exception]]]


class HookManager:
    """钩子管理器

    钩子语义（v2）：
    - before 钩子：签名与被包装方法一致（实例方法含 self）。
      返回非 None 时短路：跳过原方法，该值直接作为方法结果返回。
    - after 钩子：签名 (result, *被包装方法参数)。返回非 None 时替换 result，
      多个钩子按 priority 升序链式传递。

    使用流程：
    1. @hook_manager.hook("hook_name") 注册钩子
    2. @hook_manager.wrap_hooks(before=..., after=...) 在方法前后执行
    """

    def __init__(self):
        self._hooks = defaultdict(list)

    def clear(self):
        """清除所有钩子（用于测试）"""
        self._hooks.clear()

    def register(self, hook_name: str, callback: Callable, priority: int = 100):
        """手动注册钩子（priority 越小越先执行）"""
        self._hooks[hook_name].append((priority, callback))
        self._hooks[hook_name].sort(key=lambda x: x[0])

    async def run(self, hook_name: str, *args, **kwargs) -> HookResult:
        """异步执行所有已注册的钩子

        Args:
            hook_name: 钩子名称
            *args, **kwargs: 透传给每个钩子

        Returns:
            (results, errors): 钩子返回值列表（按注册顺序）与错误列表
        """
        results = []
        errors = []
        for _, cb in self._hooks.get(hook_name, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    results.append(await cb(*args, **kwargs))
                else:
                    results.append(cb(*args, **kwargs))
            except Exception as e:
                errors.append((cb.__name__, e))
                logger.error(f"钩子执行失败 [{hook_name}]: {cb.__name__} - {e}", exc_info=True)
        return results, errors

    def run_sync(self, hook_name: str, *args, **kwargs) -> HookResult:
        """同步执行钩子（给同步包装器用），只执行同步钩子

        Args:
            hook_name: 钩子名称
            *args, **kwargs: 透传给每个钩子

        Returns:
            (results, errors): 钩子返回值列表（按注册顺序）与错误列表
        """
        results = []
        errors = []
        for _, cb in self._hooks.get(hook_name, []):
            try:
                if not asyncio.iscoroutinefunction(cb):
                    results.append(cb(*args, **kwargs))
                else:
                    logger.warning(
                        f"[{hook_name}]: {cb.__name__} - 异步钩子不能在同步环境中执行"
                    )
            except Exception as e:
                errors.append((cb.__name__, e))
                logger.error(f"钩子执行失败 [{hook_name}]: {cb.__name__} - {e}", exc_info=True)
        return results, errors

    @staticmethod
    def _short_circuit(results: List[Any]) -> Any:
        """before 钩子短路：返回第一个非 None 的结果，无则返回 None"""
        for r in results:
            if r is not None:
                return r
        return None

    @staticmethod
    def _chain_result(base: Any, results: List[Any]) -> Any:
        """after 钩子链式修改：非 None 返回值依次替换结果"""
        result = base
        for r in results:
            if r is not None:
                result = r
        return result

    def hook(self, hook_name: str, priority: int = 100):
        """装饰器：自动注册钩子

        用法：
            @hook_manager.hook("collector_manager_parse_before")
            def my_hook(self, file_path):
                ...
        """
        def decorator(callback: Callable):
            self.register(hook_name, callback, priority)
            return callback
        return decorator

    def wrap_hooks(self, before: str = None, after: str = None):
        """装饰器：给核心服务的方法加钩子，自动在方法前后执行

        钩子语义：
        - before: 签名与被包装方法一致；返回非 None 时短路（跳过原方法）
        - after: 签名 (result, *被包装方法参数)；返回非 None 时替换 result

        用法：
            class CollectorManager:
                @hook_manager.wrap_hooks(before="collector_manager_parse_before",
                                         after="collector_manager_parse_after")
                def parse_session_file(self, file_path):
                    ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if before:
                    results, _ = await self.run(before, *args, **kwargs)
                    short = self._short_circuit(results)
                    if short is not None:
                        return short
                result = await func(*args, **kwargs)
                if after:
                    results, _ = await self.run(after, result, *args, **kwargs)
                    result = self._chain_result(result, results)
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if before:
                    results, _ = self.run_sync(before, *args, **kwargs)
                    short = self._short_circuit(results)
                    if short is not None:
                        return short
                result = func(*args, **kwargs)
                if after:
                    results, _ = self.run_sync(after, result, *args, **kwargs)
                    result = self._chain_result(result, results)
                return result

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator


hook_manager = HookManager()
