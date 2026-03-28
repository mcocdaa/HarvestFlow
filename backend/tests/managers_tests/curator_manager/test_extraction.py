# @file backend/tests/managers_tests/curator_manager/test_extraction.py
# @brief CuratorManager 标签和工具提取测试
# @create 2026-03-27

from managers.curator_manager import CuratorManager


class TestCuratorManagerExtraction:
    def setup_method(self):
        self.manager = CuratorManager()

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

    def test_extract_tool_names_skips_non_dict_and_missing_name(self):
        content = {
            "tool_calls": [
                "not a dict",
                {"missing_name": "test"},
                {"name": "valid_tool"},
                None,
            ]
        }
        tools = self.manager._extract_tool_names_from_calls(content)

        assert len(tools) == 1
        assert "valid_tool" in tools
