# @file backend/test/test_session_manager.py
# @brief 会话管理器测试
# @create 2026-03-18

import pytest
import os
import json
from core.database import Database
from managers.session_manager import SessionManager


class TestSessionManager:
    @pytest.fixture(autouse=True)
    def setup_method(self, test_db_path):
        self.db_path = test_db_path
        self.db = Database(test_db_path)
        self.db.initialize_tables()

        self.manager = SessionManager()
        self.manager.db = self.db

        yield

        self.db.close()

    def test_create_session(self, sample_session):
        result = self.manager.create_session(sample_session)

        assert result["session_id"] == sample_session["session_id"]

        session = self.manager.get_session(sample_session["session_id"])
        assert session is not None
        assert session["session_id"] == "test_session_001"

    def test_get_session(self, sample_session):
        self.manager.create_session(sample_session)

        session = self.manager.get_session("test_session_001")
        assert session is not None
        assert session["session_id"] == "test_session_001"
        assert session["status"] == "raw"

    def test_get_session_not_found(self):
        session = self.manager.get_session("nonexistent")
        assert session is None

    def test_get_sessions_empty(self):
        result = self.manager.get_sessions()
        assert result["sessions"] == []
        assert result["total"] == 0

    def test_get_sessions_with_data(self, sample_session):
        self.manager.create_session(sample_session)

        result = self.manager.get_sessions()
        assert result["total"] == 1
        assert len(result["sessions"]) == 1

    def test_get_sessions_by_status(self, sample_session):
        self.manager.create_session(sample_session)

        result = self.manager.get_sessions(status="raw")
        assert result["total"] == 1

        result = self.manager.get_sessions(status="approved")
        assert result["total"] == 0

    def test_get_sessions_pagination(self, sample_session):
        for i in range(25):
            session = sample_session.copy()
            session["session_id"] = f"session_{i:03d}"
            self.manager.create_session(session)

        result = self.manager.get_sessions(page=1, page_size=10)
        assert result["total"] == 25
        assert len(result["sessions"]) == 10
        assert result["page"] == 1
        assert result["page_size"] == 10

        result = self.manager.get_sessions(page=3, page_size=10)
        assert len(result["sessions"]) == 5

    def test_update_session(self, sample_session):
        self.manager.create_session(sample_session)

        updates = {
            "status": "approved",
            "quality_manual_score": 5,
            "tags": ["reviewed"]
        }

        result = self.manager.update_session("test_session_001", updates)
        assert result is not None
        assert result["status"] == "approved"
        assert result["quality_manual_score"] == 5

    def test_delete_session(self, sample_session):
        self.manager.create_session(sample_session)

        result = self.manager.delete_session("test_session_001")
        assert result is True

        session = self.manager.get_session("test_session_001")
        assert session is None

    def test_delete_nonexistent_session(self):
        result = self.manager.delete_session("nonexistent")
        assert result is False

    def test_get_session_content(self, temp_dir, sample_session):
        session_file = os.path.join(temp_dir, "test_session.json")
        with open(session_file, 'w') as f:
            json.dump(sample_session, f)

        sample_session["file_path"] = session_file
        self.manager.create_session(sample_session)

        content = self.manager.get_session_content("test_session_001")
        assert content is not None
        assert content["session_id"] == "test_session_001"
        assert len(content["messages"]) == 3

    def test_get_session_content_not_found(self):
        content = self.manager.get_session_content("nonexistent")
        assert content is None
