# @file plugins/examples/reviewer-example/backend.py
# @brief Example reviewer plugin implementation
# @create 2026-03-28

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ExampleReviewer:
    name = "reviewer-example"
    description = "Example reviewer plugin - demonstrates how to build a custom reviewer"

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def get_extra_fields(self) -> List[Dict]:
        """获取额外字段定义

        Returns:
            额外字段定义列表
        """
        return [
            {
                'name': 'data_quality',
                'label': '数据质量',
                'type': 'select',
                'options': ['优秀', '良好', '一般', '较差'],
                'required': False
            },
            {
                'name': 'use_case',
                'label': '使用场景',
                'type': 'text',
                'placeholder': '请输入该会话的使用场景',
                'required': False
            },
            {
                'name': 'needs_review',
                'label': '需要复查',
                'type': 'checkbox',
                'required': False
            }
        ]

    def validate(self, session: Dict) -> bool:
        """验证会话

        Args:
            session: 会话数据

        Returns:
            是否验证通过
        """
        try:
            logger.debug(f"[ExampleReviewer] Validating session")

            # 验证规则1：必须有消息
            messages = session.get('content', {}).get('messages', [])
            if not messages:
                logger.warning("[ExampleReviewer] Validation failed: no messages")
                return False

            # 验证规则2：消息数量至少2条
            if len(messages) < 2:
                logger.warning("[ExampleReviewer] Validation failed: not enough messages")
                return False

            # 验证规则3：第一条消息必须是用户消息
            first_msg = messages[0]
            if isinstance(first_msg, dict) and first_msg.get('role') != 'user':
                logger.warning("[ExampleReviewer] Validation failed: first message not from user")
                return False

            logger.info("[ExampleReviewer] Validation passed")
            return True

        except Exception as e:
            logger.error(f"[ExampleReviewer] Validation error: {e}")
            return False

    def before_approve(self, session: Dict, notes: str, score: int) -> Dict:
        """审批前钩子

        Args:
            session: 会话数据
            notes: 评审意见
            score: 评分

        Returns:
            修改后的会话数据
        """
        logger.info(f"[ExampleReviewer] Before approve hook called")

        # 可以在这里添加审批前的逻辑
        # 例如：添加元数据、记录时间戳等
        if 'metadata' not in session:
            session['metadata'] = {}

        session['metadata']['approved_by_plugin'] = self.name
        session['metadata']['approval_timestamp'] = 'now'

        return session

    def before_reject(self, session: Dict, notes: str, score: int) -> Dict:
        """拒绝前钩子

        Args:
            session: 会话数据
            notes: 评审意见
            score: 评分

        Returns:
            修改后的会话数据
        """
        logger.info(f"[ExampleReviewer] Before reject hook called")

        if 'metadata' not in session:
            session['metadata'] = {}

        session['metadata']['rejected_by_plugin'] = self.name

        return session


reviewer_plugin = ExampleReviewer()


def on_load():
    logger.info("[ExampleReviewer] Plugin loaded")


def get_reviewer():
    return reviewer_plugin
