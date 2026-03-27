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

    def test_transaction_commit(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        with self.manager.transaction() as conn:
            conn.execute("INSERT INTO sessions (session_id, file_path) VALUES (?, ?)",
                        ("tx-test-1", "/test/tx.json"))

        session = self.manager.session_get("tx-test-1")
        assert session is not None

    def test_transaction_rollback(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        try:
            with self.manager.transaction() as conn:
                conn.execute("INSERT INTO sessions (session_id, file_path) VALUES (?, ?)",
                            ("tx-test-2", "/test/tx2.json"))
                raise RuntimeError("Intentional rollback")
        except RuntimeError:
            pass

        session = self.manager.session_get("tx-test-2")
        assert session is None

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

    def test_raises_if_not_initialized_transaction(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            with self.manager.transaction():
                pass

    def test_raises_if_not_initialized_audit_log(self):
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            self.manager.audit_log_create("test", "action")
