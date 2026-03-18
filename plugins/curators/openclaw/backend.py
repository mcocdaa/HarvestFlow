# @file plugins/curators/openclaw/backend.py
# @brief OpenClaw 会话审核器插件
# @create 2026-03-18

import re
from typing import Dict, List


class OpenClawCurator:
    name = "openclaw"
    description = "OpenClaw-specific curator - scores sessions based on tool calls, decision chains, and outputs"

    # 文件扩展名模式
    FILE_EXTENSIONS = [".py", ".ts", ".js", ".json", ".md", ".yaml", ".yml", ".txt", ".sh", ".sql", ".xml", ".html", ".css"]

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def evaluate(self, session: Dict) -> Dict:
        """评估会话并返回评分结果"""
        score = 2  # 基础分
        score_reasons = ["基础分"]

        # 检查工具调用成功
        if self._check_tool_call_success(session):
            score += 1
            score_reasons.append("工具调用成功")

        # 检查多步决策链
        if self._check_decision_chain(session):
            score += 1
            score_reasons.append("多步决策链 (≥3轮)")

        # 检查明确输出
        if self._check_explicit_output(session):
            score += 1
            score_reasons.append("明确的最终输出")

        # message_count > 20 加分
        message_count = session.get("message_count", 0)
        if message_count > 20:
            score += 1
            score_reasons.append(f"消息数较多 ({message_count})")

        # 最高5分
        score = min(score, 5)

        # 判断高价值
        is_high_value = score >= 3

        # 提取标签
        tags = self._extract_tags(session)

        return {
            "score": score,
            "is_high_value": is_high_value,
            "tags": tags,
            "score_reasons": score_reasons,
        }

    def _check_tool_call_success(self, session: Dict) -> bool:
        """检查是否有工具调用成功（has_tool_calls=True 且无 error）"""
        if not session.get("has_tool_calls", False):
            return False

        messages = session.get("messages", [])
        for msg in messages:
            if msg.get("role") != "assistant":
                continue

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                continue

            for tc in tool_calls:
                if isinstance(tc, dict):
                    # 如果有 tool_result 且没有 error，认为成功
                    tc_type = tc.get("type", "")
                    if tc_type == "tool_result":
                        content = tc.get("content", "")
                        if isinstance(content, str) and "error" in content.lower():
                            return False
                    # 有 tool_use 就认为有工具调用
                    if tc_type == "tool_use":
                        return True

        return session.get("has_tool_calls", False)

    def _check_decision_chain(self, session: Dict) -> bool:
        """检查是否有 ≥3 轮 assistant 消息（每轮含 tool_use）"""
        messages = session.get("messages", [])
        assistant_with_tool_count = 0

        for msg in messages:
            if msg.get("role") != "assistant":
                continue

            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            # 检查是否有 tool_use
            has_tool_use = False
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        has_tool_use = True
                        break

            if not has_tool_use and tool_calls:
                # 检查 tool_calls 列表
                for tc in tool_calls:
                    if isinstance(tc, dict) and tc.get("type") == "tool_use":
                        has_tool_use = True
                        break

            if has_tool_use:
                assistant_with_tool_count += 1

            if assistant_with_tool_count >= 3:
                return True

        return False

    def _check_explicit_output(self, session: Dict) -> bool:
        """检查 assistant 消息中是否包含代码块或文件路径"""
        messages = session.get("messages", [])

        for msg in messages:
            if msg.get("role") != "assistant":
                continue

            content = msg.get("content", "")
            if not content:
                continue

            # 检查代码块：``` 出现次数 ≥ 2（开头+结尾）
            code_block_count = content.count("```")
            if code_block_count >= 2:
                return True

            # 检查文件路径
            if self._has_file_path(content):
                return True

        return False

    def _has_file_path(self, text: str) -> bool:
        """检查文本中是否包含文件路径"""
        for ext in self.FILE_EXTENSIONS:
            # 匹配包含扩展名的路径模式
            pattern = rf'[\w\\/:][\w\s\\/:-]*\.{ext[1:]}(\s|$)'
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_tags(self, session: Dict) -> List[str]:
        """从 agent_id、tools_used、内容关键词提取标签"""
        tags = []

        # 从 agent_id 添加标签
        agent_id = session.get("agent_id")
        if agent_id:
            tags.append(f"agent:{agent_id}")

        # 从 tools_used 添加标签
        tools_used = session.get("tools_used", [])
        for tool in tools_used:
            tags.append(f"tool:{tool}")

        # 从内容关键词提取
        messages = session.get("messages", [])
        all_content = ""
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                all_content += content.lower() + " "

        # 关键词标签
        keyword_tags = {
            "bug": "bug-fix",
            "fix": "bug-fix",
            "error": "bug-fix",
            "feature": "feature",
            "implement": "feature",
            "test": "testing",
            "review": "review",
            "refactor": "refactor",
            "optimize": "optimization",
            "security": "security",
            "config": "config",
            "deploy": "deployment",
        }

        for keyword, tag in keyword_tags.items():
            if keyword in all_content and tag not in tags:
                tags.append(tag)

        return list(set(tags))


curator_plugin = OpenClawCurator()


def on_load():
    print("[OpenClawCurator] Plugin loaded")


def get_curator():
    return curator_plugin