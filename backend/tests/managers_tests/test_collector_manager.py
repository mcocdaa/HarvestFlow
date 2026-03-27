# @file backend/tests/managers_tests/test_collector_manager.py
# @brief CollectorManager 采集管理器测试
# @create 2026-03-26

import os
import json
import tempfile
import argparse

import pytest

from core.setting_manager import setting_manager
from managers.collector_manager import CollectorManager


class TestCollectorManager:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_init_parses_watch_folders(self, args_minimal):
        args_minimal.watch_folders = "/folder1, /folder2,/folder3"
        args_minimal.poll_interval = 30
        self.manager.init(args_minimal)

        assert self.manager.watch_folders == ["/folder1", "/folder2", "/folder3"]
        assert self.manager.poll_interval == 30

    def test_init_empty_watch_folders(self, args_minimal):
        args_minimal.watch_folders = ""
        self.manager.init(args_minimal)

        assert self.manager.watch_folders == []

    def test_init_uses_default_poll_interval(self, args_minimal):
        if hasattr(args_minimal, 'poll_interval'):
            delattr(args_minimal, 'poll_interval')
        self.manager.init(args_minimal)

        assert self.manager.poll_interval == 60

    def test_raw_sessions_dir_property(self, args_minimal):
        self.manager.init(args_minimal)
        original_data = setting_manager.config.get("DATA_DIR")
        setting_manager.config["DATA_DIR"] = "/test/data"

        assert self.manager.raw_sessions_dir == "/test/data/raw_sessions"

        if original_data is not None:
            setting_manager.config["DATA_DIR"] = original_data

    def test_scan_folder_returns_json_files(self, tmp_path):
        (tmp_path / "file1.json").write_text("{}")
        (tmp_path / "file2.json").write_text("{}")
        (tmp_path / "file.txt").write_text("text")

        result = self.manager.scan_folder(str(tmp_path))

        assert len(result) == 2
        assert any("file1.json" in f for f in result)
        assert any("file2.json" in f for f in result)

    def test_scan_folder_resursive(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file.json").write_text("{}")

        result = self.manager.scan_folder(str(tmp_path))

        assert len(result) == 1
        assert "subdir" in result[0]

    def test_scan_folder_none_when_no_folder_provided(self):
        self.manager.watch_folders = []
        result = self.manager.scan_folder(None)
        assert result == []

    def test_scan_folder_folder_not_exists(self):
        result = self.manager.scan_folder("/nonexistent/path")
        assert result == []

    def test_scan_folder_uses_first_watch_folder(self):
        self.manager.watch_folders = ["/tmp"]
        result = self.manager.scan_folder(None)
        assert isinstance(result, list)

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

    def test_import_session_success(self, tmp_path, monkeypatch):
        from datetime import datetime
        from managers import session_manager

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "test.json"
        with open(source_file, "w") as f:
            json.dump({"session_id": "test-import", "messages": []}, f)

        def mock_create(session_data):
            return session_data

        monkeypatch.setattr(session_manager, "create_session", mock_create)

        target_dir = tmp_path / "target"
        result = self.manager.import_session(str(source_file), str(target_dir))

        date_folder = datetime.now().strftime("%Y-%m-%d")
        assert result is not None
        assert result == "test-import"
        assert os.path.exists(os.path.join(target_dir, date_folder, f"{result}.json"))

    def test_import_session_parse_fails_returns_none(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "bad.json"
        with open(source_file, "w") as f:
            f.write("bad")

        result = self.manager.import_session(str(source_file))
        assert result is None

    def test_import_session_copy_error_returns_none(self, tmp_path, monkeypatch):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "test.json"
        with open(source_file, "w") as f:
            json.dump({"session_id": "test-error", "messages": []}, f)

        def mock_copy2(*args):
            raise OSError("permission denied")

        monkeypatch.setattr("shutil.copy2", mock_copy2)

        result = self.manager.import_session(str(source_file))
        assert result is None

    def test_import_all_returns_correct_counts(self, tmp_path, monkeypatch):
        from managers import session_manager

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        for i in range(3):
            with open(source_dir / f"{i}.json", "w") as f:
                json.dump({"session_id": f"test-{i}", "messages": []}, f)

        def mock_create(session_data):
            return session_data

        monkeypatch.setattr(session_manager, "create_session", mock_create)

        result = self.manager.import_all(str(source_dir))

        assert result["total"] == 3
        assert result["imported"] == 3
        assert result["failed"] == 0

    def test_import_all_mixed_success_and_failure(self, tmp_path, monkeypatch):
        from managers import session_manager

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        for i in range(2):
            with open(source_dir / f"{i}.json", "w") as f:
                json.dump({"session_id": f"test-{i}", "messages": []}, f)
        with open(source_dir / "bad.json", "w") as f:
            f.write("bad json")

        def mock_create(session_data):
            return session_data

        monkeypatch.setattr(session_manager, "create_session", mock_create)

        result = self.manager.import_all(str(source_dir))

        assert result["total"] == 3
        assert result["imported"] == 2
        assert result["failed"] == 1

    def test_import_all_no_files_returns_zero(self, tmp_path):
        source_dir = tmp_path / "empty"
        source_dir.mkdir()

        result = self.manager.import_all(str(source_dir))

        assert result["total"] == 0
        assert result["imported"] == 0
        assert result["failed"] == 0

    def test_add_watch_folder_adds_new(self):
        self.manager.add_watch_folder("/test/path")
        assert "/test/path" in self.manager.watch_folders

    def test_add_watch_folder_prevents_duplicates(self):
        self.manager.add_watch_folder("/test/path")
        self.manager.add_watch_folder("/test/path")
        assert len(self.manager.watch_folders) == 1

    def test_remove_watch_folder_removes(self):
        self.manager.add_watch_folder("/test/path")
        assert "/test/path" in self.manager.watch_folders

        self.manager.remove_watch_folder("/test/path")
        assert "/test/path" not in self.manager.watch_folders

    def test_remove_watch_folder_ignores_not_present(self):
        self.manager.remove_watch_folder("/nonexistent")
        assert len(self.manager.watch_folders) == 0
