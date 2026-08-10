import pytest
import asyncio
import logging
from core.hook_manager import HookManager


@pytest.fixture
def fresh_hook_manager():
    hm = HookManager()
    yield hm
    hm.clear()


class TestDispatch:
    def test_dispatch_returns_results_in_registration_order(self, fresh_hook_manager):
        order = []

        def first(value):
            order.append("first")
            return value

        def second(value):
            order.append("second")
            return value

        fresh_hook_manager.register("dispatch_order", first)
        fresh_hook_manager.register("dispatch_order", second)

        async def execute(cb):
            return True, cb("v")

        results, errors = asyncio.run(
            fresh_hook_manager._dispatch("dispatch_order", ("v",), {}, execute)
        )

        assert order == ["first", "second"]
        assert results == ["v", "v"]
        assert errors == []

    def test_dispatch_collects_execute_errors(self, fresh_hook_manager):
        def bad_cb():
            raise ValueError("boom")

        fresh_hook_manager.register("dispatch_errors", bad_cb)

        async def execute(cb):
            return True, cb()

        results, errors = asyncio.run(
            fresh_hook_manager._dispatch("dispatch_errors", (), {}, execute)
        )

        assert results == []
        assert len(errors) == 1
        assert errors[0][0] == "bad_cb"
        assert isinstance(errors[0][1], ValueError)

    def test_dispatch_skips_when_collect_is_false(self, fresh_hook_manager):
        fresh_hook_manager.register("dispatch_skip", lambda: "x")

        async def execute(cb):
            return False, cb()

        results, errors = asyncio.run(
            fresh_hook_manager._dispatch("dispatch_skip", (), {}, execute)
        )

        assert results == []
        assert errors == []

    def test_run_awaits_async_hooks(self, fresh_hook_manager):
        async def async_cb(value):
            await asyncio.sleep(0)
            return value * 2

        fresh_hook_manager.register("run_async", async_cb)
        results, errors = asyncio.run(fresh_hook_manager.run("run_async", 21))

        assert results == [42]
        assert errors == []

    def test_run_sync_skips_async_hooks_with_warning(self, fresh_hook_manager, caplog):
        async def async_cb():
            return "should not run"

        fresh_hook_manager.register("sync_warn", async_cb)
        with caplog.at_level(logging.WARNING, logger="core.hook_manager"):
            results, errors = fresh_hook_manager.run_sync("sync_warn")

        assert results == []
        assert errors == []
        assert any(
            "异步钩子不能在同步环境中执行" in record.getMessage()
            for record in caplog.records
        )
