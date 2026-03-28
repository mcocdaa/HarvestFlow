# @file plugins/reviewers/default/backend.py
# @brief 默认人工审核插件
# @create 2026-03-18

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DefaultReviewer:
    name = "default"
    description = "Default human reviewer - basic review interface"

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def get_extra_fields(self) -> List[Dict[str, Any]]:
        """获取额外字段

        Returns:
            字段定义列表
        """
        return [
            {
                "name": "quality_notes",
                "label": "Quality Notes",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "reviewer_tags",
                "label": "Reviewer Tags",
                "type": "tags",
                "required": False,
            },
        ]

    def validate(self, session: Dict) -> bool:
        """验证会话

        Args:
            session: 会话数据

        Returns:
            是否有效
        """
        if not session.get("messages"):
            return False
        return True


reviewer_plugin = DefaultReviewer()


def on_load():
    logger.info("[DefaultReviewer] Plugin loaded")


def get_reviewer():
    return reviewer_plugin
