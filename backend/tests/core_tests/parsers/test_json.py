# @file backend/tests/core_tests/parsers/test_json.py
# @brief parse_json_file 单元测试
# @create 2026-08-10

import json
import re

from core.parsers import parse_json_file


class TestParseJson:
    def test_returns_dict_as_is(self, tmp_path):
        path = tmp_path / "session.json"
        data = {"session_id": "abc", "messages": [{"role": "user", "content": "hi"}]}
        path.write_text(json.dumps(data), encoding='utf-8')

        result = parse_json_file(str(path))
        assert result == data

    def test_generates_session_id_when_missing(self, tmp_path):
        path = tmp_path / "session.json"
        path.write_text(json.dumps({"messages": []}), encoding='utf-8')

        result = parse_json_file(str(path))
        assert result is not None
        assert re.match(r'^session_\d{8}_\d{6}_session\.json$', result["session_id"])

    def test_invalid_json_returns_none(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding='utf-8')
        assert parse_json_file(str(path)) is None

    def test_missing_file_returns_none(self, tmp_path):
        assert parse_json_file(str(tmp_path / "not_exist.json")) is None

    def test_empty_object_gets_session_id(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("{}", encoding='utf-8')
        result = parse_json_file(str(path))
        assert result is not None
        assert "session_id" in result
