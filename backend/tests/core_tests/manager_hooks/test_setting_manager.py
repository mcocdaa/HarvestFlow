import argparse
import pytest
from core.hook_manager import hook_manager


class TestSettingManagerHooks:
    def test_construct_hooks_called(self):
        from core.setting_manager import SettingManager

        call_order = []

        def on_construct_before(manager):
            call_order.append("before")

        def on_construct_after(manager):
            call_order.append("after")

        hook_manager.register("setting_manager_construct_before", on_construct_before, priority=10)
        hook_manager.register("setting_manager_construct_after", on_construct_after, priority=10)

        manager = SettingManager()

        assert "before" in call_order
        assert "after" in call_order
        assert call_order.index("before") < call_order.index("after")

    def test_register_arguments_hook_called(self):
        from core.setting_manager import SettingManager

        called = []

        def on_register_after(manager, parser):
            called.append(True)

        hook_manager.register("setting_manager_register_arguments", on_register_after, priority=10)

        manager = SettingManager()
        parser = argparse.ArgumentParser()
        manager.register_arguments(parser)

        assert len(called) == 1

    def test_init_hooks_called(self):
        from core.setting_manager import SettingManager

        call_order = []

        def on_init_before(manager, args):
            call_order.append("before")

        def on_init_after(manager, args):
            call_order.append("after")

        hook_manager.register("setting_manager_init_before", on_init_before, priority=10)
        hook_manager.register("setting_manager_init_after", on_init_after, priority=10)

        manager = SettingManager()
        args = argparse.Namespace(
            host="localhost",
            port=9000,
            data_dir="./data",
            log_level="INFO",
            cors_origins="*"
        )
        manager.init(args)

        assert "before" in call_order
        assert "after" in call_order

    def test_hook_receives_manager_instance(self):
        from core.setting_manager import SettingManager

        received = []

        def on_construct_after(manager):
            received.append(manager)

        hook_manager.register("setting_manager_construct_after", on_construct_after, priority=10)

        manager = SettingManager()

        assert len(received) == 1
        assert received[0] is manager
