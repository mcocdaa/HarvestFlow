# @file backend/managers/reviewer_manager.py
# @brief 人工审核管理器 - 支持人工审批、拒绝和批量操作
# @create 2026-03-18

from typing import Dict, List
import argparse

from core import database_manager, hook_manager
from core.constants import SessionStatus
from managers.base import BaseManager
from managers.session_manager import session_manager


class ReviewerManager(BaseManager):
    """人工审核管理器

    职责：
    1. 人工审批/拒绝会话
    2. 批量操作
    3. 审计日志记录

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("reviewer_manager_construct_before", "reviewer_manager_construct_after")
    def __init__(self):
        super().__init__()

    @hook_manager.wrap_hooks(after="reviewer_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数（无参数）"""

    @hook_manager.wrap_hooks("reviewer_manager_init_before", "reviewer_manager_init_after")
    def init(self, args: argparse.Namespace):
        """初始化人工审核管理器

        Args:
            args: 解析后的参数
        """
        pass

    def _review(self, session_id: str, target_status: SessionStatus, action: str,
                notes: str = None, score: int = None) -> Dict:
        """审批/拒绝公共逻辑（委托 session_manager.apply_review 统一入口）

        Args:
            session_id: 会话 ID
            target_status: 目标状态（APPROVED / REJECTED）
            action: 审计动作名（"approve" / "reject"）
            notes: 备注
            score: 人工评分（缺省沿用现有 quality_manual_score）

        Returns:
            更新后的会话，失败返回 {"session_id", "error"}
        """
        return session_manager.apply_review(session_id, target_status, action, notes, score)

    @hook_manager.wrap_hooks("reviewer_manager_approve_before", "reviewer_manager_approve_after")
    def approve_session(self, session_id: str, notes: str = None, score: int = None) -> Dict:
        """审批会话"""
        return self._review(session_id, SessionStatus.APPROVED, "approve", notes, score)

    @hook_manager.wrap_hooks("reviewer_manager_reject_before", "reviewer_manager_reject_after")
    def reject_session(self, session_id: str, notes: str = None, score: int = None) -> Dict:
        """拒绝会话"""
        return self._review(session_id, SessionStatus.REJECTED, "reject", notes, score)

    def _batch_operation(self, session_ids: List[str], operation_func) -> Dict:
        """批量操作的通用方法"""
        results = []
        for session_id in session_ids:
            result = operation_func(session_id)
            results.append({
                "session_id": session_id,
                "success": "error" not in result
            })

        return {
            "total": len(session_ids),
            "success": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results,
        }

    @hook_manager.wrap_hooks("reviewer_manager_batch_approve_before", "reviewer_manager_batch_approve_after")
    def batch_approve(self, session_ids: List[str]) -> Dict:
        """批量审批"""
        return self._batch_operation(session_ids, self.approve_session)

    @hook_manager.wrap_hooks("reviewer_manager_batch_reject_before", "reviewer_manager_batch_reject_after")
    def batch_reject(self, session_ids: List[str]) -> Dict:
        """批量拒绝"""
        return self._batch_operation(session_ids, self.reject_session)

    @hook_manager.wrap_hooks("reviewer_manager_get_pending_before", "reviewer_manager_get_pending_after")
    def get_pending_sessions(self, page: int = 1, page_size: int = 20) -> Dict:
        """获取待审核会话"""
        return session_manager.get_sessions(status="curated", page=page, page_size=page_size)

    @hook_manager.wrap_hooks("reviewer_manager_get_audit_logs_before", "reviewer_manager_get_audit_logs_after")
    def get_audit_logs(self, session_id: str = None) -> List[Dict]:
        """获取审计日志"""
        return database_manager.audit_log_get(session_id=session_id)


reviewer_manager = ReviewerManager()
