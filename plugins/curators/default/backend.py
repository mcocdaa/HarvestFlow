# @file plugins/curators/default/backend.py
# @brief 默认审核器插件
# @create 2026-03-18

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

DEFAULT_BASE_SCORE = 3
MESSAGE_COUNT_THRESHOLD_1 = 10
MESSAGE_COUNT_THRESHOLD_2 = 20
MAX_SCORE = 5


class DefaultCurator:
    name = "default"
    description = "Default curator - passes all sessions without filtering"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.auto_approve_threshold = self.config.get("auto_approve_threshold", 4)

    def evaluate(self, session: Dict) -> Dict[str, Any]:
        """评估会话质量

        Args:
            session: 会话数据

        Returns:
            评估结果字典
        """
        score = self._calculate_score(session)

        return {
            "score": score,
            "is_high_value": True,
            "tags": self._extract_tags(session),
            "notes": "Default curator - passed all sessions",
        }

    def _calculate_score(self, session: Dict) -> int:
        """计算质量分数

        Args:
            session: 会话数据

        Returns:
            分数（0-5）
        """
        score = DEFAULT_BASE_SCORE

        if session.get("messages"):
            msg_count = len(session.get("messages", []))
            if msg_count > MESSAGE_COUNT_THRESHOLD_1:
                score += 1
            if msg_count > MESSAGE_COUNT_THRESHOLD_2:
                score += 1

        if session.get("tool_calls"):
            score += 1

        if session.get("final_output") or session.get("result"):
            score += 1

        return min(score, MAX_SCORE)

    def _extract_tags(self, session: Dict) -> List[str]:
        """提取标签

        Args:
            session: 会话数据

        Returns:
            标签列表
        """
        tags = []

        if session.get("task_type"):
            tags.append(session.get("task_type"))

        if session.get("agent_role"):
            tags.append(session.get("agent_role"))

        return list(set(tags))


curator_plugin = DefaultCurator()


def on_load():
    logger.info("[DefaultCurator] Plugin loaded")


def get_curator():
    return curator_plugin
