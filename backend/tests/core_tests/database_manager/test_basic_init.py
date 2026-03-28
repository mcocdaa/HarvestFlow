# @file backend/tests/core_tests/database_manager/test_basic_init.py
# @brief DatabaseManager 基础初始化测试
# @create 2026-03-27

import os
import argparse

import pytest

from core.database_manager import DatabaseManager


class TestDatabaseManagerBasicInit:
    def setup_method(self):
        self.manager = DatabaseManager()

    def teardown_method(self):
        if self.manager.connection:
            self.manager.close()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_init_creates_tables(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        assert self.manager.connection is not None
        assert os.path.exists(args_with_db_path.db_path)

    def test_close(self, args_with_db_path):
        self.manager.init(args_with_db_path)
        assert self.manager.connection is not None

        self.manager.close()
        assert self.manager.connection is None

    def test_init_creates_parent_dir(self, tmp_path):
        db_path = tmp_path / "data" / "db" / "test.db"
        args = argparse.Namespace(db_path=str(db_path))

        self.manager.init(args)
        assert db_path.exists()
        self.manager.close()

    def test_uses_setting_manager_fallback(self):
        from core import setting_manager
        original = setting_manager.config.get("DB_PATH")
        setting_manager.config["DB_PATH"] = "/tmp/fallback.db"

        args = argparse.Namespace()
        self.manager.init(args)
        assert self.manager.db_path == "/tmp/fallback.db"
        self.manager.close()

        if original is not None:
            setting_manager.config["DB_PATH"] = original

    def test__initialize_tables_raises_when_no_connection(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager._initialize_tables()

    def test__create_table_raises_when_no_connection(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager._create_table("CREATE TABLE test (id INTEGER)")
