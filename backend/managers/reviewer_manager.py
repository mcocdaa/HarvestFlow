# @file backend/managers/reviewer_manager.py
# @brief 人工审核管理器 - 支持人工审批、拒绝和批量操作
# @create 2026-03-18

import json
import os
import shutil
import logging
from typing import Dict, List
import argparse

from core import database_manager, setting_manager, hook_manager
from managers.session_manager import session_manager


class ReviewerManager:
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
        self.logger = logging.getLogger(__name__)

    @hook_manager.wrap_hooks(after="reviewer_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_argument_group("Reviewer", "Reviewer Settings")
        group.add_argument(
            "--reviewer-data-dir",
            type=str,
            default=None,
            help="审核数据目录"
        )

    @hook_manager.wrap_hooks("reviewer_manager_init_before", "reviewer_manager_init_after")
    def init(self, args: argparse.Namespace):
        if getattr(args, 'reviewer_data_dir', None):
            self.data_dir = args.reviewer_data_dir
        else:
            self.data_dir = setting_manager.get("DATA_DIR", "./data")

    @property
    def human_approved_dir(self) -> str:
        return os.path.join(self.data_dir, "human_approved")

    @hook_manager.wrap_hooks("reviewer_manager_approve_before", "reviewer_manager_approve_after")
    def approve_session(self, session_id: str, notes: str = None) -> Dict:
        """审批会话"""
        session = session_manager.get_session(session_id)
        if not session:
            return {"session_id": session_id, "error": "session not found"}

        current_status = session.get("status")

        if current_status == "curated" or current_status == "raw":
            source_path = session.get("file_path")
            if source_path and os.path.exists(source_path):
                dest_path = os.path.join(self.human_approved_dir, f"{session_id}.json")
                os.makedirs(self.human_approved_dir, exist_ok=True)
                try:
                    shutil.copy2(source_path, dest_path)
                    session_manager.update_session(session_id, {
                        "file_path": dest_path,
                        "status": "approved"
                    })
                except Exception as e:
                    return {"session_id": session_id, "error": str(e)}
        else:
            session_manager.update_session(session_id, {"status": "approved"})

        database_manager.audit_log_create(session_id, "approve", "user", notes)

        return session_manager.get_session(session_id)

    @hook_manager.wrap_hooks("reviewer_manager_reject_before", "reviewer_manager_reject_after")
    def reject_session(self, session_id: str, notes: str = None) -> Dict:
        """拒绝会话"""
        session = session_manager.get_session(session_id)
        if not session:
            return {"session_id": session_id, "error": "session not found"}

        session_manager.update_session(session_id, {"status": "rejected"})
        database_manager.audit_log_create(session_id, "reject", "user", notes)

        return session_manager.get_session(session_id)

    @hook_manager.wrap_hooks("reviewer_manager_update_before", "reviewer_manager_update_after")
    def update_session(self, session_id: str, updates: Dict) -> Dict:
        """更新会话"""
        session = session_manager.get_session(session_id)
        if not session:
            return {"session_id": session_id, "error": "session not found"}

        session_manager.update_session(session_id, updates)
        database_manager.audit_log_create(session_id, "modify", "user", json.dumps(updates))

        return session_manager.get_session(session_id)

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
