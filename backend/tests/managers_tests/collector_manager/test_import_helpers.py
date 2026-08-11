# @file backend/tests/managers_tests/collector_manager/test_import_helpers.py
# @brief CollectorManager import 辅助方法测试
# @create 2026-08-10

from managers.collector_manager import CollectorManager


class TestBuildSessionRecord:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_build_session_record_attaches_file_path(self):
        session_data = {"session_id": "test-session", "messages": []}

        record = self.manager._build_session_record("/path/to/file.json", session_data)

        assert record["file_path"] == "/path/to/file.json"

    def test_build_session_record_content_is_original_snapshot(self):
        session_data = {"session_id": "test-session", "messages": []}

        record = self.manager._build_session_record("/path/to/file.json", session_data)

        # content 保存原始数据快照，不含 file_path 键
        assert record["content"] == {"session_id": "test-session", "messages": []}
        assert "file_path" not in record["content"]

    def test_build_session_record_does_not_mutate_input(self):
        session_data = {"session_id": "test-session", "messages": []}
        original = dict(session_data)

        self.manager._build_session_record("/path/to/file.json", session_data)

        assert session_data == original
        assert "file_path" not in session_data
        assert "content" not in session_data


class TestCreateSession:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_create_session_returns_session_id(self, monkeypatch):
        from managers import session_manager

        def mock_create(session_data):
            return session_data

        monkeypatch.setattr(session_manager, "create_session", mock_create)

        record = {"session_id": "test-session", "messages": []}

        result = self.manager._create_session(record)

        assert result == "test-session"

    def test_create_session_returns_none_when_create_raises(self, monkeypatch):
        from managers import session_manager

        def mock_create(session_data):
            raise RuntimeError("Database connection failed")

        monkeypatch.setattr(session_manager, "create_session", mock_create)

        record = {"session_id": "test-session", "messages": []}

        result = self.manager._create_session(record)

        assert result is None
