# @file plugins/reviewers/default/hooks.py
# @brief 默认审查器插件 hooks
# @create 2026-03-26

from core.hook_manager import hook_manager


@hook_manager.hook("reviewer_manager_approve_after")
def default_reviewer_approve(args, result):
    """默认审查器批准钩子"""
    pass


@hook_manager.hook("reviewer_manager_reject_after")
def default_reviewer_reject(args, result):
    """默认审查器拒绝钩子"""
    pass
