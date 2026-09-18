# @file plugins/reviewers/example/backend.py
# @brief 示例审核插件：扩展字段定义与提交校验逻辑
# @create 2026-09-18

import logging
from typing import Dict, List, Optional

from core import database_manager

logger = logging.getLogger(__name__)

EXAMPLE_FIELDS: List[Dict] = [
    {
        "name": "data_quality",
        "label": "数据质量",
        "type": "select",
        "options": ["优秀", "良好", "一般", "较差"],
        "required": False,
    },
    {
        "name": "use_case",
        "label": "使用场景",
        "type": "text",
        "placeholder": "请输入该会话的使用场景",
        "required": False,
    },
    {
        "name": "needs_review",
        "label": "需要复查",
        "type": "checkbox",
        "required": False,
    },
]


def validate_review(session_id: str, action: str, extras: Optional[Dict] = None) -> Optional[str]:
    """提交校验：返回错误文案则阻止审批，None 表示放行"""
    if action != "approve":
        return None

    session = database_manager.session_get(session_id)
    if not session:
        return None

    messages = (session.get("content") or {}).get("messages", [])
    if len(messages) < 2:
        return "会话消息不足 2 条，不允许通过"

    if (extras or {}).get("data_quality") == "较差":
        return "数据质量标记为「较差」时不允许直接通过"

    return None
