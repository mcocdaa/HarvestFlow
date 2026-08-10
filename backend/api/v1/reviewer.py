# @file backend/api/v1/reviewer.py
# @brief Reviewer API 路由
# @create 2026-03-22

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
from managers.reviewer_manager import reviewer_manager

router = APIRouter()


@router.get("/reviewer/pending")
def get_pending_sessions(page: int = 1, page_size: int = 20) -> dict:
    return reviewer_manager.get_pending_sessions(page, page_size)


@router.post("/reviewer/approve/{session_id}")
def approve_session(session_id: str, notes: Optional[str] = None, score: Optional[int] = None) -> dict:
    result = reviewer_manager.approve_session(session_id, notes, score)
    if not result:
        raise HTTPException(404, detail="Session not found")
    if "error" in result:
        raise HTTPException(400, detail=result["error"])
    return {"success": True, "session": result}


@router.post("/reviewer/reject/{session_id}")
def reject_session(session_id: str, notes: Optional[str] = None, score: Optional[int] = None) -> dict:
    result = reviewer_manager.reject_session(session_id, notes, score)
    if not result:
        raise HTTPException(404, detail="Session not found")
    if "error" in result:
        raise HTTPException(400, detail=result["error"])
    return {"success": True, "session": result}


@router.patch("/reviewer/session/{session_id}")
def update_session(session_id: str, updates: Dict) -> dict:
    result = reviewer_manager.update_session(session_id, updates)
    if not result:
        raise HTTPException(404, detail="Session not found")
    if "error" in result:
        raise HTTPException(400, detail=result["error"])
    return {"success": True, "session": result}


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
