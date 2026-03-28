# @file backend/tests/core_tests/secrets_manager/test_additional_features.py
# @brief SecretsManager 额外功能测试（缓存、刷新、验证等）
# @create 2026-03-27

import time
import base64

from core.secrets_manager import SecretsManager


class TestSecretsManagerAdditionalFeatures:
    def setup_method(self):
        self.manager = SecretsManager()

    def test_generate_random_secret(self, args_minimal):
        self.manager.init(args_minimal, [])
        result = self.manager._generate_random_secret()
        assert len(result) > 0
        assert isinstance(result, str)
        decoded = base64.urlsafe_b64decode(result)
        assert len(decoded) == 24

    def test_validate_required_passes_when_all_have_values(self, args_minimal):
        self.manager.init(args_minimal, [])
        self.manager.secret_defs = [
            {"name": "KEY1", "level": "required"},
            {"name": "KEY2", "level": "optional"},
        ]
        self.manager._set_cache("KEY1", "value1")
        assert self.manager._validate_required() is True

    def test_validate_required_fails_when_missing_required(self, args_minimal):
        self.manager.init(args_minimal, [])
        self.manager.secret_defs = [
            {"name": "MISSING_KEY", "level": "required"},
        ]
        assert self.manager._validate_required() is False

    def test_cache_set_and_get(self, args_minimal):
        self.manager.init(args_minimal, [])
        self.manager._set_cache("TEST_KEY", "test_value")
        assert self.manager._get_cache("TEST_KEY") == "test_value"

    def test_get_cache_returns_none_for_nonexistent(self, args_minimal):
        self.manager.init(args_minimal, [])
        assert self.manager._get_cache("NONEXISTENT") is None

    def test_is_cache_expired_returns_true_for_nonexistent(self, args_minimal):
        self.manager.init(args_minimal, [])
        assert self.manager.is_cache_expired("NONEXISTENT") is True

    def test_is_cache_expired_returns_false_for_fresh(self, args_minimal):
        self.manager.init(args_minimal, [])
        self.manager._set_cache("TEST_KEY", "test_value")
        assert self.manager.is_cache_expired("TEST_KEY") is False

    def test_get_secret_returns_cached_value(self, args_minimal):
        self.manager.init(args_minimal, [])
        self.manager._set_cache("TEST_KEY", "cached_value")
        assert self.manager.get_secret("TEST_KEY") == "cached_value"

    def test_get_secret_returns_empty_for_nonexistent(self, args_minimal):
        self.manager.init(args_minimal, [])
        assert self.manager.get_secret("NONEXISTENT") == ""

    def test_list_secrets_returns_all_names(self, args_minimal):
        self.manager.init(args_minimal, [
            {"name": "KEY1", "level": "optional"},
            {"name": "KEY2", "level": "optional"},
            {"name": "KEY3", "level": "optional"},
        ])
        result = self.manager.list_secrets()
        assert len(result) == 3
        assert "KEY1" in result
        assert "KEY2" in result
        assert "KEY3" in result

    def test_refresh_secret_updates_cache(self, args_minimal):
        self.manager.init(args_minimal, [{"name": "TEST_KEY", "level": "optional"}])
        self.manager._set_cache("TEST_KEY", "old_value")
        result = self.manager.refresh_secret("TEST_KEY")
        assert result == "old_value"

    def test_refresh_secret_waits_when_already_refreshing(self, args_minimal):
        self.manager.init(args_minimal, [{"name": "TEST_KEY", "level": "optional"}])
        self.manager._set_cache("TEST_KEY", "cached_value")
        self.manager.refreshing.add("TEST_KEY")

        result = self.manager.refresh_secret("TEST_KEY")
        assert result == "cached_value"

    def test_refresh_all_secrets_executes_without_error(self, args_minimal):
        self.manager.init(args_minimal, [
            {"name": "KEY1", "level": "optional"},
            {"name": "KEY2", "level": "optional"},
        ])
        self.manager.refresh_all_secrets()

    def test_get_secret_force_refresh_returns_empty_for_nonexistent(self, args_minimal):
        self.manager.init(args_minimal, [])
        assert self.manager.get_secret_force_refresh("NONEXISTENT") == ""

    def test_get_value_source_returns_correct_labels(self, args_minimal):
        self.manager.init(args_minimal, [])

        self.manager.client.set_secret("EXISTS", "value")
        assert self.manager._get_value_source({"name": "EXISTS", "level": "optional"}) == "远程服务"

        assert self.manager._get_value_source({"name": "MISSING", "level": "required"}) == "随机生成"
        assert self.manager._get_value_source({"name": "DEF", "level": "optional", "default": "abc"}) == "默认值"
        assert self.manager._get_value_source({"name": "EMPTY", "level": "optional"}) == "空值"

    def test_load_all_secrets_populates_cache(self, args_minimal):
        self.manager.init(args_minimal, [])
        self.manager.secret_defs = [
            {"name": "TEST1", "level": "optional", "default": "val1"},
            {"name": "TEST2", "level": "optional", "default": "val2"},
        ]
        self.manager._load_all_secrets()
        assert self.manager.get_secret("TEST1") == "val1"
        assert self.manager.get_secret("TEST2") == "val2"

    def test_resolve_secret_value_returns_client_value_when_available(self, args_minimal):
        self.manager.init(args_minimal, [])
        self.manager.client.set_secret("TEST_KEY", "client_value")
        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "optional",
        })
        assert result == "client_value"

    def test_resolve_secret_value_returns_random_for_required_no_client(self, args_minimal):
        self.manager.init(args_minimal, [])
        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "required",
        })
        assert len(result) > 0
        assert isinstance(result, str)

    def test_resolve_secret_value_required_generates_random_when_upload_fails(self, args_minimal, monkeypatch):
        self.manager.init(args_minimal, [])
        called = False

        def mock_set_secret(*args, **kwargs):
            nonlocal called
            called = True
            return False

        monkeypatch.setattr(self.manager.client, "set_secret", mock_set_secret)

        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "required",
        })
        assert called
        assert len(result) > 0
        assert isinstance(result, str)

    def test_resolve_secret_value_returns_default_when_no_client_no_value(self, args_minimal):
        self.manager.init(args_minimal, [])
        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "optional",
            "default": "my_default",
        })
        assert result == "my_default"

    def test_resolve_secret_value_returns_empty_when_no_client_no_default(self, args_minimal):
        self.manager.init(args_minimal, [])
        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "optional",
        })
        assert result == ""
