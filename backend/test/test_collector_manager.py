# @file backend/test/test_collector_manager.py
# @brief 采集管理器测试
# @create 2026-03-18

import pytest
import os
import json
from core.database import Database, get_database
from managers.collector_manager import CollectorManager
from managers.session_manager import SessionManager


class TestCollectorManager:
    @pytest.fixture(autouse=True)
    def setup_method(self, test_db_path, test_data_dir):
        self.db_path = test_db_path
        self.data_dir = test_data_dir

        from core import database as db_module
        import config.settings as settings

        db_module._db_instance = None
        settings.DB_PATH = test_db_path
        settings.RAW_SESSIONS_DIR = os.path.join(test_data_dir, "raw_sessions")
        os.makedirs(settings.RAW_SESSIONS_DIR, exist_ok=True)

        self.db = get_database()
        self.db.initialize_tables()

        self.collector = CollectorManager()
        self.collector.db = self.db

        self.session_manager = SessionManager()
        self.session_manager.db = self.db

        yield

        self.db.close()

    def test_scan_empty_folder(self):
        files = self.collector.scan_folder("/nonexistent_folder")
        assert files == []

    def test_scan_folder_with_json_files(self, temp_dir):
        for i in range(3):
            file_path = os.path.join(temp_dir, f"session_{i}.json")
            with open(file_path, 'w') as f:
                json.dump({"session_id": f"session_{i}"}, f)

        files = self.collector.scan_folder(temp_dir)
        assert len(files) == 3

    def test_scan_folder_ignores_non_json(self, temp_dir):
        file_path = os.path.join(temp_dir, "readme.txt")
        with open(file_path, 'w') as f:
            f.write("This is not JSON")

        files = self.collector.scan_folder(temp_dir)
        assert files == []

    def test_parse_session_file(self, sample_session_file):
        result = self.collector.parse_session_file(sample_session_file)

        assert result is not None
        assert "session_id" in result
        assert result["agent_role"] == "backend_dev"

    def test_parse_invalid_file(self):
        result = self.collector.parse_session_file("/nonexistent/file.json")
        assert result is None

    def test_import_session(self, sample_session_file):
        session_id = self.collector.import_session(sample_session_file)

        assert session_id is not None

        session = self.session_manager.get_session(session_id)
        assert session is not None
        assert session["status"] == "raw"

    def test_import_session_generates_id(self, temp_dir):
        session_data = {
            "messages": [{"role": "user", "content": "test"}]
        }
        session_file = os.path.join(temp_dir, "no_id_session.json")
        with open(session_file, 'w') as f:
            json.dump(session_data, f)

        session_id = self.collector.import_session(session_file)

        assert session_id is not None
        assert session_id.startswith("session_")

    def test_import_all(self, temp_dir):
        for i in range(3):
            file_path = os.path.join(temp_dir, f"session_{i}.json")
            with open(file_path, 'w') as f:
                json.dump({"session_id": f"session_{i}"}, f)

        result = self.collector.import_all(temp_dir)

        assert result["total"] == 3
        assert result["imported"] == 3
        assert result["failed"] == 0

    def test_add_watch_folder(self):
        self.collector.add_watch_folder("/test/folder")
        assert "/test/folder" in self.collector.watch_folders

    def test_add_duplicate_watch_folder(self):
        self.collector.add_watch_folder("/test/folder")
        self.collector.add_watch_folder("/test/folder")
        assert self.collector.watch_folders.count("/test/folder") == 1

    def test_remove_watch_folder(self):
        self.collector.add_watch_folder("/test/folder")
        self.collector.remove_watch_folder("/test/folder")
        assert "/test/folder" not in self.collector.watch_folders
