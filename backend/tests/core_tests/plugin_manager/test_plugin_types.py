# @file backend/tests/core_tests/plugin_manager/test_plugin_types.py
# @brief PluginManager 不同插件类型加载测试
# @create 2026-03-27

import os
import yaml
import argparse

from core import setting_manager
from core.plugin_manager import PluginManager


class TestPluginManagerPluginTypes:
    def setup_method(self):
        self.original_plugins_dir = setting_manager.get("PLUGINS_DIR")
        self.manager = None

    def teardown_method(self):
        setting_manager.set("PLUGINS_DIR", self.original_plugins_dir or "")

    def test_init_with_plugins(self, args_minimal, temp_plugins_dir, plugin_yaml_content):
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
        args_minimal.plugins_dir = str(plugins_dir)
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 1
        assert "collectors/test-plugin" in self.manager.plugins

    def test_py_file_plugin(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        py_path = os.path.join(plugins_dir, "test_plugin.py")
        with open(py_path, "w") as f:
            f.write("# Test plugin\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test_plugin": {
                        "enabled": True,
                        "path": "test_plugin.py"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 1
        assert "test_plugin" in self.manager.plugins
        assert self.manager.plugins["test_plugin"]["type"] == "unknown"

    def test_absolute_path_plugin(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_dir = os.path.join(plugins_dir, "myplugin")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "plugin.yaml"), "w") as f:
            yaml.dump({"name": "My Plugin", "type": "collector"}, f)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "myplugin": {
                        "enabled": True,
                        "path": os.path.join(plugins_dir, "myplugin")
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 1
        assert self.manager.plugins["myplugin"]["name"] == "My Plugin"

    def test_default_path_implicit(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_dir = os.path.join(plugins_dir, "test_default")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "plugin.yaml"), "w") as f:
            yaml.dump({"name": "Test Default", "type": "collector"}, f)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test_default": {
                        "enabled": True
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 1
        assert "test_default" in self.manager.plugins
