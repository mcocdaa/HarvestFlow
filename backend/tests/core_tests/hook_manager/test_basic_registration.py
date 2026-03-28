import pytest
import asyncio
from core.hook_manager import HookManager


@pytest.fixture
def fresh_hook_manager():
    hm = HookManager()
    yield hm
    hm.clear()


class TestBasicRegistration:
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

    def test_no_hook_registered(self, fresh_hook_manager):
        results = []

        asyncio.run(fresh_hook_manager.run("nonexistent_hook", "arg"))

        assert results == []
