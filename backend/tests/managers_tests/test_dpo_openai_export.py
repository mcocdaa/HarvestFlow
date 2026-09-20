# @file backend/tests/managers_tests/test_dpo_openai_export.py
# @brief DPO 对抗偏好数据对与 OpenAI Messages 导出单元测试
# @create 2026-09-20

from managers.exporter_manager import ExporterManager
from core.constants import ExportFormat


class TestDpoAndOpenaiExport:
    def setup_method(self):
        self.manager = ExporterManager()

    def test_convert_to_openai_messages(self):
        sessions = [
            {
                "session_id": "sess_1",
                "content": {
                    "system_prompt": "You are a helpful coding assistant.",
                    "messages": [
                        {"role": "user", "content": "Write a python function"},
                        {"role": "assistant", "content": "def hello(): pass", "tool_calls": [{"name": "bash"}]}
                    ],
                    "tools": [{"name": "bash"}]
                }
            }
        ]

        result = self.manager._convert_to_openai(sessions)
        assert len(result) == 1
        record = result[0]
        assert "messages" in record
        messages = record["messages"]
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful coding assistant."
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["tool_calls"] == [{"name": "bash"}]
        assert record["tools"] == [{"name": "bash"}]

    def test_convert_to_dpo_with_human_edited_diff(self):
        """标注员在线修改前作为 rejected，修改后作为 chosen"""
        sessions = [
            {
                "session_id": "sess_dpo_1",
                "review_meta": {
                    "original_response": "Here is buggy code: print(x)",
                    "action": "approve"
                },
                "content": {
                    "system_prompt": "You are helpful.",
                    "messages": [
                        {"role": "user", "content": "How to print x safely?"},
                        {"role": "assistant", "content": "Here is safe code: if 'x' in locals(): print(x)"}
                    ]
                }
            }
        ]

        result = self.manager._convert_to_dpo(sessions)
        assert len(result) == 1
        dpo_record = result[0]

        assert dpo_record["prompt"] == "How to print x safely?"
        assert dpo_record["instruction"] == "How to print x safely?"
        assert dpo_record["chosen"] == "Here is safe code: if 'x' in locals(): print(x)"
        assert dpo_record["rejected"] == "Here is buggy code: print(x)"
        assert dpo_record["system"] == "You are helpful."
        assert dpo_record["session_id"] == "sess_dpo_1"

    def test_convert_to_dpo_fallback_baseline(self):
        sessions = [
            {
                "session_id": "sess_dpo_2",
                "review_meta": {},
                "content": {
                    "messages": [
                        {"role": "user", "content": "Explain gravity"},
                        {"role": "assistant", "content": "Gravity is a fundamental interaction..."}
                    ]
                }
            }
        ]

        result = self.manager._convert_to_dpo(sessions)
        assert len(result) == 1
        assert result[0]["chosen"] == "Gravity is a fundamental interaction..."
        assert len(result[0]["rejected"]) > 0

    def test_formats_enum_has_openai_and_dpo(self):
        assert ExportFormat.OPENAI == "openai"
        assert ExportFormat.DPO == "dpo"
