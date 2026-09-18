# @file backend/tests/plugins_tests/test_reviewer_example.py
# @brief 示例审核插件测试（钩子注册与字段贡献）
# @create 2026-09-18

import importlib
import sys
from pathlib import Path

# 项目根（plugins/ 与 backend/ 的父目录）加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in (str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.hook_manager import hook_manager  # noqa: E402
from managers.reviewer_manager import reviewer_manager  # noqa: E402


def test_example_plugin_registers_hooks():
    """导入示例插件 hooks 后：扩展字段经 after 钩子聚合"""
    hook_manager.clear()
    import plugins.reviewers.example.hooks as hooks_module  # noqa: F401

    importlib.reload(hooks_module)
    fields = reviewer_manager.get_extra_fields()
    assert [f["name"] for f in fields] == ["data_quality", "use_case", "needs_review"]
    assert fields[0]["type"] == "select"
    hook_manager.clear()


def test_validate_review_skips_non_approve_actions():
    """非 approve 动作不触发校验（无需数据库）"""
    from plugins.reviewers.example.backend import validate_review

    assert validate_review("any-session", "reject", {}) is None
