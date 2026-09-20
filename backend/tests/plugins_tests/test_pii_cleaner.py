# @file backend/tests/plugins_tests/test_pii_cleaner.py
# @brief PII 隐私脱敏 Cleaner 插件与通用格式互通测试
# @create 2026-09-20

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from plugins.curators.pii_cleaner.backend import clean_text, clean_session_content  # noqa: E402
from core.parsers import normalize_to_session_record, parse_multiformat_content  # noqa: E402


class TestPiiCleaner:
    def test_clean_api_keys(self):
        # OpenAI key
        text = "My key is sk-1234567890abcdef1234567890abcdef and should be masked."
        cleaned = clean_text(text)
        assert "sk-[REDACTED_API_KEY]" in cleaned
        assert "1234567890abcdef" not in cleaned

        # GitHub token
        gh_text = "Token: ghp_123456789012345678901234567890123456"
        assert "ghp_[REDACTED_GITHUB_TOKEN]" in clean_text(gh_text)

        # Bearer token
        bearer_text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
        assert "Bearer [REDACTED_TOKEN]" in clean_text(bearer_text)

    def test_clean_phone_numbers(self):
        text1 = "请致电 13812345678 获取验证码"
        cleaned1 = clean_text(text1)
        assert "[REDACTED_PHONE]" in cleaned1
        assert "13812345678" not in cleaned1

        text2 = "Contact: +86-15900001111 or +1 (555) 123-4567"
        cleaned2 = clean_text(text2)
        assert "[REDACTED_PHONE]" in cleaned2

    def test_clean_emails(self):
        text = "Contact us at secret_support@enterprise.internal for details."
        cleaned = clean_text(text)
        assert "[REDACTED_EMAIL]" in cleaned
        assert "secret_support@" not in cleaned

    def test_clean_session_content_nested(self):
        data = {
            "messages": [
                {"role": "user", "content": "我的电话是 18611112222，秘钥是 sk-9876543210fedcba9876543210"},
                {"role": "assistant", "content": "收到，请保管好邮箱 admin@example.com"}
            ],
            "metadata": {
                "author_phone": "13900002222"
            }
        }
        cleaned = clean_session_content(data)
        user_msg = cleaned["messages"][0]["content"]
        asst_msg = cleaned["messages"][1]["content"]

        assert "[REDACTED_PHONE]" in user_msg
        assert "18611112222" not in user_msg
        assert "sk-[REDACTED_API_KEY]" in user_msg
        assert "[REDACTED_EMAIL]" in asst_msg
        assert cleaned["metadata"]["author_phone"] == "[REDACTED_PHONE]"


class TestMultiFormatParsers:
    def test_parse_openai_messages_format(self):
        raw = {
            "messages": [
                {"role": "system", "content": "You are assistant"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "tools": [{"type": "function"}]
        }
        record = normalize_to_session_record(raw, default_name="test_openai")
        assert record is not None
        assert "content" in record
        assert record["status"] == "raw"
        assert len(record["content"]["messages"]) == 3
        assert record["content"]["system_prompt"] == "You are assistant"
        assert record["tags"] == ["openai"]

    def test_parse_sharegpt_format(self):
        raw = {
            "conversations": [
                {"from": "human", "value": "How are you?"},
                {"from": "gpt", "value": "I am fine, thank you!"}
            ],
            "system": "Helpful bot"
        }
        record = normalize_to_session_record(raw, default_name="test_sharegpt")
        assert record is not None
        assert record["agent_role"] == "gpt"
        messages = record["content"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "How are you?"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "I am fine, thank you!"
        assert record["content"]["system_prompt"] == "Helpful bot"

    def test_parse_alpaca_format(self):
        raw = {
            "instruction": "Translate to French",
            "input": "Hello world",
            "output": "Bonjour le monde"
        }
        record = normalize_to_session_record(raw, default_name="test_alpaca")
        assert record is not None
        messages = record["content"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert "Translate to French" in messages[0]["content"]
        assert "Hello world" in messages[0]["content"]
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Bonjour le monde"

    def test_parse_multiformat_content_jsonl(self):
        jsonl = (
            '{"instruction": "Q1", "output": "A1"}\n'
            '{"messages": [{"role": "user", "content": "Q2"}, {"role": "assistant", "content": "A2"}]}\n'
        )
        records = parse_multiformat_content(jsonl, source_name="batch")
        assert len(records) == 2
        assert records[0]["content"]["messages"][0]["content"] == "Q1"
        assert records[1]["content"]["messages"][0]["content"] == "Q2"
