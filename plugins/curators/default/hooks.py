# @file plugins/curators/default/hooks.py
# @brief 默认审核器插件 hooks
# @create 2026-03-26

from core.hook_manager import hook_manager


@hook_manager.hook("curator_manager_evaluate_after")
def default_curator_evaluate(args, result):
    """默认审核器评估钩子"""
    pass
