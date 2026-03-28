# @file backend/tests/managers_tests/curator_manager/test_scoring.py
# @brief CuratorManager 评分计算测试
# @create 2026-03-27

from managers.curator_manager import CuratorManager


class TestCuratorManagerScoring:
    def setup_method(self):
        self.manager = CuratorManager()

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
