# @file backend/tests/core_tests/plugin_manager/test_helpers.py
# @brief PluginManager 私有辅助方法测试
# @create 2026-08-10

import yaml
from pathlib import Path

from core.plugin_manager import PluginManager


def _make_manager(tmp_path) -> PluginManager:
    manager = PluginManager.__new__(PluginManager)
    manager.logger = __import__('logging').getLogger('test_plugin_helpers')
    manager.plugins_dir = Path(tmp_path)
    return manager


class TestModuleName:
    def test_replaces_forward_slash(self):
        manager = _make_manager(Path('/tmp'))
        assert manager._module_name("collectors/openclaw") == "plugins.collectors.openclaw"

    def test_replaces_os_sep(self):
        manager = _make_manager(Path('/tmp'))
        assert manager._module_name("collectors" + __import__('os').sep + "openclaw") == "plugins.collectors.openclaw"

    def test_plain_key(self):
        manager = _make_manager(Path('/tmp'))
        assert manager._module_name("simple") == "plugins.simple"


class TestReadYaml:
    def test_reads_valid_yaml(self, tmp_path):
        path = tmp_path / "plugin.yaml"
        path.write_text("name: demo\ntype: collector\n", encoding='utf-8')
        manager = _make_manager(tmp_path)
        assert manager._read_yaml(path) == {"name": "demo", "type": "collector"}

    def test_missing_file_returns_none(self, tmp_path):
        manager = _make_manager(tmp_path)
        assert manager._read_yaml(tmp_path / "not_exist.yaml") is None

    def test_invalid_yaml_returns_none(self, tmp_path):
        path = tmp_path / "bad.yaml"
        path.write_text("key: [unclosed\n", encoding='utf-8')
        manager = _make_manager(tmp_path)
        assert manager._read_yaml(path) is None

    def test_empty_file_returns_empty(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding='utf-8')
        manager = _make_manager(tmp_path)
        assert manager._read_yaml(path) == {}


class TestReadManifest:
    def test_directory_reads_plugin_yaml(self, tmp_path):
        plugin_dir = tmp_path / "demo"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.yaml").write_text(
            "name: demo\ntype: curator\n", encoding='utf-8'
        )
        manager = _make_manager(tmp_path)
        assert manager._read_manifest(plugin_dir) == {"name": "demo", "type": "curator"}

    def test_py_file_builds_default_manifest(self, tmp_path):
        path = tmp_path / "single.py"
        path.write_text("", encoding='utf-8')
        manager = _make_manager(tmp_path)
        assert manager._read_manifest(path) == {
            "name": "single",
            "type": "unknown",
            "backend_entry": "single.py",
        }


class TestLoadEntry:
    def test_enabled_directory_with_manifest(self, tmp_path):
        plugin_dir = tmp_path / "collectors" / "demo"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text(
            yaml.safe_dump({"name": "Demo", "type": "collector", "version": "1.0.0"}),
            encoding='utf-8',
        )
        manager = _make_manager(tmp_path)
        entry = manager._load_entry("collectors/demo", {"enabled": True})

        assert entry["enabled"] is True
        assert entry["name"] == "Demo"
        assert entry["type"] == "collector"
        assert entry["manifest"]["version"] == "1.0.0"
        assert str(Path(entry["path"])) == str(plugin_dir.resolve())

    def test_disabled_entry_returns_disabled_structure(self, tmp_path):
        manager = _make_manager(tmp_path)
        entry = manager._load_entry("collectors/demo", {"enabled": False})

        assert entry == {
            "enabled": False,
            "path": "",
            "name": "demo",
            "type": "unknown",
            "manifest": {},
        }

    def test_single_py_file_entry(self, tmp_path):
        plugin_path = tmp_path / "solo.py"
        plugin_path.write_text("", encoding='utf-8')
        manager = _make_manager(tmp_path)
        entry = manager._load_entry("solo", {"enabled": True, "path": "solo.py"})

        assert entry["enabled"] is True
        assert entry["name"] == "solo"
        assert entry["type"] == "unknown"
        assert entry["manifest"]["backend_entry"] == "solo.py"

    def test_missing_path_returns_none(self, tmp_path):
        manager = _make_manager(tmp_path)
        assert manager._load_entry("ghost", {"enabled": True}) is None

    def test_missing_manifest_returns_none(self, tmp_path):
        plugin_dir = tmp_path / "no-manifest"
        plugin_dir.mkdir()
        manager = _make_manager(tmp_path)
        assert manager._load_entry("no-manifest", {"enabled": True}) is None

    def test_none_config_returns_none(self, tmp_path):
        manager = _make_manager(tmp_path)
        assert manager._load_entry("any", None) is None
