# @file backend/tests/managers_tests/curator_manager/test_bulk_evaluate.py
# @brief CuratorManager 批量评估测试
# @create 2026-03-27

from managers.curator_manager import CuratorManager


class TestCuratorManagerBulkEvaluate:
    def setup_method(self):
        self.manager = CuratorManager()

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

    def test_evaluate_all_filters_error_results(self, args_minimal, monkeypatch):
        """P1.8: evaluate_all should exclude error results from high_value/low_value counts."""
        from core import database_manager

        self.manager.init(args_minimal)

        original = database_manager.session_get_by_status
        database_manager.session_get_by_status = lambda status: [
            {"session_id": "1"},
            {"session_id": "2"},
            {"session_id": "3"},
        ]

        call_idx = 0
        def mock_evaluate(session_id):
            nonlocal call_idx
            call_idx += 1
            if call_idx == 1:
                return {"session_id": session_id, "is_high_value": True}
            elif call_idx == 2:
                return {"session_id": session_id, "error": "session not found"}
            else:
                return {"session_id": session_id, "is_high_value": False}

        monkeypatch.setattr(self.manager, "evaluate_session", mock_evaluate)

        try:
            result = self.manager.evaluate_all()

            assert result["total"] == 3
            assert result["high_value"] == 1
            assert result["low_value"] == 1
        finally:
            database_manager.session_get_by_status = original
