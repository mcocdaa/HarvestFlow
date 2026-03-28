# @file backend/tests/managers_tests/curator_manager/test_bulk_evaluate.py
# @brief CuratorManager 批量评估测试
# @create 2026-03-27

from managers.curator_manager import CuratorManager


class TestCuratorManagerBulkEvaluate:
    def setup_method(self):
        self.manager = CuratorManager()

    def test__move_to_curated_session_not_found(self, args_minimal, monkeypatch):
        from managers import session_manager

        self.manager.init(args_minimal)

        def mock_get(session_id):
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        self.manager._move_to_curated("test")

        assert True

    def test__move_to_curated_no_source_path(self, args_minimal, monkeypatch):
        from managers import session_manager

        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id}

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        self.manager._move_to_curated("test")

        assert True

    def test__move_to_curated_source_not_exists(self, args_minimal, monkeypatch):
        from managers import session_manager

        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id, "file_path": "/nonexistent/file.json"}

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        self.manager._move_to_curated("test")

        assert True

    def test_evaluate_all_evaluates_all_raw_sessions(self, args_minimal, monkeypatch):
        from core import database_manager

        self.manager.init(args_minimal)

        original = database_manager.session_get_by_status
        database_manager.session_get_by_status = lambda status: [
            {"session_id": "1"},
            {"session_id": "2"},
            {"session_id": "3"}
        ]

        called = []
        def mock_evaluate(session_id):
            called.append(session_id)
            return {"session_id": session_id, "is_high_value": True}

        monkeypatch.setattr(self.manager, "evaluate_session", mock_evaluate)

        try:
            result = self.manager.evaluate_all()

            assert result["total"] == 3
            assert result["high_value"] == 3
            assert len(called) == 3
        finally:
            database_manager.session_get_by_status = original

    def test_evaluate_all_counts_low_value(self, args_minimal, monkeypatch):
        from core import database_manager

        self.manager.init(args_minimal)

        original = database_manager.session_get_by_status
        database_manager.session_get_by_status = lambda status: [
            {"session_id": "1"},
            {"session_id": "2"}
        ]

        called_count = 0
        def mock_evaluate(session_id):
            nonlocal called_count
            called_count += 1
            if called_count == 1:
                return {"session_id": session_id, "is_high_value": True}
            else:
                return {"session_id": session_id, "is_high_value": False}

        monkeypatch.setattr(self.manager, "evaluate_session", mock_evaluate)

        try:
            result = self.manager.evaluate_all()

            assert result["total"] == 2
            assert result["high_value"] == 1
            assert result["low_value"] == 1
        finally:
            database_manager.session_get_by_status = original

    def test__move_to_curated_handles_copy_exception(self, args_minimal, monkeypatch):
        from managers import session_manager

        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id, "file_path": "/nonexistent/test.json"}

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        called_update = False
        def mock_update(session_id, updates):
            nonlocal called_update
            called_update = True
            return None

        monkeypatch.setattr(session_manager, "update_session", mock_update)

        self.manager._move_to_curated("test")

        assert called_update is False
