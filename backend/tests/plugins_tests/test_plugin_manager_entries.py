# @file backend/tests/plugins_tests/test_plugin_manager_entries.py
# @brief 插件注册表条目：禁用插件保留 manifest（验证修复）
# @create 2026-09-18

import sys
from pathlib import Path

# 项目根（plugins/ 与 backend/ 的父目录）加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.plugin_manager import PluginManager  # noqa: E402


def _write_plugin(plugins_dir: Path, key: str, manifest: str) -> Path:
    path = plugins_dir / key
    path.mkdir(parents=True)
    (path / "plugin.yaml").write_text(manifest, encoding="utf-8")
    return path


class TestDisabledEntryManifest:
    def test_disabled_entry_keeps_manifest(self, tmp_path):
        """禁用插件仍读取 plugin.yaml，供前端展示名称/描述"""
        plugins_dir = tmp_path / "plugins"
        _write_plugin(
            plugins_dir,
            "reviewers/example",
            'name: "Reviewer Example"\ntype: "reviewer"\nversion: "1.0.0"\n'
            'description: "demo"\nauthor: "tester"\n',
        )
        manager = PluginManager()
        manager.plugins_dir = plugins_dir

        entry = manager._load_entry("reviewers/example", {"enabled": False})

        assert entry["enabled"] is False
        assert entry["name"] == "Reviewer Example"
        assert entry["type"] == "reviewer"
        assert entry["manifest"]["version"] == "1.0.0"
        assert entry["manifest"]["author"] == "tester"
        assert entry["path"].endswith("reviewers/example")

    def test_disabled_entry_without_manifest(self, tmp_path):
        """无 plugin.yaml 的禁用插件回退 key 末段作为显示名"""
        plugins_dir = tmp_path / "plugins"
        (plugins_dir / "reviewers" / "empty").mkdir(parents=True)
        manager = PluginManager()
        manager.plugins_dir = plugins_dir

        entry = manager._load_entry("reviewers/empty", {"enabled": False})

        assert entry["enabled"] is False
        assert entry["name"] == "empty"
        assert entry["manifest"] == {}

    def test_disabled_entry_with_custom_path(self, tmp_path):
        """cfg.path 指向自定义目录时禁用条目同样解析 manifest"""
        plugins_dir = tmp_path / "plugins"
        custom = tmp_path / "custom-plugin"
        custom.mkdir()
        (custom / "plugin.yaml").write_text(
            'name: "Custom"\ntype: "reviewer"\n', encoding="utf-8"
        )
        manager = PluginManager()
        manager.plugins_dir = plugins_dir

        entry = manager._load_entry("reviewers/custom", {"enabled": False, "path": str(custom)})

        assert entry["name"] == "Custom"
        assert entry["type"] == "reviewer"
