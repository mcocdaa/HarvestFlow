# @file backend/tests/plugins_tests/test_openclaw_curator.py
# @brief OpenClaw 审核器短路钩子测试
# @create 2026-08-11

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core import database_manager  # noqa: E402
from core.hook_manager import hook_manager  # noqa: E402
from managers.curator_manager import curator_manager  # noqa: E402
from managers.session_manager import session_manager  # noqa: E402


@pytest.fixture(autouse=True)
def clean_hooks():
    """每个用例后清理钩子，避免污染其他测试"""
    yield
    hook_manager.clear()


@pytest.fixture
def db(args_with_db_path):
    database_manager.init(args_with_db_path)
    yield database_manager
    database_manager.close()


@pytest.fixture
def curated_setup(db):
    """注册 openclaw curator 钩子并启用 curator

    clean_hooks 在每个用例后清空钩子，而 import 只执行一次（模块缓存），
    因此这里 reload hooks 模块强制重新执行装饰器注册。
    """
    import importlib

    import plugins.curators.openclaw.hooks as oc_hooks
    importlib.reload(oc_hooks)

    curator_manager.enabled = True
    curator_manager.auto_approve_threshold = 4
    yield
    curator_manager.enabled = True
    curator_manager.auto_approve_threshold = 4


def make_raw_session(db, session_id="oc-1", **content_extra):
    """创建 raw 状态会话（content 为 OpenClaw collector 输出快照）"""
    content = {
        "session_id": session_id,
        "agent_id": "backend_dev",
        "messages": [
            {"role": "user", "content": "fix the bug"},
            {"role": "assistant", "content": "I will fix it", "tool_calls": [
                {"type": "tool_use", "name": "read_file"},
            ]},
            {"role": "assistant", "content": "```python\nprint(1)\n```", "tool_calls": [
                {"type": "tool_use", "name": "write_file"},
            ]},
            {"role": "assistant", "content": "fixed", "tool_calls": [
                {"type": "tool_use", "name": "run_tests"},
            ]},
        ],
        "tools_used": ["read_file", "write_file", "run_tests"],
        "has_tool_calls": True,
        "message_count": 20,
        **content_extra,
    }
    return session_manager.create_session({
        "session_id": session_id,
        "file_path": f"/tmp/{session_id}.jsonl",
        "content": content,
        "status": "raw",
    })


def make_low_value_session(db, session_id="oc-low"):
    """低价值会话：无工具调用/无代码块/消息少 → OpenClaw 评分 2 分（< 阈值 3，不 auto_approve）"""
    content = {
        "session_id": session_id,
        "agent_id": "backend_dev",
        "messages": [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ],
        "tools_used": [],
        "has_tool_calls": False,
        "message_count": 2,
    }
    return session_manager.create_session({
        "session_id": session_id,
        "file_path": f"/tmp/{session_id}.jsonl",
        "content": content,
        "status": "raw",
    })


class TestOpenClawCuratorHook:
    def test_import_registers_hook(self):
        import plugins.curators.openclaw  # noqa: F401

        assert "curator_manager_evaluate_before" in hook_manager._hooks

    def test_short_circuit_evaluates_and_writes_db(self, db, curated_setup):
        make_low_value_session(db, "oc-1")

        result = curator_manager.evaluate_session("oc-1")

        assert result["session_id"] == "oc-1"
        assert result["score"] == 2                       # openclaw 基础分
        assert "score_reasons" in result                  # openclaw 附加字段
        assert result["auto_approved"] is False
        session = db.session_get("oc-1")
        assert session["status"] == "curated"             # 低分不 auto_approve
        assert session["quality_auto_score"] == 2
        assert session["tags"]

    def test_high_value_auto_approves(self, db, curated_setup):
        make_raw_session(db, "oc-hi", message_count=25)

        result = curator_manager.evaluate_session("oc-hi")

        # 高分内容（工具调用+决策链+代码块+消息数）→ openclaw 评分 ≥ 3 → auto_approve
        assert result["score"] == 5
        assert result["auto_approved"] is True
        assert db.session_get("oc-hi")["status"] == "approved"

    def test_not_raw_returns_error(self, db, curated_setup):
        make_raw_session(db, "oc-2")
        db.session_update("oc-2", {"status": "curated"})

        result = curator_manager.evaluate_session("oc-2")
        assert result == {"session_id": "oc-2", "error": "session is not in raw status"}

    def test_missing_session_returns_error(self, db, curated_setup):
        result = curator_manager.evaluate_session("no-such")
        assert result == {"session_id": "no-such", "error": "session not found"}

    def test_disabled_returns_error(self, db, curated_setup):
        make_raw_session(db, "oc-3")
        curator_manager.enabled = False

        result = curator_manager.evaluate_session("oc-3")
        assert result == {"session_id": "oc-3", "error": "curator disabled"}

    def test_exception_falls_back_to_builtin(self, db, curated_setup, monkeypatch):
        make_raw_session(db, "oc-fb")
        curator_manager.auto_approve_threshold = 5        # 内置评分 4 分 < 5 → 不 auto_approve，状态停在 curated

        def boom(*a, **k):
            raise RuntimeError("boom")

        # 注意：hooks.py 是 `from ...backend import get_curator` 导入（绑定副本），
        # 必须 patch hooks 模块中的引用，patch backend 模块无效
        monkeypatch.setattr("plugins.curators.openclaw.hooks.get_curator", boom)

        result = curator_manager.evaluate_session("oc-fb")

        # 不短路 → 内置评分执行（返回结构无 score_reasons）
        assert "score_reasons" not in result
        assert "score" in result
        assert result["auto_approved"] is False
        assert db.session_get("oc-fb")["status"] == "curated"
