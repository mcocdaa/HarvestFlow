# @file backend/tests/core_tests/database_manager/test_sessions.py
# @brief DatabaseManager Session 操作测试
# @create 2026-03-27

import pytest

from core.database_manager import DatabaseManager


class TestDatabaseManagerSessions:
    def setup_method(self):
        self.manager = DatabaseManager()

    def teardown_method(self):
        if self.manager.connection:
            self.manager.close()

    def test_session_create_and_get(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        session_data = {
            "session_id": "test-session-001",
            "file_path": "/tmp/test.json",
            "status": "raw",
            "agent_role": "tester",
            "task_type": "testing",
        }
        result = self.manager.session_create(session_data)
        assert result["session_id"] == "test-session-001"

        session = self.manager.session_get("test-session-001")
        assert session is not None
        assert session["session_id"] == "test-session-001"
        assert session["status"] == "raw"

    def test_session_get_not_found(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        session = self.manager.session_get("nonexistent")
        assert session is None

    def test_session_update(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        session_data = {
            "session_id": "test-session-002",
            "file_path": "/tmp/test.json",
            "status": "raw",
        }
        self.manager.session_create(session_data)

        updated = self.manager.session_update("test-session-002", {
            "status": "curated",
            "quality_auto_score": 85
        })
        assert updated is not None
        assert updated["status"] == "curated"
        assert updated["quality_auto_score"] == 85

    def test_session_delete(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        session_data = {
            "session_id": "test-session-003",
            "file_path": "/tmp/test.json",
            "status": "raw",
        }
        self.manager.session_create(session_data)

        result = self.manager.session_delete("test-session-003")
        assert result is True

        session = self.manager.session_get("test-session-003")
        assert session is None

    def test_session_update_no_allowed_fields(self, args_with_db_path):
        self.manager.init(args_with_db_path)
        self.manager.session_create({"session_id": "test", "file_path": "/test.json"})

        result = self.manager.session_update("test", {})
        assert result is None

    def test_session_delete_not_found(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        result = self.manager.session_delete("nonexistent")
        assert result is False

    def test_session_delete_ignores_file_error(self, args_with_db_path):
        self.manager.init(args_with_db_path)
        self.manager.session_create({
            "session_id": "test-delete-error",
            "file_path": "/nonexistent/path/does/not/exist.json",
            "status": "raw"
        })

        result = self.manager.session_delete("test-delete-error")
        assert result is True
        assert self.manager.session_get("test-delete-error") is None

    def test_json_fields_loaded_correctly(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.session_create({
            "session_id": "json-test",
            "file_path": "/test/json.json",
            "status": "raw",
            "tags": ["tag1", "tag2", "tag3"],
            "tools_used": ["tool1", "tool2"]
        })

        session = self.manager.session_get("json-test")
        assert session["tags"] == ["tag1", "tag2", "tag3"]
        assert session["tools_used"] == ["tool1", "tool2"]
