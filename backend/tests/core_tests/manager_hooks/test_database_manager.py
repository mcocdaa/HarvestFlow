import argparse
import pytest
from core.hook_manager import hook_manager


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
