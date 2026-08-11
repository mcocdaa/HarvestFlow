# @file backend/tests/core_tests/test_constants.py
# @brief 全局枚举与通用常量测试
# @create 2026-08-11

import json

from core.constants import (
    SessionStatus,
    ExportFormat,
    MAX_PAGE_SIZE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_HISTORY_LIMIT,
)


class TestSessionStatus:
    def test_members_values(self):
        assert SessionStatus.RAW.value == "raw"
        assert SessionStatus.CURATED.value == "curated"
        assert SessionStatus.APPROVED.value == "approved"
        assert SessionStatus.REJECTED.value == "rejected"

    def test_str_equality_and_lookup(self):
        # StrEnum 成员与字符串天然兼容（==、in、dict 键）
        assert SessionStatus.RAW == "raw"
        assert "approved" in [SessionStatus.APPROVED]
        assert {SessionStatus.CURATED: 1}.get("curated") == 1

    def test_unique_values(self):
        values = [s.value for s in SessionStatus]
        assert len(values) == len(set(values))

    def test_json_serialization(self):
        assert json.dumps({"status": SessionStatus.RAW}) == '{"status": "raw"}'

    def test_all_members_str(self):
        for s in SessionStatus:
            assert isinstance(str(s), str)
            assert s.value == str(s)


class TestExportFormat:
    def test_members_values(self):
        assert ExportFormat.SHAREGPT.value == "sharegpt"
        assert ExportFormat.ALPACA.value == "alpaca"

    def test_unique_values(self):
        values = [f.value for f in ExportFormat]
        assert len(values) == len(set(values))


class TestCommonConstants:
    def test_values(self):
        assert MAX_PAGE_SIZE == 100
        assert DEFAULT_PAGE_SIZE == 20
        assert DEFAULT_HISTORY_LIMIT == 20
