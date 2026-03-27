# @file backend/tests/core_tests/plugin_manager/test_secrets.py
# @brief PluginManager 密钥获取测试
# @create 2026-03-27

import os
import yaml
import argparse

from core import setting_manager
from core.plugin_manager import PluginManager


class TestPluginManagerSecrets:
    def setup_method(self):
        self.original_plugins_dir = setting_manager.get("PLUGINS_DIR")
        self.manager = None

    def teardown_method(self):
        setting_manager.set("PLUGINS_DIR", self.original_plugins_dir or "")

    def test_get_plugin_secrets(self, args_minimal, temp_plugins_dir, plugin_yaml_content):
        plugins_dir = str(temp_plugins_dir)
        os.makedirs(os.path.join(plugins_dir, "collectors", "test-plugin"))
        with open(os.path.join(plugins_dir, "collectors", "test-plugin", "plugin.yaml"), "w") as f:
            f.write(plugin_yaml_content)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "collectors/test-plugin": {
                        "enabled": True
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        secrets = self.manager.get_plugin_secrets()
        assert len(secrets) == 1
        assert secrets[0]["name"] == "TEST_API_KEY"

    def test_empty_secrets_list(self, args_minimal):
        setting_manager.set("PLUGINS_DIR", "")
        manager = PluginManager()
        manager.plugins = {}
        secrets = manager.get_plugin_secrets()
        assert len(secrets) == 0

    def test_secrets_with_missing_fields(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_dir = os.path.join(plugins_dir, "collectors", "test")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "plugin.yaml"), "w") as f:
            yaml.dump({
                "name": "Test",
                "type": "collector",
                "secrets": [
                    {"name": "TEST_KEY"}
                ]
            }, f)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "collectors/test": {"enabled": True}
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        secrets = self.manager.get_plugin_secrets()
        assert len(secrets) == 1
        assert secrets[0]["description"] == ""
        assert secrets[0]["default"] is None
