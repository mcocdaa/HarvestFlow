# @file backend/managers/curator_manager.py
# @brief 自动审核管理器 - 评估会话质量并自动打标签
# @create 2026-03-18

from typing import Dict, List
import argparse

from core import database_manager, setting_manager, hook_manager
from core.constants import SessionStatus
from managers.base import BaseManager
from managers.session_manager import session_manager


DEFAULT_BASE_SCORE = 3
DEFAULT_AUTO_APPROVE_THRESHOLD = 4
MESSAGE_COUNT_THRESHOLD_1 = 10
MESSAGE_COUNT_THRESHOLD_2 = 20
MAX_SCORE = 5


class CuratorManager(BaseManager):
    """自动审核管理器

    职责：
    1. 评估会话质量
    2. 自动打标签和评分

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("curator_manager_construct_before", "curator_manager_construct_after")
    def __init__(self):
        super().__init__()
        self.enabled: bool = True
        self.auto_approve_threshold: int = DEFAULT_AUTO_APPROVE_THRESHOLD

    @hook_manager.wrap_hooks(after="curator_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_argument_group("Curator", "Curator Settings")
        group.add_argument(
            "--curator-enabled",
            type=str,
            default=None,
            choices=["true", "false", "1", "0", "yes", "no"],
            help="是否启用自动审核 (默认: true)"
        )
        group.add_argument(
            "--auto-approve-threshold",
            type=int,
            default=None,
            help=f"自动审批阈值 (默认: {DEFAULT_AUTO_APPROVE_THRESHOLD})"
        )

    @hook_manager.wrap_hooks("curator_manager_init_before", "curator_manager_init_after")
    def init(self, args: argparse.Namespace):
        curator_enabled_val = getattr(args, 'curator_enabled', None)
        if curator_enabled_val is None:
            curator_enabled_val = setting_manager.get("CURATOR_ENABLED", True)
        self.enabled = str(curator_enabled_val).lower() in ('true', '1', 'yes')

        threshold_val = getattr(args, 'auto_approve_threshold', None)
        if threshold_val is None:
            threshold_val = setting_manager.get("AUTO_APPROVE_THRESHOLD", DEFAULT_AUTO_APPROVE_THRESHOLD)
        self.auto_approve_threshold = int(threshold_val)

    @hook_manager.wrap_hooks("curator_manager_evaluate_before", "curator_manager_evaluate_after")
    def evaluate_session(self, session_id: str) -> Dict:
        """评估单个会话（模板：校验 → 评分 → 回写 → 自动审批）

        插件通过 curator_manager_score_before 窄钩子只接管评分步骤，
        校验与回写编排始终由本模板负责，插件无需复制。
        """
        if not self.enabled:
            return self.error_result(session_id, "curator disabled")

        content, error = self._validate_for_evaluation(session_id)
        if error:
            return self.error_result(session_id, error)

        scored = self._score(content)
        score = int(scored["score"])
        is_high_value = bool(scored.get("is_high_value", score >= self.auto_approve_threshold))
        tags = scored.get("tags", [])
        # 评分步骤未显式返回 tools_used 时回退到 content（插件窄钩子只负责评分）
        tools_used = scored.get("tools_used", content.get("tools_used", []))

        session_manager.update_session(session_id, {
            "quality_auto_score": score,
            "tags": tags,
            "tools_used": tools_used,
            "status": SessionStatus.CURATED.value,
        })

        # Auto-approve high-value sessions（经 apply_review 统一入口，含流转校验+审计）
        auto_approved = False
        if is_high_value:
            review_result = session_manager.apply_review(
                session_id, SessionStatus.APPROVED, "auto_approve",
                notes=f"score {score} >= threshold {self.auto_approve_threshold}",
                score=score
            )
            auto_approved = "error" not in review_result

        result = {
            "session_id": session_id,
            "score": score,
            "is_high_value": is_high_value,
            "tags": tags,
            "tools_used": tools_used,
            "auto_approved": auto_approved,
        }
        # 评分步骤的附加产物（如 score_reasons）并入 API 响应
        result.update({k: v for k, v in scored.items() if k not in result})
        return result

    def _validate_for_evaluation(self, session_id: str) -> tuple:
        """评估前置校验（错误文案为 API 404/409 映射依据，不可更改）

        Returns:
            (content, error)：校验通过返回 (会话 content, None)，否则 (None, 错误文案)
        """
        session = session_manager.get_session(session_id)
        if not session:
            return None, "session not found"

        if session.get("status") != SessionStatus.RAW.value:
            return None, "session is not in raw status"

        content = session.get("content")
        if not content:
            return None, "content not found"

        return content, None

    @hook_manager.wrap_hooks(before="curator_manager_score_before", after="curator_manager_score_after")
    def _score(self, content: Dict) -> Dict:
        """内置评分步骤（窄钩子接入点）

        before 钩子签名 (self, content)；返回非 None dict 即短路接管，
        需包含 score 键，可选 is_high_value / tags / tools_used 及任意附加键。

        Returns:
            {"score": int, "tags": List[str], "tools_used": List[str], ...}
        """
        score = self._calculate_score(content)
        tool_names = self._extract_tool_names_from_calls(content)
        return {
            "score": score,
            "tags": self._extract_tags(content, tool_names),
            "tools_used": self._extract_tools(content, tool_names),
        }

    def _calculate_score(self, content: Dict) -> int:
        """计算质量分数"""
        score = DEFAULT_BASE_SCORE

        if content.get("messages"):
            message_count = len(content.get("messages", []))
            if message_count > MESSAGE_COUNT_THRESHOLD_1:
                score += 1
            if message_count > MESSAGE_COUNT_THRESHOLD_2:
                score += 1

        if content.get("tool_calls") or content.get("tools_used"):
            score += 1

        if content.get("final_output") or content.get("result"):
            score += 1

        return min(score, MAX_SCORE)

    def _extract_tool_names_from_calls(self, content: Dict) -> List[str]:
        """从 tool_calls 中提取工具名称"""
        tool_names = []
        if content.get("tool_calls"):
            for tool_call in content.get("tool_calls", []):
                if isinstance(tool_call, dict) and tool_call.get("name"):
                    tool_names.append(tool_call.get("name"))
        return tool_names

    @staticmethod
    def _unique_names(names: List[str]) -> List[str]:
        """去重保序（替代 set() 的任意顺序）"""
        seen = set()
        result = []
        for name in names:
            if name not in seen:
                seen.add(name)
                result.append(name)
        return result

    def _extract_tags(self, content: Dict, tool_names: List[str] = None) -> List[str]:
        """提取标签"""
        tags = []

        if content.get("task_type"):
            tags.append(content.get("task_type"))

        if content.get("agent_role"):
            tags.append(content.get("agent_role"))

        tags.extend(tool_names if tool_names is not None else self._extract_tool_names_from_calls(content))

        return self._unique_names(tags)

    def _extract_tools(self, content: Dict, tool_names: List[str] = None) -> List[str]:
        """提取使用的工具"""
        tools = []

        if content.get("tools_used"):
            tools.extend(content.get("tools_used", []))

        tools.extend(tool_names if tool_names is not None else self._extract_tool_names_from_calls(content))

        return self._unique_names(tools)

    @hook_manager.wrap_hooks("curator_manager_evaluate_all_before", "curator_manager_evaluate_all_after")
    def evaluate_all(self) -> Dict:
        """评估所有 raw 会话"""
        if not self.enabled:
            return {"success": False, "error": "curator disabled"}

        raw_sessions = database_manager.session_get_by_status(SessionStatus.RAW.value)

        results = []
        for row in raw_sessions:
            session_id = row["session_id"]
            result = self.evaluate_session(session_id)
            results.append(result)

        success_results = [r for r in results if "error" not in r]
        return {
            "total": len(results),
            "high_value": len([r for r in success_results if r.get("is_high_value")]),
            "low_value": len([r for r in success_results if not r.get("is_high_value")]),
            "results": results,
        }


curator_manager = CuratorManager()
