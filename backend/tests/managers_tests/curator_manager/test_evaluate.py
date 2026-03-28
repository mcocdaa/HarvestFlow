# @file backend/tests/managers_tests/curator_manager/test_evaluate.py
# @brief CuratorManager 会话评估测试
# @create 2026-03-27

import pytest

from managers.curator_manager import CuratorManager


class TestCuratorManagerEvaluate:
    def setup_method(self):
        self.manager = CuratorManager()

    def test_evaluate_session_session_not_found(self, args_minimal, monkeypatch):
        from managers import session_manager

        self.manager.init(args_minimal)

        def mock_get(session_id):
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        result = self.manager.evaluate_session("nonexistent")

        assert "error" in result
        assert result["error"] == "session not found"

    def test_evaluate_session_content_not_found(self, args_minimal, monkeypatch):
        from managers import session_manager

        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id, "file_path": "/nonexistent.json"}

        def mock_get_content(session_id):
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)
        monkeypatch.setattr(session_manager, "get_session_content", mock_get_content)

        result = self.manager.evaluate_session("test")

        assert "error" in result
        assert result["error"] == "content not found"

    def test_evaluate_session_calculates_score(self, args_minimal, monkeypatch):
        from managers import session_manager

        self.manager.init(args_minimal)

        content = {
            "messages": [1] * 15,
            "tool_calls": [{"name": "tool1"}],
            "final_output": "result"
        }

        def mock_get(session_id):
            return {"session_id": session_id, "file_path": "/test.json"}

        def mock_get_content(session_id):
            return content

        monkeypatch.setattr(session_manager, "get_session", mock_get)
        monkeypatch.setattr(session_manager, "get_session_content", mock_get_content)

        called_updates = None
        def mock_update(session_id, updates):
            nonlocal called_updates
            called_updates = updates
            return {"session_id": session_id, **updates}

        monkeypatch.setattr(session_manager, "update_session", mock_update)

        result = self.manager.evaluate_session("test")

        assert result["score"] == 5
        assert result["is_high_value"] is True
        assert called_updates is not None
        assert called_updates["quality_auto_score"] == 5
