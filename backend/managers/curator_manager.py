# @file backend/managers/curator_manager.py
# @brief 自动审核管理器 - 评估会话质量并自动打标签
# @create 2026-03-18

import json
import os
import shutil
import logging
from typing import Dict, List
import argparse

from core import database_manager, setting_manager, hook_manager
from managers.session_manager import session_manager


DEFAULT_BASE_SCORE = 3
DEFAULT_AUTO_APPROVE_THRESHOLD = 4
MESSAGE_COUNT_THRESHOLD_1 = 10
MESSAGE_COUNT_THRESHOLD_2 = 20
MAX_SCORE = 5


class CuratorManager:
    """自动审核管理器

    职责：
    1. 评估会话质量
    2. 自动打标签和评分
    3. 高价值会话移动到 curated 目录

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("curator_manager_construct_before", "curator_manager_construct_after")
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled: bool = True
        self.auto_approve_threshold: int = DEFAULT_AUTO_APPROVE_THRESHOLD

    @hook_manager.wrap_hooks(after="curator_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_argument_group("Curator", "Curator Settings")
        group.add_argument(
            "--curator-enabled",
            type=bool,
            default=True,
            help="是否启用自动审核 (默认: True)"
        )
        group.add_argument(
            "--auto-approve-threshold",
            type=int,
            default=DEFAULT_AUTO_APPROVE_THRESHOLD,
            help=f"自动审批阈值 (默认: {DEFAULT_AUTO_APPROVE_THRESHOLD})"
        )

    @hook_manager.wrap_hooks("curator_manager_init_before", "curator_manager_init_after")
    def init(self, args: argparse.Namespace):
        curator_enabled_val = getattr(args, 'curator_enabled', setting_manager.get("CURATOR_ENABLED", True))
        self.enabled = str(curator_enabled_val).lower() in ('true', '1', 'yes')

        self.auto_approve_threshold = getattr(args, 'auto_approve_threshold', setting_manager.get("AUTO_APPROVE_THRESHOLD", DEFAULT_AUTO_APPROVE_THRESHOLD))
        self.auto_approve_threshold = int(self.auto_approve_threshold)

    @property
    def agent_curated_dir(self) -> str:
        return os.path.join(setting_manager.get("DATA_DIR", "./data"), "agent_curated")

    @hook_manager.wrap_hooks("curator_manager_evaluate_before", "curator_manager_evaluate_after")
    def evaluate_session(self, session_id: str) -> Dict:
        """评估单个会话"""
        session = session_manager.get_session(session_id)
        if not session:
            return {"session_id": session_id, "error": "session not found"}

        content = session_manager.get_session_content(session_id)
        if not content:
            return {"session_id": session_id, "error": "content not found"}

        score = self._calculate_score(content)
        is_high_value = score >= self.auto_approve_threshold

        tags = self._extract_tags(content)
        tools_used = self._extract_tools(content)

        session_manager.update_session(session_id, {
            "quality_auto_score": score,
            "tags": tags,
            "tools_used": tools_used,
        })

        result = {
            "session_id": session_id,
            "score": score,
            "is_high_value": is_high_value,
            "tags": tags,
            "tools_used": tools_used,
        }

        # 所有评估过的会话都标记为 curated，高价值的移动到 curated 目录
        self._mark_as_curated(session_id)

        if is_high_value:
            self._move_to_curated(session_id)

        return result

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

    def _extract_tags(self, content: Dict) -> List[str]:
        """提取标签"""
        tags = []

        if content.get("task_type"):
            tags.append(content.get("task_type"))

        if content.get("agent_role"):
            tags.append(content.get("agent_role"))

        tags.extend(self._extract_tool_names_from_calls(content))

        return list(set(tags))

    def _extract_tools(self, content: Dict) -> List[str]:
        """提取使用的工具"""
        tools = []

        if content.get("tools_used"):
            tools.extend(content.get("tools_used", []))

        tools.extend(self._extract_tool_names_from_calls(content))

        return list(set(tools))

    @hook_manager.wrap_hooks("curator_manager_mark_as_curated_before", "curator_manager_mark_as_curated_after")
    def _mark_as_curated(self, session_id: str):
        """标记为 curated 状态"""
        session = session_manager.get_session(session_id)
        if not session:
            return

        session_manager.update_session(session_id, {"status": "curated"})

    @hook_manager.wrap_hooks("curator_manager_move_to_curated_before", "curator_manager_move_to_curated_after")
    def _move_to_curated(self, session_id: str):
        """移动到 curated 目录"""
        session = session_manager.get_session(session_id)
        if not session:
            return

        source_path = session.get("file_path")
        if not source_path or not os.path.exists(source_path):
            return

        dest_path = os.path.join(self.agent_curated_dir, f"{session_id}.json")

        try:
            shutil.copy2(source_path, dest_path)
            session_manager.update_session(session_id, {
                "file_path": dest_path,
                "status": "curated"
            })
        except Exception as e:
            self.logger.error(f"移动文件失败: {e}")

    @hook_manager.wrap_hooks("curator_manager_evaluate_all_before", "curator_manager_evaluate_all_after")
    def evaluate_all(self) -> Dict:
        """评估所有 raw 会话"""
        raw_sessions = database_manager.session_get_by_status("raw")

        results = []
        for row in raw_sessions:
            session_id = row["session_id"]
            result = self.evaluate_session(session_id)
            results.append(result)

        return {
            "total": len(results),
            "high_value": len([r for r in results if r.get("is_high_value")]),
            "low_value": len([r for r in results if not r.get("is_high_value")]),
            "results": results,
        }


curator_manager = CuratorManager()
