# @file backend/api/v1/session.py
# @brief Session API 路由
# @create 2026-03-22

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Optional, Dict
from managers.session_manager import session_manager

router = APIRouter()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, detail="Session not found")
    return {"success": True, "session": session}


@router.get("/sessions/{session_id}/content")
async def get_session_content(session_id: str) -> dict:
    content = session_manager.get_session_content(session_id)
    if not content:
        raise HTTPException(404, detail="Content not found")
    return {"success": True, "content": content}


@router.get("/sessions")
async def get_sessions(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort: str = "recent"
) -> dict:
    return session_manager.get_sessions(status, page, page_size, sort)


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, updates: Dict) -> dict:
    result = session_manager.update_session(session_id, updates)
    if result is None:
        raise HTTPException(404, detail="Session not found")
    return {"success": True, "session": result}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(404, detail="Session not found")
    return Response(status_code=204)


@router.get("/stats")
async def get_stats() -> dict:
    return session_manager.get_stats()
