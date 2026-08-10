# @file backend/tests/managers_tests/test_reviewer_manager.py
# @brief ReviewerManager 测试
# @create 2026-03-26

import argparse


from managers.reviewer_manager import ReviewerManager


class TestReviewerManager:
    def setup_method(self):
        self.manager = ReviewerManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_update_session_invalid_status_transition(self, args_minimal, monkeypatch):
        """P1.1: update_session should return error on invalid status transition."""
        from managers import session_manager

        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id, "status": "raw"}

        def mock_update(session_id, updates):
            # "approved" is not a valid transition from "raw"
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)
        monkeypatch.setattr(session_manager, "update_session", mock_update)

        result = self.manager.update_session("test-session", {"status": "approved"})

        assert "error" in result
        assert result["error"] == "invalid status transition"

    def test_update_session_returns_full_session_on_success(self, args_minimal, monkeypatch):
        """P1.1: update_session should return the updated session on success."""
        from managers import session_manager
        from core import database_manager

        self.manager.init(args_minimal)

        updated_session = {"session_id": "test-session", "status": "approved", "quality_manual_score": 90}

        def mock_get(session_id):
            return {"session_id": session_id, "status": "curated"}

        def mock_update(session_id, updates):
            return updated_session

        monkeypatch.setattr(session_manager, "get_session", mock_get)
        monkeypatch.setattr(session_manager, "update_session", mock_update)
        monkeypatch.setattr(database_manager, "audit_log_create", lambda *args, **kwargs: None)

        result = self.manager.update_session("test-session", {"quality_manual_score": 90})

        assert "error" not in result
        assert result["session_id"] == "test-session"

    def test_approve_session_invalid_status(self, args_minimal, monkeypatch):
        """P1.2: approve should reject sessions where transition is not in flow table."""
        from managers import session_manager

        self.manager.init(args_minimal)

        monkeypatch.setattr(session_manager, "get_session",
                            lambda sid: {"session_id": sid, "status": "raw"})

        result = self.manager.approve_session("test-session")

        assert "error" in result
        assert result["error"] == "invalid status transition"

    def test_reject_session_invalid_status(self, args_minimal, monkeypatch):
        """P1.2: reject should reject sessions where transition is not in flow table."""
        from managers import session_manager

        self.manager.init(args_minimal)

        monkeypatch.setattr(session_manager, "get_session",
                            lambda sid: {"session_id": sid, "status": "raw"})

        result = self.manager.reject_session("test-session")

        assert "error" in result
        assert result["error"] == "invalid status transition"
