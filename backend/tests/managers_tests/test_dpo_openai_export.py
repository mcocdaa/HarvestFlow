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

    def test_convert_to_dpo_skips_unedited_session(self):
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
        assert len(result) == 0

    def test_convert_to_dpo_preserves_multiturn_history(self):
        sessions = [
            {
                "session_id": "sess_dpo_multi",
                "review_meta": {
                    "chosen": "Use WeakMap to avoid retaining dead references.",
                    "rejected": "Just use a global dict.",
                    "original_response": "Just use a global dict.",
                    "diff_applied": True,
                },
                "content": {
                    "system_prompt": "You are a senior engineer.",
                    "messages": [
                        {"role": "user", "content": "My worker is leaking memory."},
                        {"role": "assistant", "content": "Can you share how you cache objects?"},
                        {"role": "user", "content": "I store DOM nodes in a Map."},
                        {"role": "assistant", "content": "Use WeakMap to avoid retaining dead references."},
                    ],
                },
            }
        ]

        result = self.manager._convert_to_dpo(sessions)
        assert len(result) == 1
        rec = result[0]
        assert rec["chosen"] == "Use WeakMap to avoid retaining dead references."
        assert rec["rejected"] == "Just use a global dict."
        assert rec["chosen"] != rec["rejected"]
        assert "My worker is leaking memory." in rec["prompt"]
        assert "Can you share how you cache objects?" in rec["prompt"]
        assert "I store DOM nodes in a Map." in rec["prompt"]
        assert len(rec["history"]) == 3

    def test_e2e_human_edit_review_apply_to_sft_and_dpo_export(self, args_with_db_path, tmp_path, monkeypatch):
        """端到端回归测试：人工在线修改并审批后，SFT 导出使用修改后 chosen，DPO 导出包含 chosen != rejected 且跳过未修改会话"""
        from core import database_manager
        from core.constants import SessionStatus
        from managers.reviewer_manager import reviewer_manager
        from managers.session_manager import session_manager

        database_manager.init(args_with_db_path)
        self.manager.output_dir = str(tmp_path)

        # 1. 创建待审会话 A（人工在线修改）与会话 B（未修改直接通过）
        session_manager.create_session({
            "session_id": "e2e-edited",
            "status": SessionStatus.RAW.value,
            "content": {
                "system_prompt": "Helpful coding assistant",
                "messages": [
                    {"role": "user", "content": "How to compare tokens securely?"},
                    {"role": "assistant", "content": "Use token == expected"},
                ],
            },
        })
        session_manager.update_session("e2e-edited", {"status": SessionStatus.CURATED.value})

        session_manager.create_session({
            "session_id": "e2e-unedited",
            "status": SessionStatus.RAW.value,
            "content": {
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            },
        })
        session_manager.update_session("e2e-unedited", {"status": SessionStatus.CURATED.value})

        # 2. 人工在 ReviewWorkspace 中修改 e2e-edited 的回复并审批通过
        reviewer_manager.approve_session(
            "e2e-edited",
            notes="Fixed timing attack",
            score=5,
            extras={
                "diff_applied": True,
                "chosen": "Use hmac.compare_digest(token, expected)",
                "rejected": "Use token == expected",
                "original_response": "Use token == expected",
            },
        )
        reviewer_manager.approve_session("e2e-unedited", notes="Looks good", score=4)

        # 3. 验证数据库中 content 已更新为人工修改后的 chosen，且 review_meta 保留了 original_response 与 rejected
        updated_sess = session_manager.get_session("e2e-edited")
        assert updated_sess["content"]["messages"][-1]["content"] == "Use hmac.compare_digest(token, expected)"
        assert updated_sess["review_meta"]["original_response"] == "Use token == expected"
        assert updated_sess["review_meta"]["rejected"] == "Use token == expected"

        # 4. SFT (OpenAI / ShareGPT) 导出应包含 2 条会话，且 e2e-edited 的回复为修改后的文本
        sft_res = self.manager.export(format="openai")
        assert sft_res["success"] is True
        assert sft_res["record_count"] == 2
        with open(sft_res["file_path"], encoding="utf-8") as f:
            sft_lines = [f.readline(), f.readline()]
        assert any("Use hmac.compare_digest(token, expected)" in line for line in sft_lines)

        # 5. DPO 导出应仅包含被修改过的 e2e-edited（跳过无 rejected 的 e2e-unedited），且 chosen != rejected
        dpo_res = self.manager.export(format="dpo")
        assert dpo_res["success"] is True
        assert dpo_res["record_count"] == 1
        import json
        with open(dpo_res["file_path"], encoding="utf-8") as f:
            dpo_items = [json.loads(line) for line in f if line.strip()]
        assert len(dpo_items) == 1
        assert dpo_items[0]["session_id"] == "e2e-edited"
        assert dpo_items[0]["chosen"] == "Use hmac.compare_digest(token, expected)"
        assert dpo_items[0]["rejected"] == "Use token == expected"
        assert dpo_items[0]["chosen"] != dpo_items[0]["rejected"]

    def test_formats_enum_has_openai_and_dpo(self):
        assert ExportFormat.OPENAI == "openai"
        assert ExportFormat.DPO == "dpo"
