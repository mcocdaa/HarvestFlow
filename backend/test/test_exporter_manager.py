# @file backend/test/test_exporter_manager.py
# @brief 导出管理器测试
# @create 2026-03-18

import pytest
import os
import json
from core.database import Database
from managers.exporter_manager import ExporterManager
from managers.session_manager import SessionManager
from managers.reviewer_manager import ReviewerManager


class TestExporterManager:
    @pytest.fixture(autouse=True)
    def setup(self, test_db_path, test_data_dir):
        self.db_path = test_db_path
        self.data_dir = test_data_dir

        self.db = Database(test_db_path)
        self.db.initialize_tables()

        self.exporter = ExporterManager()
        self.exporter.db = self.db

        self.session_manager = SessionManager()
        self.session_manager.db = self.db

        self.reviewer = ReviewerManager()
        self.reviewer.db = self.db

        yield

        self.db.close()

    def test_export_no_sessions(self):
        result = self.exporter.export()

        assert result["success"] == False
        assert "No sessions found" in result["message"]

    def test_export_with_sessions(self, sample_session, temp_dir):
        for i in range(3):
            session = sample_session.copy()
            session["session_id"] = f"session_{i}"
            session["status"] = "approved"
            session["file_path"] = os.path.join(temp_dir, f"session_{i}.json")
            with open(session["file_path"], 'w') as f:
                json.dump({"messages": [{"role": "user", "content": f"test{i}"}]}, f)

            self.session_manager.create_session(session)
            self.reviewer.approve_session(session["session_id"])

        result = self.exporter.export(format="sharegpt", version="v1")

        assert result["success"] == True
        assert result["record_count"] > 0

    def test_convert_to_sharegpt(self, sample_session):
        sessions = [
            {
                "session_id": "test_001",
                "content": {
                    "messages": [
                        {"role": "system", "content": "You are helpful"},
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi there!"}
                    ],
                    "system_prompt": "You are helpful"
                }
            }
        ]

        result = self.exporter._convert_to_sharegpt(sessions)

        assert len(result) > 0
        assert "conversations" in result[0]

    def test_convert_to_alpaca(self, sample_session):
        sessions = [
            {
                "session_id": "test_001",
                "content": {
                    "messages": [
                        {"role": "user", "content": "What is 2+2?"},
                        {"role": "assistant", "content": "2+2 equals 4"}
                    ]
                }
            }
        ]

        result = self.exporter._convert_to_alpaca(sessions)

        assert len(result) > 0
        assert "instruction" in result[0]
        assert "output" in result[0]

    def test_export_formats(self):
        formats = ["sharegpt", "alpaca"]

        for fmt in formats:
            result = self.exporter.export(format=fmt)
            assert "success" in result

    def test_export_with_min_score(self, sample_session, temp_dir):
        session = sample_session.copy()
        session["session_id"] = "high_score"
        session["status"] = "approved"
        session["quality_manual_score"] = 5
        session["file_path"] = os.path.join(temp_dir, "high_score.json")
        with open(session["file_path"], 'w') as f:
            json.dump({"messages": [{"role": "user", "content": "test"}]}, f)

        self.session_manager.create_session(session)

        result = self.exporter.export(min_score=4)

        assert result["success"] == True

    def test_get_export_history(self):
        result = self.exporter.get_export_history()

        assert isinstance(result, list)

    def test_default_format(self):
        assert self.exporter.default_format == "sharegpt"
