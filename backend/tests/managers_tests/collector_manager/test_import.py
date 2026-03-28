# @file backend/tests/managers_tests/collector_manager/test_import.py
# @brief CollectorManager 导入会话测试
# @create 2026-03-27

import os
import json
import tempfile

import pytest

from managers.collector_manager import CollectorManager


class TestCollectorManagerImport:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_import_session_success(self, tmp_path, monkeypatch):
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

        assert result is not None
        assert result == "test-import"

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

    def test_import_all_includes_session_ids_and_failed_files(self, tmp_path, monkeypatch):
        from managers import session_manager

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        for i in range(2):
            with open(source_dir / f"{i}.json", "w") as f:
                f.write("{\"session_id\": \"test-{i}\"}")
        with open(source_dir / "bad.json", "w") as f:
            f.write("bad json")

        def mock_create(session_data):
            return session_data

        monkeypatch.setattr(session_manager, "create_session", mock_create)

        result = self.manager.import_all(str(source_dir))

        assert len(result["session_ids"]) == 2
        assert len(result["failed_files"]) == 1
        assert "bad.json" in result["failed_files"][0]

    def test_import_session_returns_none_when_create_fails(self, tmp_path, monkeypatch):
        from managers import session_manager

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "test.json"
        with open(source_file, "w") as f:
            f.write("{\"session_id\": \"test-fail\", \"messages\": []}")

        def mock_create(session_data):
            raise RuntimeError("Database connection failed")

        monkeypatch.setattr(session_manager, "create_session", mock_create)

        result = self.manager.import_session(str(source_file))
        assert result is None
