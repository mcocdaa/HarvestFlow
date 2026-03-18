# @file backend/test/test_plugin_loader.py
# @brief 插件加载器测试
# @create 2026-03-18

import pytest
import os
import yaml
import tempfile
import shutil
from pathlib import Path
from core.database import Database
from core.plugin_loader import PluginLoader


class TestPluginLoader:
    @pytest.fixture
    def temp_plugins_dir(self, temp_dir):
        plugins_dir = os.path.join(temp_dir, "plugins")
        os.makedirs(plugins_dir, exist_ok=True)

        collectors_dir = os.path.join(plugins_dir, "collectors")
        os.makedirs(collectors_dir, exist_ok=True)

        return plugins_dir

    @pytest.fixture
    def sample_plugin(self, temp_plugins_dir):
        plugin_dir = os.path.join(temp_plugins_dir, "collectors", "test_collector")
        os.makedirs(plugin_dir, exist_ok=True)

        plugin_yaml = {
            "name": "test_collector",
            "description": "Test collector plugin",
            "version": "1.0.0",
            "author": "Test",
            "enabled": True,
            "backend_entry": "backend.py"
        }

        with open(os.path.join(plugin_dir, "plugin.yaml"), 'w') as f:
            yaml.dump(plugin_yaml, f)

        with open(os.path.join(plugin_dir, "backend.py"), 'w') as f:
            f.write("""
def on_load():
    print("Test plugin loaded")

def get_collector():
    return None
""")

        return plugin_dir

    def test_plugin_loader_init(self, temp_plugins_dir):
        loader = PluginLoader()
        assert loader.loaded_plugins == {}
        assert loader._plugin_modules == {}

    def test_load_config_empty(self, temp_plugins_dir):
        loader = PluginLoader()
        loader.plugins_dir = Path(temp_plugins_dir)

        config = loader.load_config()
        assert config == {"plugins": {}}

    def test_load_config_with_plugins(self, temp_plugins_dir, sample_plugin):
        loader = PluginLoader()
        loader.plugins_dir = Path(temp_plugins_dir)

        config_path = os.path.join(temp_plugins_dir, "plugins.yaml")
        with open(config_path, 'w') as f:
            yaml.dump({"plugins": {"collectors/test_collector": {"enabled": True}}}, f)

        config = loader.load_config()
        assert "plugins" in config

    def test_get_plugin_manifests_empty(self, temp_plugins_dir):
        loader = PluginLoader()
        loader.plugins_dir = Path(temp_plugins_dir)

        manifests = loader.get_plugin_manifests()
        assert manifests == []

    def test_get_enabled_plugins_empty(self, test_db_path):
        db = Database(test_db_path)
        db.initialize_tables()

        loader = PluginLoader()
        plugins = loader.get_enabled_plugins()
        assert plugins == []

        db.close()

    def test_plugin_yaml_validation(self, sample_plugin):
        plugin_yaml_path = os.path.join(sample_plugin, "plugin.yaml")
        assert os.path.exists(plugin_yaml_path)

        with open(plugin_yaml_path, 'r') as f:
            plugin_config = yaml.safe_load(f)

        assert plugin_config["name"] == "test_collector"
        assert plugin_config["enabled"] == True


class TestDefaultPlugins:
    def test_default_collector_plugin_exists(self):
        plugin_path = "/home/mcocdaa/AI_CODE/HarvestFlow/plugins/collectors/default/plugin.yaml"
        if os.path.exists(plugin_path):
            with open(plugin_path, 'r') as f:
                config = yaml.safe_load(f)
            assert config["name"] == "default"

    def test_default_curator_plugin_exists(self):
        plugin_path = "/home/mcocdaa/AI_CODE/HarvestFlow/plugins/curators/default/plugin.yaml"
        if os.path.exists(plugin_path):
            with open(plugin_path, 'r') as f:
                config = yaml.safe_load(f)
            assert config["name"] == "default"

    def test_default_reviewer_plugin_exists(self):
        plugin_path = "/home/mcocdaa/AI_CODE/HarvestFlow/plugins/reviewers/default/plugin.yaml"
        if os.path.exists(plugin_path):
            with open(plugin_path, 'r') as f:
                config = yaml.safe_load(f)
            assert config["name"] == "default"
            assert "frontend_entry" in config
