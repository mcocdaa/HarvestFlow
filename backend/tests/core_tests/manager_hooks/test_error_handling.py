import pytest
from core.hook_manager import hook_manager


class TestHookErrorIsolation:
    def test_hook_error_does_not_stop_other_hooks(self):
        from core.setting_manager import SettingManager

        call_order = []

        def error_hook(manager):
            raise RuntimeError("intentional error")

        def success_hook(manager):
            call_order.append("success")

        hook_manager.register("setting_manager_construct_before", error_hook, priority=10)
        hook_manager.register("setting_manager_construct_after", success_hook, priority=20)

        manager = SettingManager()

        assert "success" in call_order

    def test_multiple_hooks_all_called(self):
        from core.setting_manager import SettingManager

        call_order = []

        def hook1(manager):
            call_order.append(1)

        def hook2(manager):
            call_order.append(2)

        def hook3(manager):
            call_order.append(3)

        hook_manager.register("setting_manager_construct_after", hook3, priority=30)
        hook_manager.register("setting_manager_construct_after", hook1, priority=10)
        hook_manager.register("setting_manager_construct_after", hook2, priority=20)

        manager = SettingManager()

        assert call_order == [1, 2, 3]


class TestHookDecoratorRegistration:
    def test_decorator_registration(self):
        from core.setting_manager import SettingManager

        call_order = []

        @hook_manager.hook("setting_manager_construct_before", priority=10)
        def hook_a(manager):
            call_order.append("a")

        @hook_manager.hook("setting_manager_construct_before", priority=20)
        def hook_b(manager):
            call_order.append("b")

        manager = SettingManager()

        assert call_order == ["a", "b"]
