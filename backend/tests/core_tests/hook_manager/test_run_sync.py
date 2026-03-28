import pytest
import asyncio
from core.hook_manager import HookManager


@pytest.fixture
def fresh_hook_manager():
    hm = HookManager()
    yield hm
    hm.clear()


class TestRunSync:
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
