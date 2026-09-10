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
        monkeypatch.setattr(session_manager, "apply_review", lambda *args, **kwargs: {})

        result = self.manager.evaluate_session("test")

        assert result["score"] == 5
        assert result["is_high_value"] is True
        assert updates_list[0]["quality_auto_score"] == 5

    def test_score_hook_without_tools_used_falls_back_to_content(self, args_minimal, monkeypatch):
        """窄钩子只返回 score 时，tools_used 应回退到 content 值（不被写空）"""
        from core.hook_manager import hook_manager
        from managers import session_manager

        self.manager.init(args_minimal)

        content = {"messages": [1] * 5, "tools_used": ["read_file", "grep"]}

        monkeypatch.setattr(session_manager, "get_session",
            lambda sid: {"session_id": sid, "status": "raw", "content": content})

        updates_list = []

        def mock_update(session_id, updates, operator=None):
            updates_list.append(updates)
            return {"session_id": session_id, **updates}

        monkeypatch.setattr(session_manager, "update_session", mock_update)
        monkeypatch.setattr(session_manager, "apply_review", lambda *a, **k: {})

        def score_hook(self_, content_):
            return {"score": 2}

        hook_manager.register("curator_manager_score_before", score_hook)
        try:
            result = self.manager.evaluate_session("test")
        finally:
            hook_manager.unregister("curator_manager_score_before", score_hook)

        assert updates_list[0]["tools_used"] == ["read_file", "grep"]
        assert result["tools_used"] == ["read_file", "grep"]

    def test_evaluate_session_auto_approves_high_value(self, args_minimal, monkeypatch):
        """高分会话应触发自动审批（经 session_manager.apply_review 统一入口）"""
        from managers import session_manager

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

        apply_calls = []

        def mock_apply(session_id, target_status, action, notes=None, score=None):
            apply_calls.append({
                "session_id": session_id,
                "target_status": target_status,
                "action": action,
                "notes": notes,
                "score": score,
            })
            return {"session_id": session_id}

        monkeypatch.setattr(session_manager, "apply_review", mock_apply)

        result = self.manager.evaluate_session("test")
        assert result["auto_approved"] is True
        assert len(apply_calls) == 1
        assert apply_calls[0]["target_status"].value == "approved"
        assert apply_calls[0]["action"] == "auto_approve"
        assert apply_calls[0]["score"] == 5
