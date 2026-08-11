# @file backend/tests/core_tests/secrets_manager/test_secrets_manager_core.py
# @brief SecretsManager 核心功能测试
# @create 2026-03-27


from core.secrets_manager import SecretsManager, LocalSecretsClient


class TestSecretsManagerConstructor:
    def test_default_constructor_sets_local_client_class(self):
        manager = SecretsManager()
        assert manager._client_class == LocalSecretsClient
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
        assert result == ("default_value", "default")

    def test_returns_empty_when_no_default(self, args_minimal):
        self.manager.init(args_minimal, [])

        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "optional",
        })
        assert result == ("", "default")

    def test_generates_random_for_required_when_no_client(self, args_minimal):
        self.manager.init(args_minimal, [])

        result = self.manager._resolve_secret_value({
            "name": "TEST_KEY",
            "level": "required",
        })
        assert len(result[0]) > 0
        assert isinstance(result[0], str)


class TestSecretsManagerGetSecret:
    def setup_method(self):
        self.manager = SecretsManager()

    def test_get_secret_returns_empty_when_not_in_cache(self, args_minimal):
        self.manager.init(args_minimal, [])
        result = self.manager.get_secret("TEST_KEY")
        assert result == ""


class TestRefreshConcurrency:
    def test_serial_refresh(self):
        from core.secrets_manager import secrets_manager

        original_client = secrets_manager.client
        try:
            calls = []

            class FakeClient:
                def is_available(self):
                    return True

                def get_secret(self, name):
                    calls.append(name)
                    return "new-value"

            secrets_manager.client = FakeClient()
            secrets_manager._set_cache("KEY", "old-value")

            result = secrets_manager.refresh_secret("KEY")
            assert result == "new-value"
            assert calls == ["KEY"]
        finally:
            secrets_manager.client = original_client

    def test_concurrent_refresh_single_fetch(self):
        import threading
        import time

        from core.secrets_manager import secrets_manager

        original_client = secrets_manager.client
        try:
            calls = []

            class SlowClient:
                def is_available(self):
                    return True

                def get_secret(self, name):
                    calls.append(name)
                    time.sleep(0.2)
                    return "slow-value"

            secrets_manager.client = SlowClient()
            secrets_manager._set_cache("KEY2", "old-value")

            results = []

            def worker():
                results.append(secrets_manager.refresh_secret("KEY2"))

            threads = [threading.Thread(target=worker) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(calls) == 1        # 并发去重：仅一次真实刷新
            assert results == ["slow-value", "slow-value", "slow-value"]
        finally:
            secrets_manager.client = original_client

    def test_waiting_thread_gets_refreshed_cache(self):
        import threading
        import time

        from core.secrets_manager import secrets_manager

        original_client = secrets_manager.client
        try:
            calls = []

            class GateClient:
                def is_available(self):
                    return True

                def get_secret(self, name):
                    calls.append(name)
                    time.sleep(0.1)
                    return "gated-value"

            secrets_manager.client = GateClient()
            secrets_manager._set_cache("KEY3", "old-value")

            results = []
            threads = [threading.Thread(target=lambda: results.append(secrets_manager.refresh_secret("KEY3"))) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 两个线程都拿到刷新后的值（等待者等待完成后读缓存）
            assert set(results) == {"gated-value"}
            assert len(calls) == 1
        finally:
            secrets_manager.client = original_client
