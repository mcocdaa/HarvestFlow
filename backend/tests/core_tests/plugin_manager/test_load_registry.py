# @file backend/tests/core_tests/plugin_manager/test_load_registry.py
# @brief PluginManager 加载注册表测试
# @create 2026-03-27

import os
import tempfile
import yaml
import argparse

import pytest

from core import setting_manager
from core.plugin_manager import PluginManager


class TestPluginManagerLoadRegistry:
    def setup_method(self):
        self.original_plugins_dir = setting_manager.get("PLUGINS_DIR")
        self.manager = None

    def teardown_method(self):
        setting_manager.set("PLUGINS_DIR", self.original_plugins_dir or "")

    def test_init_empty_plugins_dir(self, args_minimal):
        setting_manager.set("PLUGINS_DIR", "")
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert self.manager.plugins_dir is not None
        assert len(self.manager.plugins) == 0

    def test_plugins_dir_not_exists(self, args_minimal, tmp_path):
        non_existent = tmp_path / "non_existent_plugins"
        setting_manager.set("PLUGINS_DIR", str(non_existent))
        manager = PluginManager()
        plugins = manager._load_registry()

        assert len(plugins) == 0

    def test_plugins_yaml_not_exists(self, args_minimal, tmp_path):
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        setting_manager.set("PLUGINS_DIR", str(plugins_dir))
        manager = PluginManager()
        plugins = manager._load_registry()

        assert len(plugins) == 0

    def test_plugins_yaml_invalid_yaml(self, args_minimal, tmp_path):
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        registry_path = plugins_dir / "plugins.yaml"
        with open(registry_path, "w") as f:
            f.write("invalid: yaml: [")

        setting_manager.set("PLUGINS_DIR", str(plugins_dir))
        manager = PluginManager()
        plugins = manager._load_registry()

        assert len(plugins) == 0

    def test_disabled_plugin_skipped(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        os.makedirs(os.path.join(plugins_dir, "collectors", "test-plugin"))

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "collectors/test-plugin": {
                        "enabled": False
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 0

    def test_plugin_path_does_not_exist(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "nonexistent/plugin": {
                        "enabled": True
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 0

    def test_plugin_missing_plugin_yaml(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        os.makedirs(os.path.join(plugins_dir, "collectors", "test-plugin"))

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

        assert len(self.manager.plugins) == 0

    def test_plugin_yaml_invalid(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_dir = os.path.join(plugins_dir, "collectors", "test-plugin")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "plugin.yaml"), "w") as f:
            f.write("bad yaml [")

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

        assert len(self.manager.plugins) == 0

    def test_invalid_path_type_skipped(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        os.makedirs(os.path.join(plugins_dir, "test"))

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test": {
                        "enabled": True,
                        "path": "test/invalid.txt"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 0

    def test_general_exception_in_processing(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test": None
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 0
