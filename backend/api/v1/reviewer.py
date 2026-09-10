# @file backend/api/v1/reviewer.py
# @brief Reviewer API 路由
# @create 2026-03-22

from fastapi import APIRouter
from typing import Optional, List
from managers.reviewer_manager import reviewer_manager
from api.v1.common import ok, raise_from_result, not_found

router = APIRouter()


def _review_ok(result: dict) -> dict:
    """审批结果 → 响应：会话缺失 404，其他错误 400，成功包 ok(session=...)"""
    if result.get("error") == "session not found":
        raise not_found(result["error"])
    return ok(session=raise_from_result(result, "Session not found"))


@router.get("/reviewer/pending")
def get_pending_sessions(page: int = 1, page_size: int = 20) -> dict:
    return reviewer_manager.get_pending_sessions(page, page_size)


@router.post("/reviewer/approve/{session_id}")
def approve_session(session_id: str, notes: Optional[str] = None, score: Optional[int] = None) -> dict:
    return _review_ok(reviewer_manager.approve_session(session_id, notes, score))


@router.post("/reviewer/reject/{session_id}")
def reject_session(session_id: str, notes: Optional[str] = None, score: Optional[int] = None) -> dict:
    return _review_ok(reviewer_manager.reject_session(session_id, notes, score))


@router.post("/reviewer/batch-approve")
def batch_approve(session_ids: List[str]) -> dict:
    return reviewer_manager.batch_approve(session_ids)


@router.post("/reviewer/batch-reject")
def batch_reject(session_ids: List[str]) -> dict:
    return reviewer_manager.batch_reject(session_ids)


@router.get("/reviewer/audit-logs")
def get_audit_logs(session_id: Optional[str] = None) -> dict:
    logs = reviewer_manager.get_audit_logs(session_id)
    return {"logs": logs}
