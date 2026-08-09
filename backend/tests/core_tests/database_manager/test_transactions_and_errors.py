# @file backend/tests/core_tests/database_manager/test_transactions_and_errors.py
# @brief DatabaseManager 事务和错误处理测试
# @create 2026-03-27

import pytest

from core.database_manager import DatabaseManager


class TestDatabaseManagerTransactionsAndErrors:
    def setup_method(self):
        self.manager = DatabaseManager()

    def teardown_method(self):
        if self.manager.connection:
            self.manager.close()

    def test_raises_if_not_initialized_session_create(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager.session_create({"session_id": "test"})

    def test_raises_if_not_initialized_session_get(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager.session_get("test")

    def test_raises_if_not_initialized_session_update(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager.session_update("test", {})

    def test_raises_if_not_initialized_session_delete(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager.session_delete("test")

    def test_raises_if_not_initialized_audit_log(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager.audit_log_create("test", "action")

    def test_close_connection(self, args_with_db_path):
        self.manager.init(args_with_db_path)
        assert self.manager.connection is not None

        self.manager.close()
        assert self.manager.connection is None

        self.manager.close()
        assert self.manager.connection is None

    def test_session_delete_returns_false_when_session_not_exists(self, args_with_db_path):
        self.manager.init(args_with_db_path)
        result = self.manager.session_delete("nonexistent-session-id")
        assert result is False

    def test_session_delete_handles_remove_file_exception(self, args_with_db_path, monkeypatch):
        self.manager.init(args_with_db_path)
        session_id = "test-session-123"
        self.manager.session_create({"session_id": session_id, "file_path": "/nonexistent/path/file.txt"})

        session = self.manager.session_get(session_id)
        assert session is not None

        result = self.manager.session_delete(session_id)
        assert result is True
