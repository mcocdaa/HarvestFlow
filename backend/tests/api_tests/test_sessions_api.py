# @file backend/tests/api_tests/test_sessions_api.py
# @brief Session API 路由层测试（TestClient 直测）
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


class TestSessionCRUD:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/sessions")
        assert resp.status_code == 200
        assert resp.json()["sessions"] == []

    def test_import_and_get(self, client, make_session_file):
        path = make_session_file("api-test-001")
        resp = client.post("/api/v1/collector/import", params={"file_path": path})
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "api-test-001"

        resp = client.get("/api/v1/sessions/api-test-001")
        assert resp.status_code == 200
        assert resp.json()["session"]["status"] == "raw"

    def test_import_missing_file(self, client):
        resp = client.post("/api/v1/collector/import", params={"file_path": "/nonexistent/x.jsonl"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Failed to import session"

    def test_import_requires_file_path(self, client):
        resp = client.post("/api/v1/collector/import")
        assert resp.status_code == 422

    def test_get_not_found(self, client):
        resp = client.get("/api/v1/sessions/nope")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found"

    def test_update_status(self, client, make_session_file):
        path = make_session_file("api-test-002")
        client.post("/api/v1/collector/import", params={"file_path": path})
        resp = client.patch("/api/v1/sessions/api-test-002", json={"status": "curated"})
        assert resp.status_code == 200
        assert resp.json()["session"]["status"] == "curated"

    def test_update_invalid_transition_409(self, client, make_session_file):
        path = make_session_file("api-test-003")
        client.post("/api/v1/collector/import", params={"file_path": path})
        resp = client.patch("/api/v1/sessions/api-test-003", json={"status": "approved"})
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Invalid status transition"

    def test_delete_removes_session(self, client, make_session_file):
        path = make_session_file("api-test-004")
        client.post("/api/v1/collector/import", params={"file_path": path})
        resp = client.delete("/api/v1/sessions/api-test-004")
        assert resp.status_code == 204

        resp = client.get("/api/v1/sessions/api-test-004")
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v1/sessions/nope")
        assert resp.status_code == 404

    def test_stats(self, client, make_session_file):
        path = make_session_file("api-test-005")
        client.post("/api/v1/collector/import", params={"file_path": path})
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        assert resp.json()["total_sessions"] == 1
        assert resp.json()["raw_sessions"] == 1

    def test_content_endpoint(self, client, make_session_file):
        path = make_session_file("api-test-006")
        client.post("/api/v1/collector/import", params={"file_path": path})
        resp = client.get("/api/v1/sessions/api-test-006/content")
        assert resp.status_code == 200
        assert resp.json()["content"]["session_id"] == "api-test-006"
