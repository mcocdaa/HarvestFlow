# @file backend/test/test_reviewer_manager.py
# @brief 人工审核管理器测试
# @create 2026-03-18

import pytest
import os
import json
from core.database import get_database
from managers.reviewer_manager import ReviewerManager
from managers.session_manager import SessionManager


class TestReviewerManager:
    @pytest.fixture(autouse=True)
    def setup_method(self, test_db_path, test_data_dir):
        from core import database as db_module
        import config.settings as settings

        db_module._db_instance = None
        settings.DB_PATH = test_db_path
        settings.HUMAN_APPROVED_DIR = os.path.join(test_data_dir, "human_approved")
        os.makedirs(settings.HUMAN_APPROVED_DIR, exist_ok=True)

        self.db = get_database()
        self.db.initialize_tables()

        self.reviewer = ReviewerManager()
        self.reviewer.db = self.db

        self.session_manager = SessionManager()
        self.session_manager.db = self.db

        yield

        self.db.close()

    def test_approve_session(self, sample_session):
        self.session_manager.create_session(sample_session)

        result = self.reviewer.approve_session("test_session_001")

        assert result is not None
        assert result["status"] == "approved"

    def test_approve_nonexistent_session(self):
        result = self.reviewer.approve_session("nonexistent")
        assert result is None

    def test_reject_session(self, sample_session):
        self.session_manager.create_session(sample_session)

        result = self.reviewer.reject_session("test_session_001", "Not relevant")

        assert result is not None
        assert result["status"] == "rejected"

    def test_reject_nonexistent_session(self):
        result = self.reviewer.reject_session("nonexistent")
        assert result is None

    def test_update_session(self, sample_session):
        self.session_manager.create_session(sample_session)

        updates = {
            "quality_manual_score": 5,
            "tags": ["reviewed", "important"]
        }

        result = self.reviewer.update_session("test_session_001", updates)

        assert result is not None
        assert result["quality_manual_score"] == 5

    def test_batch_approve(self, sample_session):
        for i in range(5):
            session = sample_session.copy()
            session["session_id"] = f"session_{i}"
            self.session_manager.create_session(session)

        session_ids = [f"session_{i}" for i in range(5)]
        result = self.reviewer.batch_approve(session_ids)

        assert result["success"] == 5
        assert result["total"] == 5

    def test_batch_reject(self, sample_session):
        for i in range(5):
            session = sample_session.copy()
            session["session_id"] = f"session_{i}"
            self.session_manager.create_session(session)

        session_ids = [f"session_{i}" for i in range(5)]
        result = self.reviewer.batch_reject(session_ids)

        assert result["success"] == 5
        assert result["total"] == 5

    def test_get_pending_sessions(self, sample_session):
        self.session_manager.create_session(sample_session)

        result = self.reviewer.get_pending_sessions()

        assert "sessions" in result

    def test_get_audit_logs(self, sample_session):
        self.session_manager.create_session(sample_session)
        self.reviewer.approve_session("test_session_001", "Test notes")

        logs = self.reviewer.get_audit_logs()

        assert len(logs) > 0
        assert logs[0]["action"] == "approve"

    def test_get_audit_logs_by_session(self, sample_session):
        self.session_manager.create_session(sample_session)
        self.reviewer.approve_session("test_session_001")

        logs = self.reviewer.get_audit_logs("test_session_001")

        assert len(logs) > 0
        assert all(log["session_id"] == "test_session_001" for log in logs)
