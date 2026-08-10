# @file backend/tests/managers_tests/curator_manager/test_evaluate.py
# @brief CuratorManager 会话评估测试
# @create 2026-03-27


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
            return {"session_id": session_id, "status": "raw", "file_path": "/nonexistent.json"}

        def mock_get_content(session_id):
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)
        monkeypatch.setattr(session_manager, "get_session_content", mock_get_content)

        result = self.manager.evaluate_session("test")

        assert "error" in result
        assert result["error"] == "content not found"

    def test_evaluate_session_calculates_score(self, args_minimal, monkeypatch):
        from managers import session_manager
        from core import database_manager

        self.manager.init(args_minimal)

        content = {
            "messages": [1] * 15,
            "tool_calls": [{"name": "tool1"}],
            "final_output": "result"
        }

        def mock_get(session_id):
            return {"session_id": session_id, "status": "raw", "file_path": "/test.json", "content": content}

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        updates_list = []
        def mock_update(session_id, updates):
            updates_list.append(updates)
            return {"session_id": session_id, **updates}

        monkeypatch.setattr(session_manager, "update_session", mock_update)
        monkeypatch.setattr(database_manager, "session_review_apply", lambda *args, **kwargs: None)

        result = self.manager.evaluate_session("test")

        assert result["score"] == 5
        assert result["is_high_value"] is True
        assert updates_list[0]["quality_auto_score"] == 5

    def test_evaluate_session_auto_approves_high_value(self, args_minimal, monkeypatch):
        """高分会话应触发自动审批"""
        from managers import session_manager
        from core import database_manager

        self.manager.init(args_minimal)
        self.manager.auto_approve_threshold = 3  # low threshold

        content = {
            "messages": [1] * 15,
            "tool_calls": [{"name": "t1"}],
            "final_output": "result"
        }

        monkeypatch.setattr(session_manager, "get_session",
            lambda sid: {"session_id": sid, "status": "raw", "content": content})
        monkeypatch.setattr(session_manager, "update_session",
            lambda sid, up: {"session_id": sid, **up})

        apply_called = []

        def mock_apply(session_id, status, score, action, notes=None):
            apply_called.append(True)
            return {"session_id": session_id}

        monkeypatch.setattr(database_manager, "session_review_apply", mock_apply)

        result = self.manager.evaluate_session("test")
        assert result["auto_approved"] is True
        assert len(apply_called) == 1
