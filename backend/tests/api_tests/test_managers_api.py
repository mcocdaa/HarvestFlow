# @file backend/tests/api_tests/test_managers_api.py
# @brief Curator/Reviewer/Exporter/Plugins API 路由层测试（TestClient 直测）
# @create 2026-08-15

import json
import io
import zipfile
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
    """构造核心层可解析的标准 .json 会话文件（.jsonl 由采集器插件负责）"""
    def _make(session_id, role="user", content="hello"):
        path = tmp_path / f"{session_id}.json"
        path.write_text(json.dumps({
            "session_id": session_id,
            "messages": [{"role": role, "content": content}],
        }), encoding="utf-8")
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
    def test_approve_missing_session_404(self, client):
        """缺失会话应为 404（与 GET /sessions、curator 一致）"""
        resp = client.post("/api/v1/reviewer/approve/nope")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "session not found"

    def test_reject_missing_session_404(self, client):
        resp = client.post("/api/v1/reviewer/reject/nope")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "session not found"

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

    def test_extra_fields_from_hook(self, client):
        """审核插件经 after 钩子贡献扩展字段"""
        def extra_fields(result, self):
            return list(result) + [{"name": "use_case", "label": "使用场景", "type": "text"}]

        hook_manager.register("reviewer_manager_extra_fields_after", extra_fields)
        resp = client.get("/api/v1/reviewer/extra-fields")
        assert resp.status_code == 200
        assert resp.json()["fields"] == [{"name": "use_case", "label": "使用场景", "type": "text"}]

    def test_review_validation_hook_blocks(self, client, import_session):
        """before 钩子返回错误时短路审批（400）"""
        def block(self, session_id, target_status, action, notes=None, score=None, extras=None):
            return {"session_id": session_id, "error": "插件校验失败"}

        hook_manager.register("reviewer_manager_review_before", block)
        import_session("rev-block")
        client.post("/api/v1/curator/evaluate/rev-block")

        resp = client.post("/api/v1/reviewer/approve/rev-block")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "插件校验失败"

    def test_review_extras_persisted(self, client, tmp_path):
        """审批携带的 extras 存入 sessions.review_meta"""
        session_id = "rev-ext"
        session_file = tmp_path / f"{session_id}.json"
        session_file.write_text(json.dumps({
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "yo"},
            ],
        }), encoding="utf-8")
        client.post("/api/v1/collector/import", params={"file_path": str(session_file)})
        client.post(f"/api/v1/curator/evaluate/{session_id}")

        resp = client.post(
            f"/api/v1/reviewer/approve/{session_id}",
            json={"extras": {"use_case": "coding", "data_quality": "优秀"}},
        )
        assert resp.status_code == 200
        assert resp.json()["session"]["review_meta"] == {"use_case": "coding", "data_quality": "优秀"}


class TestCollectorWatchAPI:
    def test_watch_state_shape(self, client):
        resp = client.get("/api/v1/collector/watch-state")
        assert resp.status_code == 200
        body = resp.json()
        assert {"enabled", "running", "interval", "folders", "last_runs"} <= set(body.keys())

    def test_watch_start_stop(self, client):
        resp = client.post("/api/v1/collector/watch-start")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True
        assert resp.json()["running"] is True

        resp = client.post("/api/v1/collector/watch-stop")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
        assert resp.json()["running"] is False

    def test_watch_run_imports_folder(self, client, tmp_path):
        folder = tmp_path / "inbox"
        folder.mkdir()
        (folder / "auto-1.json").write_text(
            json.dumps({
                "session_id": "auto-1",
                "messages": [{"role": "user", "content": "hi"}],
            }),
            encoding="utf-8",
        )
        client.post("/api/v1/collector/watch-folder", params={"folder_path": str(folder)})

        resp = client.post("/api/v1/collector/watch-run")
        assert resp.status_code == 200
        first = resp.json()["results"][str(folder)]
        assert first["imported"] == 1

        # 再次运行：已导入的会话被跳过
        resp = client.post("/api/v1/collector/watch-run")
        second = resp.json()["results"][str(folder)]
        assert second["skipped"] == 1


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

    def test_download_export(self, client, import_session, tmp_path, monkeypatch):
        from managers.exporter_manager import exporter_manager

        monkeypatch.setattr(exporter_manager, "output_dir", str(tmp_path))
        import_session("dl-001")
        client.post("/api/v1/curator/evaluate/dl-001")
        client.post("/api/v1/reviewer/approve/dl-001")
        export_resp = client.post("/api/v1/exporter/export", json={"format": "sharegpt"})
        filename = export_resp.json()["filename"]

        resp = client.get("/api/v1/exporter/download", params={"filename": filename})
        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]
        assert resp.content

    def test_download_export_rejects_traversal(self, client, tmp_path, monkeypatch):
        from managers.exporter_manager import exporter_manager

        monkeypatch.setattr(exporter_manager, "output_dir", str(tmp_path))
        resp = client.get("/api/v1/exporter/download", params={"filename": "../app.db"})
        assert resp.status_code == 400

    def test_download_export_missing(self, client, tmp_path, monkeypatch):
        from managers.exporter_manager import exporter_manager

        monkeypatch.setattr(exporter_manager, "output_dir", str(tmp_path))
        resp = client.get("/api/v1/exporter/download", params={"filename": "none.jsonl"})
        assert resp.status_code == 404

    def test_download_export_zip(self, client, import_session, tmp_path, monkeypatch):
        from managers.exporter_manager import exporter_manager

        monkeypatch.setattr(exporter_manager, "output_dir", str(tmp_path))
        import_session("zip-001")
        client.post("/api/v1/curator/evaluate/zip-001")
        client.post("/api/v1/reviewer/approve/zip-001")
        export_resp = client.post("/api/v1/exporter/export", json={"format": "alpaca"})
        filename = export_resp.json()["filename"]

        resp = client.post("/api/v1/exporter/download-zip", json={"filenames": [filename]})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        with zipfile.ZipFile(io.BytesIO(resp.content)) as archive:
            assert archive.namelist() == [filename]

    def test_download_export_zip_empty(self, client):
        resp = client.post("/api/v1/exporter/download-zip", json={"filenames": []})
        assert resp.status_code == 400


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
