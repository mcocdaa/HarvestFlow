# @file backend/api/v1/reviewer.py
# @brief 人工审核 API
# @create 2026-03-18

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from managers.reviewer_manager import reviewer_manager

router = APIRouter()


class BatchApproveRequest(BaseModel):
    session_ids: List[str]


class BatchRejectRequest(BaseModel):
    session_ids: List[str]


class UpdateSessionRequest(BaseModel):
    quality_manual_score: Optional[int] = None
    tags: Optional[List[str]] = None
    agent_role: Optional[str] = None
    task_type: Optional[str] = None
    notes: Optional[str] = None


@router.post("/reviewer/approve/{session_id}")
async def approve_session(session_id: str, notes: Optional[str] = None):
    try:
        result = reviewer_manager.approve_session(session_id, notes)
        if result:
            return result
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reviewer/reject/{session_id}")
async def reject_session(session_id: str, notes: Optional[str] = None):
    try:
        result = reviewer_manager.reject_session(session_id, notes)
        if result:
            return result
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/reviewer/update/{session_id}")
async def update_session(session_id: str, updates: UpdateSessionRequest):
    try:
        update_dict = updates.model_dump(exclude_none=True)
        if "notes" in update_dict:
            notes = update_dict.pop("notes")

        result = reviewer_manager.update_session(session_id, update_dict)
        if result:
            return result
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reviewer/batch-approve")
async def batch_approve(request: BatchApproveRequest):
    try:
        return reviewer_manager.batch_approve(request.session_ids)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reviewer/batch-reject")
async def batch_reject(request: BatchRejectRequest):
    try:
        return reviewer_manager.batch_reject(request.session_ids)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reviewer/pending")
async def get_pending_sessions(page: int = 1, page_size: int = 20):
    try:
        return reviewer_manager.get_pending_sessions(page, page_size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reviewer/logs")
async def get_audit_logs(session_id: Optional[str] = None):
    try:
        return reviewer_manager.get_audit_logs(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
