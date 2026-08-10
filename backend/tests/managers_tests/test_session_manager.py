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
