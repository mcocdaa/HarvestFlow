# @file plugins/examples/curator-example/backend.py
# @brief Example curator plugin implementation
# @create 2026-03-28

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ExampleCurator:
    name = "curator-example"
    description = "Example curator plugin - demonstrates how to build a custom curator"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.custom_config = self.config.get("custom_config", {})

    def evaluate(self, session: Dict) -> Dict:
        """评估会话质量

        Args:
            session: 会话数据

        Returns:
            评估结果，包含 score, is_high_value, tags
        """
        try:
            logger.debug(f"[ExampleCurator] Evaluating session")

            # 计算评分
            score = self._calculate_score(session)

            # 判断是否为高价值
            is_high_value = score >= 4

            # 生成标签
            tags = self._generate_tags(session, score)

            result = {
                'score': score,
                'is_high_value': is_high_value,
                'tags': tags
            }

            logger.info(f"[ExampleCurator] Evaluation complete: score={score}, is_high_value={is_high_value}")
            return result

        except Exception as e:
            logger.error(f"[ExampleCurator] Evaluation error: {e}")
            return {
                'score': 3,
                'is_high_value': False,
                'tags': ['error']
            }

    def _calculate_score(self, session: Dict) -> int:
        """计算会话评分

        Args:
            session: 会话数据

        Returns:
            评分 (1-5)
        """
        score = 3  # 默认中等评分

        # 获取消息列表
        messages = session.get('content', {}).get('messages', [])
        message_count = len(messages)

        # 规则1：消息数量
        min_count = self.custom_config.get('min_message_count', 2)
        if message_count >= min_count:
            score += 1
        if message_count >= 5:
            score += 1

        # 规则2：检查是否有工具调用
        has_tools = self._has_tool_calls(messages)
        if has_tools:
            score += 1

        # 规则3：检查消息长度
        max_length = self.custom_config.get('max_message_length', 10000)
        avg_length = self._calculate_avg_message_length(messages)
        if avg_length > 100 and avg_length < max_length:
            score += 1

        # 确保评分在 1-5 范围内
        return max(1, min(5, score))

    def _generate_tags(self, session: Dict, score: int) -> List[str]:
        """生成标签

        Args:
            session: 会话数据
            score: 评分

        Returns:
            标签列表
        """
        tags = []

        # 质量标签
        if score >= 4:
            tags.append('high-quality')
        elif score <= 2:
            tags.append('low-quality')

        # 消息数量标签
        messages = session.get('content', {}).get('messages', [])
        if len(messages) > 5:
            tags.append('long-conversation')

        # 工具调用标签
        if self._has_tool_calls(messages):
            tags.append('tool-use')

        return tags

    def _has_tool_calls(self, messages: List[Dict]) -> bool:
        """检查是否有工具调用

        Args:
            messages: 消息列表

        Returns:
            是否有工具调用
        """
        for msg in messages:
            if isinstance(msg, dict):
                if 'tool_calls' in msg or 'tool_call_id' in msg:
                    return True
                content = msg.get('content', '')
                if isinstance(content, str) and ('function_call' in content or 'tool_call' in content):
                    return True
        return False

    def _calculate_avg_message_length(self, messages: List[Dict]) -> float:
        """计算平均消息长度

        Args:
            messages: 消息列表

        Returns:
            平均消息长度
        """
        if not messages:
            return 0

        total_length = 0
        count = 0

        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get('content', '')
                if isinstance(content, str):
                    total_length += len(content)
                    count += 1

        return total_length / count if count > 0 else 0


curator_plugin = ExampleCurator()


def on_load():
    logger.info("[ExampleCurator] Plugin loaded")


def get_curator():
    return curator_plugin
