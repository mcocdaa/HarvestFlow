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
