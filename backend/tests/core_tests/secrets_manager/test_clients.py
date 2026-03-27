# @file backend/tests/core_tests/secrets_manager/test_clients.py
# @brief SecretsManager 客户端测试
# @create 2026-03-27

import argparse

import pytest

from core.secrets_manager import (
    BaseSecretsClient,
    InfisicalSDKClient,
    LocalSecretsClient,
)


class TestBaseSecretsClient:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            BaseSecretsClient()


class TestInfisicalSDKClient:
    def setup_method(self):
        self.client = InfisicalSDKClient()

    def test_default_values(self):
        assert self.client.client_id == ""
        assert self.client.client_secret == ""
        assert self.client.project_id == ""
        assert self.client.environment == "dev"
        assert self.client.host == "https://app.infisical.com"
        assert self.client.cache_ttl == 300
        assert self.client.timeout == 10
        assert self.client._client is None
        assert self.client._connected is False

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.client.register_arguments(parser)

        args = parser.parse_args([
            "--infisical-client-id", "test-id",
            "--infisical-client-secret", "test-secret",
            "--infisical-project-id", "test-project",
            "--infisical-environment", "prod",
            "--infisical-host", "https://infisical.example.com",
            "--infisical-timeout", "30",
        ])

        assert args.infisical_client_id == "test-id"
        assert args.infisical_client_secret == "test-secret"
        assert args.infisical_project_id == "test-project"
        assert args.infisical_environment == "prod"
        assert args.infisical_host == "https://infisical.example.com"
        assert args.infisical_timeout == 30

    def test_register_arguments_with_env_defaults(self, monkeypatch):
        monkeypatch.setenv("INFISICAL_CLIENT_ID", "env-id")
        monkeypatch.setenv("INFISICAL_CLIENT_SECRET", "env-secret")
        monkeypatch.setenv("INFISICAL_PROJECT_ID", "env-project")
        monkeypatch.setenv("INFISICAL_ENVIRONMENT", "staging")

        parser = argparse.ArgumentParser()
        self.client.register_arguments(parser)
        args = parser.parse_args([])

        assert args.infisical_client_id == "env-id"
        assert args.infisical_client_secret == "env-secret"
        assert args.infisical_project_id == "env-project"
        assert args.infisical_environment == "staging"

    def test_init_sets_attributes_from_args(self):
        parser = argparse.ArgumentParser()
        self.client.register_arguments(parser)
        args = parser.parse_args([
            "--infisical-client-id", "test-id",
            "--infisical-client-secret", "test-secret",
            "--infisical-project-id", "test-project",
            "--infisical-environment", "prod",
            "--infisical-host", "https://example.com",
            "--infisical-timeout", "20",
        ])

        result = self.client.init(args)

        assert self.client.client_id == "test-id"
        assert self.client.client_secret == "test-secret"
        assert self.client.project_id == "test-project"
        assert self.client.environment == "prod"
        assert self.client.host == "https://example.com"
        assert self.client.timeout == 20
        assert result is False

    def test_get_secret_returns_none_when_not_connected(self):
        assert self.client.get_secret("ANY_KEY") is None

    def test_set_secret_returns_false_when_not_connected(self):
        assert self.client.set_secret("ANY_KEY", "value") is False

    def test_is_available_returns_false_when_not_connected(self):
        assert self.client.is_available() is False

    def test_init_returns_false_when_empty_client_id(self):
        parser = argparse.ArgumentParser()
        self.client.register_arguments(parser)
        args = parser.parse_args([
            "--infisical-client-id", "",
            "--infisical-client-secret", "test-secret",
            "--infisical-project-id", "test-project",
        ])
        result = self.client.init(args)
        assert result is False

    def test_init_returns_false_when_empty_client_secret(self):
        parser = argparse.ArgumentParser()
        self.client.register_arguments(parser)
        args = parser.parse_args([
            "--infisical-client-id", "test-id",
            "--infisical-client-secret", "",
            "--infisical-project-id", "test-project",
        ])
        result = self.client.init(args)
        assert result is False

    def test_init_returns_false_when_empty_project_id(self):
        parser = argparse.ArgumentParser()
        self.client.register_arguments(parser)
        args = parser.parse_args([
            "--infisical-client-id", "test-id",
            "--infisical-client-secret", "test-secret",
            "--infisical-project-id", "",
        ])
        result = self.client.init(args)
        assert result is False


class TestLocalSecretsClient:
    def setup_method(self):
        self.client = LocalSecretsClient()

    def test_init_always_returns_true(self, args_minimal):
        assert self.client.init(args_minimal) is True

    def test_is_available_always_returns_true(self):
        assert self.client.is_available() is True

    def test_get_secret_returns_none_for_nonexistent(self):
        assert self.client.get_secret("NONEXISTENT") is None

    def test_get_secret_returns_stored_value(self):
        self.client.set_secret("TEST_KEY", "test_value")
        assert self.client.get_secret("TEST_KEY") == "test_value"

    def test_set_secret_always_returns_true(self):
        assert self.client.set_secret("TEST_KEY", "test_value") is True
