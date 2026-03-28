# @file backend/tests/managers_tests/collector_manager/test_parsing.py
# @brief CollectorManager 文件解析测试
# @create 2026-03-27

import json

from managers.collector_manager import CollectorManager


class TestCollectorManagerParsing:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_parse_session_file_success_with_session_id(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"session_id": "my-session-id", "messages": []}
        with open(file_path, "w") as f:
            json.dump(data, f)

        result = self.manager.parse_session_file(str(file_path))

        assert result is not None
        assert result["session_id"] == "my-session-id"

    def test_parse_session_file_generates_session_id(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"messages": []}
        with open(file_path, "w") as f:
            json.dump(data, f)

        result = self.manager.parse_session_file(str(file_path))

        assert result is not None
        assert "session_id" in result
        assert result["session_id"].startswith("session_")

    def test_parse_session_file_invalid_json_returns_none(self, tmp_path):
        file_path = tmp_path / "bad.json"
        with open(file_path, "w") as f:
            f.write("bad json {{")

        result = self.manager.parse_session_file(str(file_path))

        assert result is None
