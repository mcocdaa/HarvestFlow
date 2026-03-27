# @file plugins/curators/openclaw/hooks.py
# @brief OpenClaw 审核器插件 hooks
# @create 2026-03-26

from core.hook_manager import hook_manager


@hook_manager.hook("curator_manager_evaluate_after")
def openclaw_curator_evaluate(args, result):
    """OpenClaw 审核器评估钩子"""
    pass
