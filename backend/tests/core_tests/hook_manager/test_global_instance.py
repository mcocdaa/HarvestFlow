import pytest
import asyncio
from core.hook_manager import hook_manager


class TestGlobalHookManager:
    def test_global_singleton(self):
        assert hook_manager is not None

    def test_clear(self):
        results = []

        def cb():
            results.append(1)

        hook_manager.register("clear_test", cb)
        hook_manager.clear()

        asyncio.run(hook_manager.run("clear_test"))

        assert results == []
