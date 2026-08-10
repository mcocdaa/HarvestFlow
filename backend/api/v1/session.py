# @file backend/api/v1/session.py
# @brief Session API 路由
# @create 2026-03-22

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Optional, List
from pydantic import BaseModel
from managers.session_manager import session_manager


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    quality_auto_score: Optional[int] = None
    quality_manual_score: Optional[int] = None
    agent_role: Optional[str] = None
    task_type: Optional[str] = None
    tools_used: Optional[List[str]] = None
    tags: Optional[List[str]] = None

router = APIRouter()


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, detail="Session not found")
    return {"success": True, "session": session}


@router.get("/sessions/{session_id}/content")
def get_session_content(session_id: str) -> dict:
    content = session_manager.get_session_content(session_id)
    if not content:
        raise HTTPException(404, detail="Content not found")
    return {"success": True, "content": content}


@router.get("/sessions")
def get_sessions(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort: str = "recent"
) -> dict:
    return session_manager.get_sessions(status, page, page_size, sort)


@router.patch("/sessions/{session_id}")
def update_session(session_id: str, updates: SessionUpdate) -> dict:
    try:
        result = session_manager.update_session(session_id, updates.model_dump(exclude_none=True))
    except ValueError:
        raise HTTPException(409, detail="Invalid status transition")
    if result is None:
        raise HTTPException(404, detail="Session not found")
    return {"success": True, "session": result}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(404, detail="Session not found")
    return Response(status_code=204)


@router.get("/stats")
def get_stats() -> dict:
    return session_manager.get_stats()
