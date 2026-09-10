# @file backend/tests/plugins_tests/test_openclaw_collector.py
# @brief OpenClaw 采集器插件测试（真实格式兼容性回归）
# @create 2026-09-10

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from plugins.collectors.openclaw.backend import OpenClawCollector  # noqa: E402


def write_jsonl(path: Path, records):
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
        encoding="utf-8",
    )


NESTED_V3_RECORDS = [
    {"type": "session", "version": 3, "id": "sess-abc-123", "timestamp": "2026-03-11T10:31:05Z"},
    {"type": "model_change", "id": "m1", "provider": "moonshot", "modelId": "kimi-k2.5"},
    {"type": "message", "id": "e1", "message": {
        "role": "user", "content": [{"type": "text", "text": "帮我看下登录报错"}]}},
    {"type": "message", "id": "e2", "message": {
        "role": "assistant", "content": [
            {"type": "tool_use", "name": "read_file", "input": {"path": "src/login.py"}},
        ]}},
    {"type": "message", "id": "e3", "message": {
        "role": "user", "content": [
            {"type": "tool_result", "content": "NoneType has no attribute id"},
        ]}},
    {"type": "message", "id": "e4", "message": {
        "role": "assistant", "content": [{"type": "text", "text": "已修复"}]}},
]

FLAT_RECORDS = [
    {"role": "user", "content": "hi", "sessionId": "flat-1"},
    {"role": "assistant", "content": [{"type": "tool_use", "name": "grep"}], "sessionId": "flat-1"},
]


class TestParseNestedFormat:
    """OpenClaw v3 嵌套格式：{"type": "message", "message": {...}}"""

    def test_parse_nested_v3(self, tmp_path):
        agents_dir = tmp_path / "agents"
        sessions_dir = agents_dir / "req_analyst" / "sessions"
        sessions_dir.mkdir(parents=True)
        f = sessions_dir / "abc.jsonl"
        write_jsonl(f, NESTED_V3_RECORDS)

        collector = OpenClawCollector({"min_message_count": 1})
        result = collector.parse(str(f))

        assert result is not None
        assert result["session_id"] == "sess-abc-123"
        assert result["agent_id"] == "req_analyst"
        assert result["message_count"] == 4
        assert all(m["content"] for m in result["messages"])
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "帮我看下登录报错"
        assert result["tools_used"] == ["read_file"]
        assert result["has_tool_calls"] is True
        # tool_use / tool_result 保留在消息级 tool_calls
        assert result["messages"][1]["tool_calls"][0]["type"] == "tool_use"
        assert result["messages"][2]["tool_calls"][0]["type"] == "tool_result"


class TestParseFlatFormat:
    """扁平格式向后兼容"""

    def test_parse_flat(self, tmp_path):
        f = tmp_path / "flat.jsonl"
        write_jsonl(f, FLAT_RECORDS)

        collector = OpenClawCollector({"min_message_count": 1})
        result = collector.parse(str(f))

        assert result is not None
        assert result["session_id"] == "flat-1"
        assert result["message_count"] == 2
        assert result["tools_used"] == ["grep"]
        assert result["has_tool_calls"] is True


class TestMinMessageCount:
    def test_below_threshold_returns_none(self, tmp_path):
        f = tmp_path / "abc.jsonl"
        write_jsonl(f, NESTED_V3_RECORDS)

        collector = OpenClawCollector({"min_message_count": 5})
        assert collector.parse(str(f)) is None


class TestScanWindowsPathFallback:
    """Windows sessionFile 路径在 POSIX 上回退到本机同名文件"""

    def test_scan_falls_back_to_local_basename(self, tmp_path):
        agents_dir = tmp_path / "agents"
        sessions_dir = agents_dir / "req_analyst" / "sessions"
        sessions_dir.mkdir(parents=True)
        local_file = sessions_dir / "abc.jsonl"
        write_jsonl(local_file, NESTED_V3_RECORDS)
        (sessions_dir / "sessions.json").write_text(json.dumps({
            "agent:req_analyst:main": {
                "sessionFile": "C:\\Users\\20211\\.openclaw\\agents\\req_analyst\\sessions\\abc.jsonl",
                "model": "kimi-k2.5",
                "updatedAt": 1773221755174,
                "label": "main",
            },
        }), encoding="utf-8")

        collector = OpenClawCollector({
            "agents_dir": str(agents_dir),
            "target_agents": ["req_analyst"],
        })
        files = collector.scan()

        assert files == [str(local_file)]

    def test_scan_missing_local_file_warns(self, tmp_path):
        agents_dir = tmp_path / "agents"
        sessions_dir = agents_dir / "req_analyst" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "sessions.json").write_text(json.dumps({
            "agent:req_analyst:main": {
                "sessionFile": "C:\\Users\\20211\\.openclaw\\agents\\req_analyst\\sessions\\missing.jsonl",
            },
        }), encoding="utf-8")

        collector = OpenClawCollector({
            "agents_dir": str(agents_dir),
            "target_agents": ["req_analyst"],
        })
        assert collector.scan() == []


class TestExtractMetadata:
    """绝对路径下也应能从 sessions.json 匹配到元数据"""

    def test_metadata_from_sessions_json(self, tmp_path):
        agents_dir = tmp_path / "agents"
        sessions_dir = agents_dir / "req_analyst" / "sessions"
        sessions_dir.mkdir(parents=True)
        local_file = sessions_dir / "abc.jsonl"
        write_jsonl(local_file, NESTED_V3_RECORDS)
        (sessions_dir / "sessions.json").write_text(json.dumps({
            "agent:req_analyst:main": {
                "sessionFile": "C:\\Users\\20211\\.openclaw\\agents\\req_analyst\\sessions\\abc.jsonl",
                "model": "kimi-k2.5",
                "updatedAt": 1773221755174,
                "label": "main",
            },
        }), encoding="utf-8")

        collector = OpenClawCollector({"min_message_count": 1})
        result = collector.parse(str(local_file))

        assert result["metadata"]["model"] == "kimi-k2.5"
        assert result["metadata"]["updated_at"] == 1773221755174
        assert result["metadata"]["label"] == "main"
