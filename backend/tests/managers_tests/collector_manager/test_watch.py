# @file backend/tests/managers_tests/collector_manager/test_watch.py
# @brief 目录监听：持久化、加载优先级、轮询执行与线程生命周期测试
# @create 2026-09-18

import json
import threading

from managers.collector_manager import CollectorManager


def _read_config(tmp_path):
    return json.loads((tmp_path / "watch_folders.json").read_text(encoding="utf-8"))


class TestWatchConfigPersistence:
    def test_add_and_remove_persist(self, tmp_path):
        manager = CollectorManager()
        manager.add_watch_folder("/tmp/inbox")
        assert _read_config(tmp_path)["folders"] == ["/tmp/inbox"]

        manager.remove_watch_folder("/tmp/inbox")
        assert _read_config(tmp_path)["folders"] == []

    def test_init_loads_json_over_env(self, tmp_path, args_minimal):
        (tmp_path / "watch_folders.json").write_text(
            json.dumps({"folders": ["/persisted"], "enabled": True, "interval": 5}),
            encoding="utf-8",
        )
        manager = CollectorManager()
        args_minimal.watch_folders = "/env-only"
        manager.init(args_minimal)

        assert manager.watch_folders == ["/persisted"]
        assert manager.watch_enabled is True
        assert manager.watch_interval == 5

    def test_init_keeps_env_when_no_json(self, args_minimal):
        manager = CollectorManager()
        args_minimal.watch_folders = "/env-a,/env-b"
        manager.init(args_minimal)

        assert manager.watch_folders == ["/env-a", "/env-b"]
        assert manager.watch_enabled is False


class TestWatchExecution:
    def test_watch_run_once_records_results(self, tmp_path):
        manager = CollectorManager()
        manager.watch_folders = ["/inbox-a", "/inbox-b"]
        calls = []

        def fake_import_all(folder_path=None):
            calls.append(folder_path)
            return {"total": 1, "imported": 1, "skipped": 0, "failed": 0}

        manager.import_all = fake_import_all
        results = manager.watch_run_once()

        assert calls == ["/inbox-a", "/inbox-b"]
        assert results["/inbox-a"]["imported"] == 1
        assert "at" in results["/inbox-a"]
        assert manager.get_watch_state()["last_runs"]["/inbox-b"]["total"] == 1

    def test_start_and_stop_watching(self, tmp_path):
        manager = CollectorManager()
        manager.watch_interval = 0.05
        manager.watch_folders = ["/inbox"]
        ran = threading.Event()

        def fake_import_all(folder_path=None):
            ran.set()
            return {"total": 0, "imported": 0, "skipped": 0, "failed": 0}

        manager.import_all = fake_import_all
        manager.start_watching()
        try:
            assert manager.get_watch_state()["running"] is True
            assert ran.wait(timeout=3), "监听线程未在预期时间内执行"
        finally:
            manager.stop_watching()
        assert manager.get_watch_state()["running"] is False

    def test_set_watch_enabled_persists(self, tmp_path):
        manager = CollectorManager()
        state = manager.set_watch_enabled(False)

        assert state["enabled"] is False
        assert _read_config(tmp_path)["enabled"] is False
