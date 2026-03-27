# @file backend/tests/managers_tests/test_curator_manager.py
# @brief CuratorManager 自动审核管理器测试
# @create 2026-03-26

import os
import json
import tempfile
import argparse

import pytest

from core.setting_manager import setting_manager
from managers.session_manager import session_manager
from managers.curator_manager import CuratorManager


class TestCuratorManager:
    def setup_method(self):
        self.manager = CuratorManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_init_uses_arguments(self, args_minimal):
        args_minimal.curator_enabled = False
        args_minimal.auto_approve_threshold = 5
        self.manager.init(args_minimal)

        assert self.manager.enabled is False
        assert self.manager.auto_approve_threshold == 5

    def test_init_uses_defaults(self, args_minimal):
        if hasattr(args_minimal, 'curator_enabled'):
            delattr(args_minimal, 'curator_enabled')
        if hasattr(args_minimal, 'auto_approve_threshold'):
            delattr(args_minimal, 'auto_approve_threshold')
        self.manager.init(args_minimal)

        assert self.manager.enabled is True
        assert self.manager.auto_approve_threshold == 4

    def test_agent_curated_dir_property(self, args_minimal):
        self.manager.init(args_minimal)
        original_data = setting_manager.config.get("DATA_DIR")
        setting_manager.config["DATA_DIR"] = "/test/data"

        assert self.manager.agent_curated_dir == "/test/data/agent_curated"

        if original_data is not None:
            setting_manager.config["DATA_DIR"] = original_data

    def test_evaluate_session_session_not_found(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        def mock_get(session_id):
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        result = self.manager.evaluate_session("nonexistent")

        assert "error" in result
        assert result["error"] == "session not found"

    def test_evaluate_session_content_not_found(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id, "file_path": "/nonexistent.json"}

        def mock_get_content(session_id):
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)
        monkeypatch.setattr(session_manager, "get_session_content", mock_get_content)

        result = self.manager.evaluate_session("test")

        assert "error" in result
        assert result["error"] == "content not found"

    def test_evaluate_session_calculates_score(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        content = {
            "messages": [1] * 15,
            "tool_calls": [{"name": "tool1"}],
            "final_output": "result"
        }

        def mock_get(session_id):
            return {"session_id": session_id, "file_path": "/test.json"}

        def mock_get_content(session_id):
            return content

        monkeypatch.setattr(session_manager, "get_session", mock_get)
        monkeypatch.setattr(session_manager, "get_session_content", mock_get_content)

        called_updates = None
        def mock_update(session_id, updates):
            nonlocal called_updates
            called_updates = updates
            return {"session_id": session_id, **updates}

        monkeypatch.setattr(session_manager, "update_session", mock_update)

        result = self.manager.evaluate_session("test")

        assert result["score"] == 5
        assert result["is_high_value"] is True
        assert called_updates is not None
        assert called_updates["quality_auto_score"] == 5

    def test_calculate_score_base_score(self):
        content = {}
        score = self.manager._calculate_score(content)
        assert score == 3

    def test_calculate_score_adds_for_many_messages(self):
        content = {"messages": [1] * 15}
        score = self.manager._calculate_score(content)
        assert score == 4

    def test_calculate_score_adds_for_over_20_messages(self):
        content = {"messages": [1] * 25}
        score = self.manager._calculate_score(content)
        assert score == 5

    def test_calculate_score_adds_for_tool_calls(self):
        content = {"tool_calls": [{"name": "test"}]}
        score = self.manager._calculate_score(content)
        assert score == 4

    def test_calculate_score_adds_for_tools_used(self):
        content = {"tools_used": ["test"]}
        score = self.manager._calculate_score(content)
        assert score == 4

    def test_calculate_score_adds_for_final_output(self):
        content = {"final_output": "result"}
        score = self.manager._calculate_score(content)
        assert score == 4

    def test_calculate_score_adds_for_result(self):
        content = {"result": "result"}
        score = self.manager._calculate_score(content)
        assert score == 4

    def test_calculate_score_max_at_5(self):
        content = {
            "messages": [1] * 20,
            "tool_calls": [],
            "final_output": "result"
        }
        score = self.manager._calculate_score(content)
        assert score == 5

    def test_extract_tags_from_task_type_and_role(self):
        content = {
            "task_type": "debugging",
            "agent_role": "coder"
        }
        tags = self.manager._extract_tags(content)

        assert "debugging" in tags
        assert "coder" in tags
        assert len(tags) == 2

    def test_extract_tags_from_tool_calls(self):
        content = {
            "task_type": "coding",
            "tool_calls": [
                {"name": "python"},
                {"name": "bash"}
            ]
        }
        tags = self.manager._extract_tags(content)

        assert "coding" in tags
        assert "python" in tags
        assert "bash" in tags

    def test_extract_tags_removes_duplicates(self):
        content = {
            "task_type": "python",
            "tool_calls": [{"name": "python"}]
        }
        tags = self.manager._extract_tags(content)

        assert len(tags) == 1
        assert "python" in tags

    def test_extract_tools_from_both_sources(self):
        content = {
            "tools_used": ["tool1", "tool2"],
            "tool_calls": [{"name": "tool2"}, {"name": "tool3"}]
        }
        tools = self.manager._extract_tools(content)

        assert set(tools) == {"tool1", "tool2", "tool3"}

    def test_extract_tools_removes_duplicates(self):
        content = {
            "tools_used": ["tool1", "tool1"],
            "tool_calls": [{"name": "tool1"}]
        }
        tools = self.manager._extract_tools(content)

        assert len(tools) == 1
        assert "tool1" in tools

    def test__move_to_curated_session_not_found(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        def mock_get(session_id):
            return None

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        self.manager._move_to_curated("test")

        assert True

    def test__move_to_curated_no_source_path(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id}

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        self.manager._move_to_curated("test")

        assert True

    def test__move_to_curated_source_not_exists(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        def mock_get(session_id):
            return {"session_id": session_id, "file_path": "/nonexistent/file.json"}

        monkeypatch.setattr(session_manager, "get_session", mock_get)

        self.manager._move_to_curated("test")

        assert True

    def test_evaluate_all_evaluates_all_raw_sessions(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        from core import database_manager

        original = database_manager.session_get_by_status
        database_manager.session_get_by_status = lambda status: [
            {"session_id": "1"},
            {"session_id": "2"},
            {"session_id": "3"}
        ]

        called = []
        def mock_evaluate(session_id):
            called.append(session_id)
            return {"session_id": session_id, "is_high_value": True}

        monkeypatch.setattr(self.manager, "evaluate_session", mock_evaluate)

        try:
            result = self.manager.evaluate_all()

            assert result["total"] == 3
            assert result["high_value"] == 3
            assert len(called) == 3
        finally:
            database_manager.session_get_by_status = original

    def test_evaluate_all_counts_low_value(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal)

        from core import database_manager

        original = database_manager.session_get_by_status
        database_manager.session_get_by_status = lambda status: [
            {"session_id": "1"},
            {"session_id": "2"}
        ]

        called_count = 0
        def mock_evaluate(session_id):
            nonlocal called_count
            called_count += 1
            if called_count == 1:
                return {"session_id": session_id, "is_high_value": True}
            else:
                return {"session_id": session_id, "is_high_value": False}

        monkeypatch.setattr(self.manager, "evaluate_session", mock_evaluate)

        try:
            result = self.manager.evaluate_all()

            assert result["total"] == 2
            assert result["high_value"] == 1
            assert result["low_value"] == 1
        finally:
            database_manager.session_get_by_status = original
