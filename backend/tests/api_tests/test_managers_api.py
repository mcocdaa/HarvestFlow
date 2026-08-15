# @file backend/tests/api_tests/test_managers_api.py
# @brief Curator/Reviewer/Exporter/Plugins API 路由层测试（TestClient 直测）
# @create 2026-08-15

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.hook_manager import hook_manager


@pytest.fixture
def client(args_with_db_path, tmp_path, monkeypatch):
    from main import create_app, init_app

    from core import plugin_manager

    args = args_with_db_path
    args.db_path = str(tmp_path / "test.db")
    args.data_dir = str(tmp_path / "data")
    monkeypatch.setattr(plugin_manager, "plugins_dir", Path(str(tmp_path / "plugins")).resolve())
    monkeypatch.setattr(plugin_manager, "plugins", {})
    monkeypatch.setattr(plugin_manager, "loaded_plugins", {})
    monkeypatch.setattr(plugin_manager, "plugin_modules", {})
    (tmp_path / "plugins").mkdir()

    hook_manager.clear()
    init_app(args)
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_session_file(tmp_path):
    def _make(session_id, role="user", content="hello"):
        path = tmp_path / f"{session_id}.jsonl"
        path.write_text(json.dumps({
            "type": "message",
            "id": session_id,
            "message": {
                "role": role,
                "content": [{"type": "text", "text": content}],
            },
        }) + "\n", encoding="utf-8")
        return str(path)

    return _make


@pytest.fixture
def import_session(client, make_session_file):
    def _import(session_id, role="user", content="hello"):
        client.post(
            "/api/v1/collector/import",
            params={"file_path": make_session_file(session_id, role, content)},
        )

    return _import


class TestCuratorAPI:
    def test_evaluate_not_found(self, client):
        resp = client.post("/api/v1/curator/evaluate/nope")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "session not found"

    def test_evaluate_and_status(self, client, import_session):
        import_session("cur-001")
        resp = client.post("/api/v1/curator/evaluate/cur-001")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["session_id"] == "cur-001"

        resp = client.get("/api/v1/curator/status")
        assert resp.status_code == 200
        assert "enabled" in resp.json()

    def test_evaluate_all(self, client, import_session):
        import_session("cur-002")
        import_session("cur-003")
        resp = client.post("/api/v1/curator/evaluate-all")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
        assert resp.json()["low_value"] == 2

    def test_reject_evaluate_not_raw(self, client, import_session):
        import_session("cur-004")
        client.post("/api/v1/curator/evaluate/cur-004")
        resp = client.post("/api/v1/curator/evaluate/cur-004")
        assert resp.status_code == 409
        assert resp.json()["detail"] == "session is not in raw status"


class TestReviewerAPI:
    def test_pending_flow(self, client, import_session):
        import_session("rev-001")
        client.post("/api/v1/curator/evaluate/rev-001")

        resp = client.get("/api/v1/reviewer/pending")
        assert resp.status_code == 200
        assert resp.json()["sessions"][0]["session_id"] == "rev-001"

    def test_approve_and_audit_log(self, client, import_session):
        import_session("rev-002")
        client.post("/api/v1/curator/evaluate/rev-002")

        resp = client.post("/api/v1/reviewer/approve/rev-002")
        assert resp.status_code == 200
        assert resp.json()["session"]["status"] == "approved"

        resp = client.get("/api/v1/reviewer/audit-logs")
        logs = resp.json()["logs"]
        assert logs[0]["session_id"] == "rev-002"
        assert logs[0]["action"] == "approve"

    def test_reject(self, client, import_session):
        import_session("rev-003")
        client.post("/api/v1/curator/evaluate/rev-003")

        resp = client.post("/api/v1/reviewer/reject/rev-003")
        assert resp.status_code == 200
        assert resp.json()["session"]["status"] == "rejected"

    def test_batch_approve(self, client, import_session):
        import_session("rev-004")
        import_session("rev-005")
        client.post("/api/v1/curator/evaluate/rev-004")
        client.post("/api/v1/curator/evaluate/rev-005")

        resp = client.post(
            "/api/v1/reviewer/batch-approve",
            json=["rev-004", "rev-005"],
        )
        assert resp.status_code == 200
        assert resp.json()["success"] == 2


class TestExporterAPI:
    def test_formats(self, client):
        resp = client.get("/api/v1/exporter/formats")
        assert resp.status_code == 200
        assert resp.json()["formats"] == ["sharegpt", "alpaca"]

    def test_export_without_data(self, client):
        resp = client.post("/api/v1/exporter/export", json={})
        assert resp.status_code == 400

    def test_export_and_history(self, client, import_session):
        import_session("exp-001")
        client.post("/api/v1/curator/evaluate/exp-001")
        client.post("/api/v1/reviewer/approve/exp-001")

        resp = client.post("/api/v1/exporter/export", json={"format": "sharegpt"})
        assert resp.status_code == 200
        assert resp.json()["record_count"] == 1

        resp = client.get("/api/v1/exporter/history")
        assert resp.status_code == 200
        assert resp.json()["exports"][0]["export_format"] == "sharegpt"


class TestPluginsAPI:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/plugins")
        assert resp.status_code == 200
        assert resp.json()["plugins"] == []

    def test_enable_unknown_404(self, client):
        resp = client.post("/api/v1/plugins/enable", params={"key": "unknown/plugin"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Plugin not found"

    def test_disable_unknown_404(self, client):
        resp = client.post("/api/v1/plugins/disable", params={"key": "unknown/plugin"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Plugin not found"

    def test_toggle_with_inline_comment(self, client, tmp_path, monkeypatch):
        """key 行带同行注释时 enable/disable 应仍生效（回归测试）"""
        from core import plugin_manager

        registry = tmp_path / "plugins" / "plugins.yaml"
        registry.write_text(
            "plugins:\n"
            "  collectors/openclaw:   # OpenClaw 会话采集器\n"
            "    enabled: true\n",
            encoding="utf-8",
        )
        (tmp_path / "plugins" / "collectors" / "openclaw").mkdir(parents=True)
        (tmp_path / "plugins" / "collectors" / "openclaw" / "plugin.yaml").write_text(
            'name: "OpenClaw Collector"\ntype: "collector"\nversion: "1.0.0"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(plugin_manager, "plugins_dir", Path(str(tmp_path / "plugins")).resolve())
        monkeypatch.setattr(plugin_manager, "plugins", plugin_manager._load_registry())

        resp = client.post("/api/v1/plugins/disable", params={"key": "collectors/openclaw"})
        assert resp.status_code == 200
        content = registry.read_text(encoding="utf-8")
        assert "enabled: false" in content
        assert "# OpenClaw 会话采集器" in content

        resp = client.post("/api/v1/plugins/enable", params={"key": "collectors/openclaw"})
        assert resp.status_code == 200
        assert "enabled: true" in registry.read_text(encoding="utf-8")
