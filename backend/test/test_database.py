# @file backend/test/test_database.py
# @brief 数据库模块测试
# @create 2026-03-18

import pytest
import os
import tempfile
from core.database import Database


class TestDatabase:
    def test_database_creation(self, test_db_path):
        db = Database(test_db_path)
        assert os.path.exists(test_db_path)
        db.close()

    def test_initialize_tables(self, test_db_path):
        db = Database(test_db_path)
        db.initialize_tables()

        result = db.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        assert result is not None

        result = db.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        assert result is not None

        result = db.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='export_records'")
        assert result is not None

        result = db.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='plugins'")
        assert result is not None

        db.close()

    def test_crud_operations(self, test_db_path):
        db = Database(test_db_path)
        db.initialize_tables()

        db.execute(
            "INSERT INTO sessions (session_id, file_path, status) VALUES (?, ?, ?)",
            ("test_001", "/tmp/test.json", "raw")
        )

        result = db.fetchone("SELECT * FROM sessions WHERE session_id = ?", ("test_001",))
        assert result is not None
        assert result["session_id"] == "test_001"
        assert result["status"] == "raw"

        db.execute(
            "UPDATE sessions SET status = ? WHERE session_id = ?",
            ("approved", "test_001")
        )

        result = db.fetchone("SELECT * FROM sessions WHERE session_id = ?", ("test_001",))
        assert result["status"] == "approved"

        db.execute("DELETE FROM sessions WHERE session_id = ?", ("test_001",))

        result = db.fetchone("SELECT * FROM sessions WHERE session_id = ?", ("test_001",))
        assert result is None

        db.close()

    def test_fetchall(self, test_db_path):
        db = Database(test_db_path)
        db.initialize_tables()

        db.execute("INSERT INTO sessions (session_id, file_path, status) VALUES (?, ?, ?)", ("t1", "/t1", "raw"))
        db.execute("INSERT INTO sessions (session_id, file_path, status) VALUES (?, ?, ?)", ("t2", "/t2", "raw"))
        db.execute("INSERT INTO sessions (session_id, file_path, status) VALUES (?, ?, ?)", ("t3", "/t3", "raw"))

        results = db.fetchall("SELECT * FROM sessions")
        assert len(results) == 3

        db.close()

    def test_execute_many(self, test_db_path):
        db = Database(test_db_path)
        db.initialize_tables()

        data = [
            ("multi_1", "/m1", "raw"),
            ("multi_2", "/m2", "raw"),
            ("multi_3", "/m3", "raw"),
        ]

        db.execute_many(
            "INSERT INTO sessions (session_id, file_path, status) VALUES (?, ?, ?)",
            data
        )

        results = db.fetchall("SELECT * FROM sessions")
        assert len(results) == 3

        db.close()
