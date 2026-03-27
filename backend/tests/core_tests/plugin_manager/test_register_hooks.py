# @file backend/tests/core_tests/plugin_manager/test_register_hooks.py
# @brief PluginManager 注册钩子测试
# @create 2026-03-27

import os
import yaml
import argparse

from core import setting_manager
from core.plugin_manager import PluginManager


class TestPluginManagerRegisterHooks:
    def setup_method(self):
        self.original_plugins_dir = setting_manager.get("PLUGINS_DIR")
        self.manager = None

    def teardown_method(self):
        setting_manager.set("PLUGINS_DIR", self.original_plugins_dir or "")

    def test_register_arguments(self):
        self.manager = PluginManager()
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_get_all_returns_loaded_plugins(self, args_minimal):
        setting_manager.set("PLUGINS_DIR", "")
        manager = PluginManager()
        manager.loaded_plugins = {
            "test1": {"name": "Test 1", "enabled": True},
            "test2": {"name": "Test 2", "enabled": True}
        }

        result = manager.get_all()
        assert len(result) == 2

    def test_register_hooks_no_plugins_dir(self, args_minimal):
        setting_manager.set("PLUGINS_DIR", "")
        manager = PluginManager()
        manager.plugins_dir = None
        manager.register_hooks()

        assert len(manager.loaded_plugins) == 0

    def test_register_hooks_loads_py_file(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        py_path = os.path.join(plugins_dir, "test_module.py")
        with open(py_path, "w") as f:
            f.write("TEST_VAR = 42\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test_module": {
                        "enabled": True,
                        "path": "test_module.py"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)
        self.manager.register_hooks()

        assert len(self.manager.loaded_plugins) == 1
        assert "test_module" in self.manager.plugin_modules
        assert self.manager.plugin_modules["test_module"].TEST_VAR == 42

    def test_register_hooks_no_init_py(self, args_minimal, temp_plugins_dir):
        plugins_dir = temp_plugins_dir
        plugin_dir = os.path.join(plugins_dir, "test_plugin")
        os.makedirs(plugin_dir)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test_plugin": {
                        "enabled": True,
                        "path": "test_plugin"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", str(plugins_dir))
        args_minimal.plugins_dir = str(plugins_dir)
        self.manager = PluginManager()
        self.manager.init(args_minimal)
        self.manager.register_hooks()

        assert len(self.manager.loaded_plugins) == 0

    def test_register_hooks_import_error(self, args_minimal, temp_plugins_dir):
        plugins_dir = temp_plugins_dir
        py_path = os.path.join(plugins_dir, "bad_plugin.py")
        with open(py_path, "w") as f:
            f.write("import nonexistent_module_that_does_not_exist\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "bad_plugin": {
                        "enabled": True,
                        "path": "bad_plugin.py"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", str(plugins_dir))
        args_minimal.plugins_dir = str(plugins_dir)
        self.manager = PluginManager()
        self.manager.init(args_minimal)
        self.manager.register_hooks()

        assert len(self.manager.loaded_plugins) == 0
