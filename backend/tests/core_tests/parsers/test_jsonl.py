# @file backend/tests/core_tests/parsers/test_jsonl.py
# @brief parse_jsonl_file 单元测试
# @create 2026-08-10

import json

import pytest

from core.parsers import parse_jsonl_file


@pytest.fixture
def jsonl_file(tmp_path):
    """构造一个含多行 message 的 jsonl 文件"""

    def _make(content: str, name: str = "session.jsonl") -> str:
        path = tmp_path / name
        path.write_text(content, encoding='utf-8')
        return str(path)

    return _make


def _line(type_, id_=None, role=None, content=None):
    """构造一行 jsonl 记录"""
    record = {"type": type_}
    if id_:
        record["id"] = id_
    if role or content:
        record["message"] = {"role": role, "content": content}
    return json.dumps(record)


class TestParseJsonl:
    def test_parse_normal_messages(self, jsonl_file):
        content = "\n".join([
            _line("message", "s1", "user", "hello"),
            _line("message", None, "assistant", "hi there"),
        ]) + "\n"
        path = jsonl_file(content)
        result = parse_jsonl_file(path)

        assert result is not None
        assert result["session_id"] == "s1"
        assert result["message_count"] == 2
        assert result["messages"] == [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        assert result["has_tool_calls"] is False
        assert result["tools_used"] == []

    def test_content_string_form(self, jsonl_file):
        content = json.dumps({
            "type": "message",
            "id": "s1",
            "message": {"role": "user", "content": "plain string"},
        }) + "\n"
        path = jsonl_file(content)
        result = parse_jsonl_file(path)

        assert result["messages"] == [{"role": "user", "content": "plain string"}]

    def test_content_list_text_items_concatenated(self, jsonl_file):
        content = json.dumps({
            "type": "message",
            "id": "s1",
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": "part1 "},
                    {"type": "text", "text": "part2"},
                    {"type": "tool_use", "text": "ignored"},
                ],
            },
        }) + "\n"
        path = jsonl_file(content)
        result = parse_jsonl_file(path)

        assert result["messages"] == [{"role": "user", "content": "part1 part2"}]

    def test_bad_json_lines_skipped(self, jsonl_file):
        content = "\n".join([
            "this is not json",
            _line("message", "s1", "user", "ok"),
            "{broken json",
        ]) + "\n"
        path = jsonl_file(content)
        result = parse_jsonl_file(path)

        assert result is not None
        assert result["message_count"] == 1

    def test_empty_lines_skipped(self, jsonl_file):
        content = "\n\n\n" + _line("message", "s1", "user", "ok") + "\n\n"
        path = jsonl_file(content)
        result = parse_jsonl_file(path)

        assert result is not None
        assert result["message_count"] == 1

    def test_no_messages_returns_none(self, jsonl_file):
        content = json.dumps({"type": "other", "id": "s1"}) + "\n"
        path = jsonl_file(content)
        assert parse_jsonl_file(path) is None

    def test_no_session_id_returns_none(self, jsonl_file):
        content = _line("message", None, "user", "hello") + "\n"
        path = jsonl_file(content)
        assert parse_jsonl_file(path) is None

    def test_agent_id_extracted_from_agents_path(self, jsonl_file, tmp_path):
        nested = tmp_path / "agents" / "req_analyst"
        nested.mkdir(parents=True)
        path = nested / "s.jsonl"
        path.write_text(_line("message", "s1", "user", "hi") + "\n", encoding='utf-8')

        result = parse_jsonl_file(str(path))
        assert result["agent_id"] == "req_analyst"

    def test_no_agents_path_returns_none_agent_id(self, jsonl_file):
        path = jsonl_file(_line("message", "s1", "user", "hi") + "\n")
        result = parse_jsonl_file(path)
        assert result["agent_id"] is None

    def test_missing_file_returns_none(self, tmp_path):
        assert parse_jsonl_file(str(tmp_path / "not_exist.jsonl")) is None

    def test_empty_message_content_skipped(self, jsonl_file):
        content = "\n".join([
            _line("message", "s1", "user", ""),
            _line("message", None, "assistant", ""),
            _line("message", None, "user", "real"),
        ]) + "\n"
        path = jsonl_file(content)
        result = parse_jsonl_file(path)

        assert result["message_count"] == 1
        assert result["messages"] == [{"role": "user", "content": "real"}]
