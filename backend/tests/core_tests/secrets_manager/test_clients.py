# @file backend/tests/core_tests/secrets_manager/test_clients.py
# @brief SecretsManager 客户端测试
# @create 2026-03-27

import argparse

import pytest

from core.secrets_manager import (
    BaseSecretsClient,
    LocalSecretsClient,
)


class TestBaseSecretsClient:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            BaseSecretsClient()


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
