# @file backend/test/test_curator_manager.py
# @brief 自动审核管理器测试
# @create 2026-03-18

import pytest
import os
import json
from core.database import Database, get_database
from managers.curator_manager import CuratorManager
from managers.session_manager import SessionManager


class TestCuratorManager:
    @pytest.fixture(autouse=True)
    def setup_method(self, test_db_path, test_data_dir):
        from core import database as db_module
        import config.settings as settings

        db_module._db_instance = None
        settings.DB_PATH = test_db_path
        settings.AGENT_CURATED_DIR = os.path.join(test_data_dir, "agent_curated")
        os.makedirs(settings.AGENT_CURATED_DIR, exist_ok=True)

        self.db = get_database()
        self.db.initialize_tables()

        self.curator = CuratorManager()
        self.curator.db = self.db

        self.session_manager = SessionManager()
        self.session_manager.db = self.db

        yield

        self.db.close()

    def test_evaluate_session(self, sample_session):
        self.session_manager.create_session(sample_session)

        result = self.curator.evaluate_session("test_session_001")

        assert result is not None
        assert "score" in result
        assert "is_high_value" in result
        assert isinstance(result["score"], int)
        assert 1 <= result["score"] <= 5

    def test_evaluate_nonexistent_session(self):
        result = self.curator.evaluate_session("nonexistent")
        assert result is None

    def test_calculate_score_basic(self, sample_session):
        score = self.curator._calculate_score(sample_session)
        assert isinstance(score, int)
        assert 1 <= score <= 5

    def test_calculate_score_with_many_messages(self):
        session = {
            "messages": [{"role": "user", "content": f"msg{i}"} for i in range(25)]
        }
        score = self.curator._calculate_score(session)
        assert score >= 4

    def test_calculate_score_with_tool_calls(self):
        session = {
            "messages": [{"role": "user", "content": "test"}],
            "tool_calls": [{"name": "bash", "arguments": {"command": "ls"}}]
        }
        score = self.curator._calculate_score(session)
        assert score >= 4

    def test_calculate_score_with_final_output(self):
        session = {
            "messages": [{"role": "user", "content": "test"}],
            "final_output": "completed"
        }
        score = self.curator._calculate_score(session)
        assert score >= 4

    def test_extract_tags(self, sample_session):
        tags = self.curator._extract_tags(sample_session)
        assert isinstance(tags, list)
        assert "backend_dev" in tags

    def test_extract_tools(self, sample_session):
        tools = self.curator._extract_tools(sample_session)
        assert isinstance(tools, list)

    def test_evaluate_all(self, sample_session):
        for i in range(5):
            session = sample_session.copy()
            session["session_id"] = f"session_{i}"
            self.session_manager.create_session(session)

        result = self.curator.evaluate_all()

        assert result["total"] == 5
        assert "high_value" in result
        assert "low_value" in result

    def test_evaluate_all_empty(self):
        result = self.curator.evaluate_all()
        assert result["total"] == 0

    def test_curator_config(self):
        assert self.curator.enabled == True
        assert self.curator.auto_approve_threshold == 4
