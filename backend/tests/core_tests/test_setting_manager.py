# @file backend/tests/core_tests/test_setting_manager.py
# @brief SettingManager 测试
# @create 2026-03-22

import argparse

import pytest

from core.setting_manager import SettingManager


class TestSettingManager:
    def setup_method(self):
        self.manager = SettingManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

        args = parser.parse_args(["--host", "localhost", "--port", "8080"])
        assert args.host == "localhost"
        assert args.port == 8080

    def test_init_and_get(self, args_minimal):
        self.manager.init(args_minimal)

        assert self.manager.get("host") == "127.0.0.1"
        assert self.manager.get("port") == 3000

    def test_get_with_default(self, args_minimal):
        self.manager.init(args_minimal)

        assert self.manager.get("nonexistent") is None
        assert self.manager.get("nonexistent", "default") == "default"

    def test_set_and_get(self, args_minimal):
        self.manager.init(args_minimal)

        self.manager.set("custom_key", "custom_value")
        assert self.manager.get("custom_key") == "custom_value"

    def test_cors_origins_parsing(self, args_minimal):
        args_minimal.cors_origins = "http://localhost,https://example.com"
        self.manager.init(args_minimal)

        assert self.manager.get("cors_origins") == ["http://localhost", "https://example.com"]

    def test_cors_origins_wildcard(self, args_minimal):
        args_minimal.cors_origins = "*"
        self.manager.init(args_minimal)

        assert self.manager.get("cors_origins") == ["*"]

    def test_cors_origins_from_config(self, args_minimal):
        self.manager.config["CORS_ORIGINS"] = "http://one.com, http://two.com"
        if hasattr(args_minimal, 'cors_origins'):
            delattr(args_minimal, 'cors_origins')
        self.manager.init(args_minimal)

        assert self.manager.get("cors_origins") == ["http://one.com", "http://two.com"]

    def test__getattr__(self, args_minimal):
        self.manager.init(args_minimal)

        self.manager.set("test_key", "test_value")
        assert self.manager.TEST_KEY == "test_value"
        assert self.manager.test_key == "test_value"

    def test__getattr__raises_for_private(self, args_minimal):
        self.manager.init(args_minimal)

        with pytest.raises(AttributeError):
            _ = self.manager._private_attr

    def test__getattr__returns_none_for_nonexistent(self, args_minimal):
        self.manager.init(args_minimal)

        assert self.manager.NON_EXISTENT is None

    def test_auto_upper_case_in_get(self, args_minimal):
        self.manager.init(args_minimal)

        self.manager.set("MY_KEY", "my_value")
        assert self.manager.get("my_key") == "my_value"
        assert self.manager.get("MY_KEY") == "my_value"

    def test_auto_upper_case_in_set(self, args_minimal):
        self.manager.init(args_minimal)

        self.manager.set("lower_key", "lower_value")
        assert self.manager.config["LOWER_KEY"] == "lower_value"
        assert self.manager.get("lower_key") == "lower_value"

    def test_init_uses_env_fallback(self, args_minimal):
        delattr(args_minimal, 'host')
        delattr(args_minimal, 'port')
        self.manager.config["HOST"] = "192.168.1.1"
        self.manager.config["PORT"] = "9999"

        self.manager.init(args_minimal)

        assert self.manager.get("host") == "192.168.1.1"
        assert self.manager.get("port") == "9999"

    def test_env_file_loaded(self):
        manager = SettingManager()

        assert "ROOT_DIR" in manager.config
        assert "BACKEND_DIR" in manager.config
        assert manager.config["API_VERSION"] == "v1"

    def test_logging_configured(self, args_minimal):
        import logging
        original_level = logging.getLogger().level
        self.manager.config["LOG_LEVEL"] = "DEBUG"
        self.manager.init(args_minimal)

        level = getattr(logging, self.manager.get("LOG_LEVEL"))
        assert level == logging.DEBUG

        logging.getLogger().setLevel(original_level)
