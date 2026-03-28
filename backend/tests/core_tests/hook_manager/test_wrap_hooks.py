import pytest
import asyncio
from core.hook_manager import HookManager


@pytest.fixture
def fresh_hook_manager():
    hm = HookManager()
    yield hm
    hm.clear()


class TestWrapHooks:
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

    def test_wrap_hooks_no_before_no_after(self, fresh_hook_manager):
        called_original = False

        @fresh_hook_manager.wrap_hooks()
        def wrapped():
            nonlocal called_original
            called_original = True
            return "no_hooks"

        result = wrapped()
        assert called_original
        assert result == "no_hooks"

    def test_wrap_hooks_async_no_before_no_after(self, fresh_hook_manager):
        called_original = False

        @fresh_hook_manager.wrap_hooks()
        async def wrapped():
            nonlocal called_original
            called_original = True
            return "async_no_hooks"

        result = asyncio.run(wrapped())
        assert called_original
        assert result == "async_no_hooks"
