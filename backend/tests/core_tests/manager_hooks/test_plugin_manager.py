import argparse
import pytest
from core.hook_manager import hook_manager


class TestPluginManagerHooks:
    def test_construct_hooks_called(self, args_minimal):
        from core.plugin_manager import PluginManager

        call_order = []

        def on_construct_before(manager, args):
            call_order.append("before")

        def on_construct_after(manager, args):
            call_order.append("after")

        hook_manager.register("plugin_manager_init_before", on_construct_before, priority=10)
        hook_manager.register("plugin_manager_init_after", on_construct_after, priority=10)

        manager = PluginManager()
        manager.init(args_minimal)

        assert "before" in call_order
        assert "after" in call_order

    def test_register_arguments_hook_called(self):
        from core.plugin_manager import PluginManager

        called = []

        def on_register_after(manager, parser):
            called.append(True)

        hook_manager.register("plugin_manager_register_arguments", on_register_after, priority=10)

        manager = PluginManager()
        parser = argparse.ArgumentParser()
        manager.register_arguments(parser)

        assert len(called) == 1

    def test_init_hooks_called(self):
        from core.plugin_manager import PluginManager

        call_order = []

        def on_init_before(manager, args):
            call_order.append("before")

        def on_init_after(manager, args):
            call_order.append("after")

        hook_manager.register("plugin_manager_init_before", on_init_before, priority=10)
        hook_manager.register("plugin_manager_init_after", on_init_after, priority=10)

        manager = PluginManager()
        args = argparse.Namespace(plugins_dir="./plugins")
        manager.init(args)

        assert "before" in call_order
        assert "after" in call_order
