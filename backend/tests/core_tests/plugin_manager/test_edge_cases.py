# @file backend/tests/core_tests/plugin_manager/test_edge_cases.py
# @brief PluginManager 边界情况测试
# @create 2026-03-27

import os
import yaml
import argparse

from core import setting_manager
from core.plugin_manager import PluginManager


class TestPluginManagerEdgeCases:
    def setup_method(self):
        self.original_plugins_dir = setting_manager.get("PLUGINS_DIR")
        self.manager = None

    def teardown_method(self):
        setting_manager.set("PLUGINS_DIR", self.original_plugins_dir or "")

    def test_plugin_dir_with_init_but_no_plugin_yaml_skipped(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_dir = os.path.join(plugins_dir, "test_plugin")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "__init__.py"), "w") as f:
            f.write("# Test init\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test_plugin": {
                        "enabled": True
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", str(plugins_dir))
        args_minimal.plugins_dir = str(plugins_dir)
        self.manager = PluginManager()
        self.manager.init(args_minimal)
        self.manager.register_hooks()

        assert len(self.manager.plugins) == 0

    def test_not_py_file_not_dir_skipped(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_path = os.path.join(plugins_dir, "test.txt")
        with open(plugin_path, "w") as f:
            f.write("not a python file\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test": {
                        "enabled": True,
                        "path": "test.txt"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)
        self.manager.register_hooks()

        assert len(self.manager.loaded_plugins) == 0

    def test_import_error_cleans_up_sys_modules(self, args_minimal, temp_plugins_dir):
        import sys
        plugins_dir = str(temp_plugins_dir)
        py_path = os.path.join(plugins_dir, "bad_import.py")
        with open(py_path, "w") as f:
            f.write("import this_module_does_not_exist_ever\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "bad_import": {
                        "enabled": True,
                        "path": "bad_import.py"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        module_name = "plugins.bad_import"
        assert module_name not in sys.modules
        self.manager.register_hooks()
        assert module_name not in sys.modules
        assert "bad_import" not in self.manager.loaded_plugins

    def test_register_hooks_no_plugins_dir(self, args_minimal):
        setting_manager.set("PLUGINS_DIR", "")
        manager = PluginManager()
        manager.plugins_dir = None
        manager.register_hooks()
        assert len(manager.loaded_plugins) == 0

    def test_directory_plugin_with_valid_init_and_plugin_yaml(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_dir = os.path.join(plugins_dir, "valid_plugin")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "__init__.py"), "w") as f:
            f.write("TEST_VAR = 123\n")
        with open(os.path.join(plugin_dir, "plugin.yaml"), "w") as f:
            yaml.dump({"name": "Valid Plugin", "type": "collector"}, f)

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "valid_plugin": {
                        "enabled": True
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)
        self.manager.register_hooks()

        assert len(self.manager.plugins) == 1
        assert "valid_plugin" in self.manager.loaded_plugins
        assert self.manager.plugin_modules["valid_plugin"].TEST_VAR == 123

    def test_plugin_yaml_read_exception_skipped(self, args_minimal, temp_plugins_dir):
        plugins_dir = str(temp_plugins_dir)
        plugin_dir = os.path.join(plugins_dir, "broken_yaml")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "__init__.py"), "w") as f:
            f.write("TEST_VAR = 123\n")
        with open(os.path.join(plugin_dir, "plugin.yaml"), "w") as f:
            f.write("this: is: invalid: yaml")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "broken_yaml": {
                        "enabled": True
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        assert len(self.manager.plugins) == 0

    def test_spec_none_skips_plugin(self, args_minimal, temp_plugins_dir, monkeypatch):
        import importlib.util
        plugins_dir = str(temp_plugins_dir)
        py_path = os.path.join(plugins_dir, "test.py")
        with open(py_path, "w") as f:
            f.write("TEST = 1\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test": {
                        "enabled": True,
                        "path": "test.py"
                    }
                }
            }, f)

        def mock_spec_from_file_location(*args, **kwargs):
            return None

        monkeypatch.setattr(importlib.util, "spec_from_file_location", mock_spec_from_file_location)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)
        self.manager.register_hooks()

        assert len(self.manager.loaded_plugins) == 0

    def test_spec_loader_none_skips_plugin(self, args_minimal, temp_plugins_dir, monkeypatch):
        import importlib.util
        plugins_dir = str(temp_plugins_dir)
        py_path = os.path.join(plugins_dir, "test.py")
        with open(py_path, "w") as f:
            f.write("TEST = 1\n")

        with open(os.path.join(plugins_dir, "plugins.yaml"), "w") as f:
            yaml.dump({
                "plugins": {
                    "test": {
                        "enabled": True,
                        "path": "test.py"
                    }
                }
            }, f)

        setting_manager.set("PLUGINS_DIR", plugins_dir)
        args_minimal.plugins_dir = plugins_dir
        self.manager = PluginManager()
        self.manager.init(args_minimal)

        original = importlib.util.spec_from_file_location

        def mock_spec_from_file_location(*args, **kwargs):
            spec = original(*args, **kwargs)
            spec.loader = None
            return spec

        monkeypatch.setattr(importlib.util, "spec_from_file_location", mock_spec_from_file_location)

        self.manager.register_hooks()

        assert len(self.manager.loaded_plugins) == 0
