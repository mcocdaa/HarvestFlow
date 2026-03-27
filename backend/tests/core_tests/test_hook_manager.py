# @file backend/tests/core_tests/test_hook_manager.py
# @brief HookManager 钩子管理器测试
# @create 2026-03-26

import pytest
import asyncio
from core.hook_manager import HookManager, hook_manager


@pytest.fixture
def fresh_hook_manager():
    """提供干净的 HookManager 实例"""
    hm = HookManager()
    yield hm
    hm.clear()


class TestHookManager:
    def test_register_and_run_sync(self, fresh_hook_manager):
        results = []

        def callback(value):
            results.append(value)

        fresh_hook_manager.register("test_hook", callback)
        asyncio.run(fresh_hook_manager.run("test_hook", "hello"))

        assert results == ["hello"]

    def test_register_and_run_async(self, fresh_hook_manager):
        results = []

        async def async_callback(value):
            results.append(value)

        fresh_hook_manager.register("test_async_hook", async_callback)
        asyncio.run(fresh_hook_manager.run("test_async_hook", "world"))

        assert results == ["world"]

    def test_priority_order(self, fresh_hook_manager):
        results = []

        def first():
            results.append(1)

        def second():
            results.append(2)

        def third():
            results.append(3)

        fresh_hook_manager.register("priority_test", third, priority=30)
        fresh_hook_manager.register("priority_test", first, priority=10)
        fresh_hook_manager.register("priority_test", second, priority=20)

        asyncio.run(fresh_hook_manager.run("priority_test"))

        assert results == [1, 2, 3]

    def test_multiple_callbacks(self, fresh_hook_manager):
        results = []

        def cb1():
            results.append("a")

        def cb2():
            results.append("b")

        def cb3():
            results.append("c")

        fresh_hook_manager.register("multi_test", cb1)
        fresh_hook_manager.register("multi_test", cb2)
        fresh_hook_manager.register("multi_test", cb3)

        asyncio.run(fresh_hook_manager.run("multi_test"))

        assert results == ["a", "b", "c"]

    def test_error_isolation(self, fresh_hook_manager):
        results = []

        def error_callback():
            raise ValueError("intentional error")

        def success_callback():
            results.append("success")

        fresh_hook_manager.register("error_test", error_callback)
        fresh_hook_manager.register("error_test", success_callback)

        errors = asyncio.run(fresh_hook_manager.run("error_test"))

        assert results == ["success"]
        assert len(errors) == 1
        assert errors[0][0] == "error_callback"
        assert isinstance(errors[0][1], ValueError)

    def test_no_hook_registered(self, fresh_hook_manager):
        results = []

        asyncio.run(fresh_hook_manager.run("nonexistent_hook", "arg"))

        assert results == []

    def test_decorator_registration(self, fresh_hook_manager):
        results = []

        @fresh_hook_manager.hook("decorator_test", priority=5)
        def my_hook(value):
            results.append(value)

        asyncio.run(fresh_hook_manager.run("decorator_test", "decorated"))

        assert results == ["decorated"]

    def test_decorator_with_priority(self, fresh_hook_manager):
        order = []

        @fresh_hook_manager.hook("dec_priority", priority=20)
        def hook_c():
            order.append("c")

        @fresh_hook_manager.hook("dec_priority", priority=10)
        def hook_a():
            order.append("a")

        @fresh_hook_manager.hook("dec_priority", priority=15)
        def hook_b():
            order.append("b")

        asyncio.run(fresh_hook_manager.run("dec_priority"))

        assert order == ["a", "b", "c"]

    def test_run_returns_errors(self, fresh_hook_manager):
        def error1():
            raise RuntimeError("error 1")

        def error2():
            raise ValueError("error 2")

        fresh_hook_manager.register("error_return_test", error1)
        fresh_hook_manager.register("error_return_test", error2)

        errors = asyncio.run(fresh_hook_manager.run("error_return_test"))

        assert len(errors) == 2
        assert errors[0][0] == "error1"
        assert errors[1][0] == "error2"


class TestGlobalHookManager:
    def test_global_singleton(self):
        assert hook_manager is not None
        assert isinstance(hook_manager, HookManager)

    def test_clear(self):
        results = []

        def cb():
            results.append(1)

        hook_manager.register("clear_test", cb)
        hook_manager.clear()

        asyncio.run(hook_manager.run("clear_test"))

        assert results == []


class TestHookManagerRunSync:
    def test_run_sync_executes_sync_hooks(self, fresh_hook_manager):
        results = []

        def callback(value):
            results.append(value)

        fresh_hook_manager.register("sync_test", callback)
        errors = fresh_hook_manager.run_sync("sync_test", "test_value")

        assert results == ["test_value"]
        assert len(errors) == 0

    def test_run_sync_skips_async_hooks_with_warning(self, fresh_hook_manager):
        results = []

        async def async_cb():
            results.append("ran")

        fresh_hook_manager.register("async_in_sync", async_cb)
        errors = fresh_hook_manager.run_sync("async_in_sync")

        assert results == []
        assert len(errors) == 0

    def test_run_sync_captures_errors(self, fresh_hook_manager):
        def bad_cb():
            raise ValueError("test error")

        fresh_hook_manager.register("error_test", bad_cb)
        errors = fresh_hook_manager.run_sync("error_test")

        assert len(errors) == 1
        assert errors[0][0] == "bad_cb"
        assert isinstance(errors[0][1], ValueError)

    def test_run_sync_no_hooks(self, fresh_hook_manager):
        errors = fresh_hook_manager.run_sync("nonexistent")
        assert len(errors) == 0


class TestHookManagerWrapHooks:
    def test_wrap_hooks_async_function_runs_before_after(self, fresh_hook_manager):
        order = []

        def before_hook(*args, **kwargs):
            order.append(f"before:{args[0]}")

        def after_hook(*args, **kwargs):
            order.append(f"after:{args[0]}")

        fresh_hook_manager.register("test_before", before_hook)
        fresh_hook_manager.register("test_after", after_hook)

        @fresh_hook_manager.wrap_hooks(before="test_before", after="test_after")
        async def wrapped_func(value):
            order.append(f"wrapped:{value}")
            return value * 2

        result = asyncio.run(wrapped_func(5))
        assert result == 10
        assert order == ["before:5", "wrapped:5", "after:5"]

    def test_wrap_hooks_sync_function_runs_before_after(self, fresh_hook_manager):
        order = []

        def before_hook(value):
            order.append(f"before:{value}")

        def after_hook(value):
            order.append(f"after:{value}")

        fresh_hook_manager.register("sync_before", before_hook)
        fresh_hook_manager.register("sync_after", after_hook)

        @fresh_hook_manager.wrap_hooks(before="sync_before", after="sync_after")
        def wrapped_func(value):
            order.append(f"wrapped:{value}")
            return value * 2

        result = wrapped_func(10)
        assert result == 20
        assert order == ["before:10", "wrapped:10", "after:10"]

    def test_wrap_hooks_only_before(self, fresh_hook_manager):
        order = []

        def before():
            order.append("before")

        fresh_hook_manager.register("only_before", before)

        @fresh_hook_manager.wrap_hooks(before="only_before")
        def wrapped():
            order.append("wrapped")
            return "done"

        result = wrapped()
        assert result == "done"
        assert order == ["before", "wrapped"]

    def test_wrap_hooks_only_after(self, fresh_hook_manager):
        order = []

        def after():
            order.append("after")

        fresh_hook_manager.register("only_after", after)

        @fresh_hook_manager.wrap_hooks(after="only_after")
        def wrapped():
            order.append("wrapped")
            return "done"

        result = wrapped()
        assert result == "done"
        assert order == ["wrapped", "after"]
