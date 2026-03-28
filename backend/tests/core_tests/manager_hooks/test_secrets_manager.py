import argparse
import pytest
from core.hook_manager import hook_manager


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
