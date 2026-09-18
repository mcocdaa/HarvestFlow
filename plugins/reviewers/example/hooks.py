# @file plugins/reviewers/example/hooks.py
# @brief 示例审核插件 hooks：扩展字段 + 提交前校验
# @create 2026-09-18

import logging

from core.hook_manager import hook_manager
from plugins.reviewers.example.backend import EXAMPLE_FIELDS, validate_review

logger = logging.getLogger(__name__)


@hook_manager.hook("reviewer_manager_extra_fields_after")
def reviewer_example_extra_fields(result, self):
    """after 钩子：向审核面板追加扩展字段定义"""
    return list(result) + EXAMPLE_FIELDS


@hook_manager.hook("reviewer_manager_review_before")
def reviewer_example_review_before(self, session_id, target_status, action, notes=None, score=None, extras=None):
    """before 钩子：返回错误结果时短路审批（API 层映射为 400）"""
    error = validate_review(session_id, action, extras)
    if error:
        logger.info(f"[ReviewerExample] 阻止 {action} {session_id}: {error}")
        return {"session_id": session_id, "error": error}
    return None
