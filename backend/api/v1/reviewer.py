# @file backend/api/v1/reviewer.py
# @brief Reviewer API 路由
# @create 2026-03-22

from fastapi import APIRouter
from typing import Optional, List, Dict
from managers.reviewer_manager import reviewer_manager

router = APIRouter()


@router.get("/reviewer/pending")
async def get_pending_sessions(page: int = 1, page_size: int = 20) -> dict:
    return reviewer_manager.get_pending_sessions(page, page_size)


@router.post("/reviewer/approve/{session_id}")
async def approve_session(session_id: str, notes: Optional[str] = None, score: Optional[int] = None) -> dict:
    result = reviewer_manager.approve_session(session_id, notes, score)
    if result:
        return {"success": True, "session": result}
    return {"success": False, "error": "Session not found"}


@router.post("/reviewer/reject/{session_id}")
async def reject_session(session_id: str, notes: Optional[str] = None, score: Optional[int] = None) -> dict:
    result = reviewer_manager.reject_session(session_id, notes, score)
    if result:
        return {"success": True, "session": result}
    return {"success": False, "error": "Session not found"}


@router.patch("/reviewer/session/{session_id}")
async def update_session(session_id: str, updates: Dict) -> dict:
    result = reviewer_manager.update_session(session_id, updates)
    if result:
        return {"success": True, "session": result}
    return {"success": False, "error": "Session not found"}


@router.post("/reviewer/batch-approve")
async def batch_approve(session_ids: List[str]) -> dict:
    return reviewer_manager.batch_approve(session_ids)


@router.post("/reviewer/batch-reject")
async def batch_reject(session_ids: List[str]) -> dict:
    return reviewer_manager.batch_reject(session_ids)


@router.get("/reviewer/audit-logs")
async def get_audit_logs(session_id: Optional[str] = None) -> dict:
    logs = reviewer_manager.get_audit_logs(session_id)
    return {"logs": logs}
