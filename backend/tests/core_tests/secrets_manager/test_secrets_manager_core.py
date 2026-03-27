# @file backend/tests/core_tests/secrets_manager/test_secrets_manager_core.py
# @brief SecretsManager 核心功能测试
# @create 2026-03-27

import argparse

from core.secrets_manager import SecretsManager, LocalSecretsClient, InfisicalSDKClient


class TestSecretsManagerConstructor:
    def test_default_constructor_sets_local_client_class(self):
        manager = SecretsManager()
        assert manager._client_class == LocalSecretsClient
        assert manager.client is None
        assert manager.sdk_available is False

    def test_infisical_client_type_sets_infisical_client_class(self):
        manager = SecretsManager(client_type="infisical")
        assert manager._client_class == InfisicalSDKClient
        assert manager.client is None
        assert manager.sdk_available is False

    def test_init_creates_local_client_instance(self, args_minimal):
        manager = SecretsManager()
        manager.init(args_minimal, [])
        assert isinstance(manager.client, LocalSecretsClient)
        assert manager.sdk_available is False


class TestSecretsManagerCollectSecretDefs:
    def setup_method(self):
        self.manager = SecretsManager()

    def test_empty_collection_when_no_inputs(self, args_minimal):
        self.manager.init(args_minimal, [])
        result = self.manager._collect_secret_defs([])
        assert len(result) == 0

    def test_plugin_secrets_added_correctly(self, args_minimal):
        self.manager.init(args_minimal, [])
        plugin_secrets = [
            {"name": "KEY1", "description": "desc1", "level": "required"},
            {"name": "KEY2", "description": "desc2", "level": "optional"},
        ]
        result = self.manager._collect_secret_defs(plugin_secrets)
        assert len(result) == 2
        assert result[0]["name"] == "KEY1"
        assert result[1]["name"] == "KEY2"

    def test_duplicate_plugin_secrets_skipped(self, args_minimal):
        self.manager.init(args_minimal, [])
        plugin_secrets = [
            {"name": "KEY1", "description": "desc1"},
            {"name": "KEY1", "description": "desc2"},
        ]
        result = self.manager._collect_secret_defs(plugin_secrets)
        assert len(result) == 1


class TestSecretsManagerResolveSecretValue:
    def setup_method(self):
        self.manager = SecretsManager()

    def test_returns_default_when_no_client_value(self, args_minimal):
        self.manager.init(args_minimal, [])

        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "optional",
            "default": "default_value",
        })
        assert result == "default_value"

    def test_returns_empty_when_no_default(self, args_minimal):
        self.manager.init(args_minimal, [])

        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "optional",
        })
        assert result == ""

    def test_generates_random_for_required_when_no_client(self, args_minimal):
        self.manager.init(args_minimal, [])

        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "required",
        })
        assert len(result) > 0
        assert isinstance(result, str)


class TestSecretsManagerGetSecret:
    def setup_method(self):
        self.manager = SecretsManager()

    def test_get_secret_returns_empty_when_not_in_cache(self, args_minimal):
        self.manager.init(args_minimal, [])
        result = self.manager.get_secret("TEST_KEY")
        assert result == ""

    def test_list_secrets_returns_empty_list_when_no_secrets(self, args_minimal):
        self.manager.init(args_minimal, [])
        secrets = self.manager.list_secrets()
        assert len(secrets) == 0

    def test_is_sdk_available_returns_false_for_local(self, args_minimal):
        self.manager.init(args_minimal, [])
        assert self.manager.is_sdk_available() is False
        assert self.manager.is_agent_available() is False
