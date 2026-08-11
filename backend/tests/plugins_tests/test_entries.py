# @file backend/tests/plugins_tests/test_entries.py
# @brief 插件入口导入冒烟测试
# @create 2026-08-10

import sys
from pathlib import Path

import pytest

# 项目根（plugins/ 与 backend/ 的父目录）加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.hook_manager import hook_manager  # noqa: E402


@pytest.fixture(autouse=True)
def clean_hooks():
    """每个用例后清理钩子，避免污染其他测试"""
    yield
    hook_manager.clear()


class TestPluginEntries:
    def test_openclaw_collector_imports_and_registers_hooks(self):
        import plugins.collectors.openclaw  # noqa: F401

        assert "collector_manager_scan_after" in hook_manager._hooks
        assert "collector_manager_parse_before" in hook_manager._hooks

    def test_infisical_imports_and_registers_hooks(self):
        import plugins.services.infisical  # noqa: F401

        assert "secrets_manager_register_arguments" in hook_manager._hooks
        assert "secrets_manager_init_before" in hook_manager._hooks

    def test_example_plugins_import(self):
        import plugins.examples.collector_example  # noqa: F401
        import plugins.examples.curator_example  # noqa: F401
        import plugins.examples.reviewer_example  # noqa: F401
        import plugins.examples.service_example  # noqa: F401
