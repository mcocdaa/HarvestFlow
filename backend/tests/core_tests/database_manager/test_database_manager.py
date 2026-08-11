# @file backend/tests/core_tests/database_manager/test_database_manager.py
# @brief database_manager helper 单元测试（_clamp_limit / _deserialize_json_field）
# @create 2026-08-11

from core import database_manager


class TestClampLimit:
    def test_none_uses_default(self):
        dm = database_manager
        assert dm._clamp_limit(None, 20) == 20
        assert dm._clamp_limit(None, 100) == 100

    def test_bounds(self):
        dm = database_manager
        assert dm._clamp_limit(0, 20) == 1          # 下限
        assert dm._clamp_limit(-5, 20) == 1
        assert dm._clamp_limit(1000, 20) == 100     # 上限 MAX_PAGE_SIZE
        assert dm._clamp_limit(50, 20) == 50        # 正常

    def test_custom_max(self):
        dm = database_manager
        assert dm._clamp_limit(50, 10, max_value=30) == 30


class TestDeserializeJsonField:
    def test_valid_json(self):
        dm = database_manager
        data = {"tags": '["a", "b"]'}
        dm._deserialize_json_field(data, "tags")
        assert data["tags"] == ["a", "b"]

    def test_missing_field_keeps_dict(self):
        dm = database_manager
        data = {"other": 1}
        dm._deserialize_json_field(data, "tags")
        assert data == {"other": 1}

    def test_corrupt_json_keeps_raw_and_logs(self, caplog):
        dm = database_manager
        data = {"tags": "{not json"}
        with caplog.at_level("WARNING", logger="core.database_manager"):
            dm._deserialize_json_field(data, "tags")
        assert data["tags"] == "{not json"
        assert "JSON 反序列化失败" in caplog.text
