# @file backend/tests/core_tests/test_manager_hooks.py
# @brief Manager 钩子集成测试
# @create 2026-03-26

import argparse
import pytest
from core.hook_manager import hook_manager


@pytest.fixture(autouse=True)
def clean_hooks():
    """每个测试前清理钩子"""
    hook_manager.clear()
    yield
    hook_manager.clear()


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


class TestDatabaseManagerHooks:
    def test_construct_hooks_called(self):
        from core.database_manager import DatabaseManager

        call_order = []

        def on_construct_before(manager):
            call_order.append("before")

        def on_construct_after(manager):
            call_order.append("after")

        hook_manager.register("database_manager_construct_before", on_construct_before, priority=10)
        hook_manager.register("database_manager_construct_after", on_construct_after, priority=10)

        manager = DatabaseManager()

        assert "before" in call_order
        assert "after" in call_order

    def test_register_arguments_hook_called(self):
        from core.database_manager import DatabaseManager

        called = []

        def on_register_after(manager, parser):
            called.append(True)

        hook_manager.register("database_manager_register_arguments", on_register_after, priority=10)

        manager = DatabaseManager()
        parser = argparse.ArgumentParser()
        manager.register_arguments(parser)

        assert len(called) == 1

    def test_initialize_hooks_called(self, temp_db_path):
        from core.database_manager import DatabaseManager

        call_order = []

        def on_init_before(manager, args):
            call_order.append("before")

        def on_init_after(manager, args):
            call_order.append("after")

        hook_manager.register("database_manager_initialize_before", on_init_before, priority=10)
        hook_manager.register("database_manager_initialize_after", on_init_after, priority=10)

        manager = DatabaseManager()
        args = argparse.Namespace(db_path=temp_db_path)
        manager.init(args)

        assert "before" in call_order
        assert "after" in call_order

        manager.close()


class TestSecretsManagerHooks:
    def test_construct_hooks_called(self):
        from core.secrets_manager import SecretsManager

        call_order = []

        def on_construct_before(manager):
            call_order.append("before")

        def on_construct_after(manager):
            call_order.append("after")

        hook_manager.register("secrets_manager_construct_before", on_construct_before, priority=10)
        hook_manager.register("secrets_manager_construct_after", on_construct_after, priority=10)

        manager = SecretsManager()

        assert "before" in call_order
        assert "after" in call_order

    def test_register_arguments_hook_called(self):
        from core.secrets_manager import SecretsManager

        called = []

        def on_register_after(manager, parser):
            called.append(True)

        hook_manager.register("secrets_manager_register_arguments", on_register_after, priority=10)

        manager = SecretsManager()
        parser = argparse.ArgumentParser()
        manager.register_arguments(parser)

        assert len(called) == 1

    def test_init_hooks_called(self):
        from core.secrets_manager import SecretsManager

        call_order = []

        def on_init_before(manager, args, plugin_secrets):
            call_order.append("before")

        def on_init_after(manager, args, plugin_secrets):
            call_order.append("after")

        hook_manager.register("secrets_manager_init_before", on_init_before, priority=10)
        hook_manager.register("secrets_manager_init_after", on_init_after, priority=10)

        manager = SecretsManager()
        args = argparse.Namespace(
            secrets_yaml="",
            cache_ttl=300
        )
        manager.init(args, [])

        assert "before" in call_order
        assert "after" in call_order


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
