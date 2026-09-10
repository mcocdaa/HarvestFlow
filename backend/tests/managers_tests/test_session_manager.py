# @file backend/tests/managers_tests/test_session_manager.py
# @brief SessionManager 测试
# @create 2026-03-26

import argparse

import pytest

from managers.session_manager import SessionManager


class TestSessionManager:
    def setup_method(self):
        self.manager = SessionManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_update_session_invalid_transition_raises(self, monkeypatch):
        """更新会话为不合法的状态流转时应抛出 ValueError"""
        from managers.session_manager import session_manager
        import sys

        from unittest.mock import MagicMock
        mock_db = MagicMock()
        mock_db.session_get.return_value = {"session_id": "test", "status": "raw"}
        sm_module = sys.modules["managers.session_manager"]
        monkeypatch.setattr(sm_module, "database_manager", mock_db)

        with pytest.raises(ValueError, match="invalid status transition"):
            session_manager.update_session("test", {"status": "approved"})


class TestApplyReview:
    """apply_review 审批落库唯一入口（状态流转校验 + 原子更新 + 审计）"""

    def test_apply_review_success_curated_to_approved(self, args_with_db_path):
        from core import database_manager
        from core.constants import SessionStatus
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        session_manager.create_session({"session_id": "rev-1"})
        session_manager.update_session("rev-1", {"status": SessionStatus.CURATED.value})

        result = session_manager.apply_review(
            "rev-1", SessionStatus.APPROVED, "approve", notes="ok", score=4
        )

        assert "error" not in result
        assert result["status"] == SessionStatus.APPROVED.value
        assert result["quality_manual_score"] == 4

    def test_apply_review_missing_session(self, args_with_db_path):
        from core import database_manager
        from core.constants import SessionStatus
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        result = session_manager.apply_review("no-such-id", SessionStatus.APPROVED, "approve")
        assert result == {"session_id": "no-such-id", "error": "session not found"}

    def test_apply_review_invalid_transition(self, args_with_db_path):
        """raw -> approved 不在流转表内，应拒绝并返回错误"""
        from core import database_manager
        from core.constants import SessionStatus
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        session_manager.create_session({"session_id": "rev-2"})

        result = session_manager.apply_review("rev-2", SessionStatus.APPROVED, "approve")
        assert result == {"session_id": "rev-2", "error": "invalid status transition"}

    def test_apply_review_score_falls_back_to_existing(self, args_with_db_path):
        """score 缺省时沿用现有 quality_manual_score"""
        from core import database_manager
        from core.constants import SessionStatus
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        session_manager.create_session({"session_id": "rev-3"})
        session_manager.update_session("rev-3", {
            "status": SessionStatus.CURATED.value,
            "quality_manual_score": 3,
        })

        result = session_manager.apply_review("rev-3", SessionStatus.REJECTED, "reject")

        assert "error" not in result
        assert result["quality_manual_score"] == 3


class TestValidStatusTransitionsShape:
    """状态流转表枚举化后形状保持（spec T1 契约测试）"""

    def test_shape_preserved(self):
        from managers.session_manager import VALID_STATUS_TRANSITIONS

        assert {
            s.value: [x.value for x in v]
            for s, v in VALID_STATUS_TRANSITIONS.items()
        } == {
            "raw": ["curated"],
            "curated": ["approved", "rejected"],
            "approved": ["rejected"],
            "rejected": ["approved"],
        }


class TestDeleteSessionFileCleanup:
    """delete_session 承接物理文件删除（DB 层不再删文件）"""

    def test_delete_removes_db_record_and_file(self, args_with_db_path, tmp_path):
        from core import database_manager
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        session_file = tmp_path / "session.json"
        session_file.write_text("{}", encoding="utf-8")

        created = session_manager.create_session({
            "session_id": "sess-del-1",
            "file_path": str(session_file),
        })
        assert created is not None

        assert session_manager.delete_session("sess-del-1") is True
        assert database_manager.session_get("sess-del-1") is None
        assert not session_file.exists()

    def test_delete_missing_file_returns_true(self, args_with_db_path):
        from core import database_manager
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        session_manager.create_session({
            "session_id": "sess-del-2",
            "file_path": "/nonexistent/path/session.json",
        })

        assert session_manager.delete_session("sess-del-2") is True

    def test_delete_unknown_session_returns_false(self, args_with_db_path):
        from core import database_manager
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        assert session_manager.delete_session("no-such-id") is False
