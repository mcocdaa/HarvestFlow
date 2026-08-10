# @file backend/tests/core_tests/hook_manager/test_unregister.py
# @brief Hook 注销测试
# @create 2026-08-10

import asyncio
import pytest
from core.hook_manager import HookManager


@pytest.fixture
def fresh_hook_manager():
    hm = HookManager()
    yield hm
    hm.clear()


class TestUnregister:
    def test_unregister_removes_callback(self, fresh_hook_manager):
        """unregister 应移除指定钩子的回调"""
        called = []

        def cb(value):
            called.append(value)

        fresh_hook_manager.register("test_hook", cb)
        results, _ = asyncio.run(fresh_hook_manager.run("test_hook", "hello"))
        assert len(called) == 1

        fresh_hook_manager.unregister("test_hook", cb)
        called.clear()
        results, _ = asyncio.run(fresh_hook_manager.run("test_hook", "world"))
        assert len(called) == 0

    def test_unregister_nonexistent_hook_no_error(self, fresh_hook_manager):
        """卸载不存在的钩子不应报错"""

        def cb(value):
            pass

        # Should not raise
        fresh_hook_manager.unregister("nonexistent", cb)

    def test_unregister_by_module_removes_all(self, fresh_hook_manager):
        """unregister_by_module 应移除指定模块的所有回调"""
        called = []

        def cb1(value):
            called.append(("cb1", value))

        def cb2(value):
            called.append(("cb2", value))

        # cb1's module is this test file
        fresh_hook_manager.register("hook_a", cb1)
        fresh_hook_manager.register("hook_b", cb2)

        # Both should be callable initially
        asyncio.run(fresh_hook_manager.run("hook_a", "a"))
        asyncio.run(fresh_hook_manager.run("hook_b", "b"))
        assert len(called) == 2

        # Unregister by this test module
        mod = cb1.__module__
        fresh_hook_manager.unregister_by_module(mod)

        called.clear()
        asyncio.run(fresh_hook_manager.run("hook_a", "a2"))
        asyncio.run(fresh_hook_manager.run("hook_b", "b2"))
        assert len(called) == 0
