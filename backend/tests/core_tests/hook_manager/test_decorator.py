import pytest
import asyncio
from core.hook_manager import HookManager


@pytest.fixture
def fresh_hook_manager():
    hm = HookManager()
    yield hm
    hm.clear()


class TestDecoratorRegistration:
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
