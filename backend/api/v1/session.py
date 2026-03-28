# @file backend/api/v1/session.py
# @brief Session API 路由
# @create 2026-03-22

from fastapi import APIRouter
from typing import Optional, Dict
from managers.session_manager import session_manager
from core import database_manager

router = APIRouter()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    session = session_manager.get_session(session_id)
    if session:
        return {"success": True, "session": session}
    return {"success": False, "error": "Session not found"}


@router.get("/sessions/{session_id}/content")
async def get_session_content(session_id: str) -> dict:
    content = session_manager.get_session_content(session_id)
    if content:
        return {"success": True, "content": content}
    return {"success": False, "error": "Content not found"}


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
    if result:
        return {"success": True, "session": result}
    return {"success": False, "error": "Session not found"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    success = session_manager.delete_session(session_id)
    return {"success": success}


@router.get("/stats")
async def get_stats() -> dict:
    raw = database_manager.session_get_by_status("raw")
    approved = database_manager.session_get_by_status("approved")
    rejected = database_manager.session_get_by_status("rejected")

    cursor = database_manager.connection.execute(
        "SELECT AVG(quality_auto_score) as avg_score FROM sessions WHERE quality_auto_score IS NOT NULL"
    )
    row = cursor.fetchone()
    avg_score = row["avg_score"] if row and row["avg_score"] else 0

    return {
        "total_sessions": len(raw) + len(approved) + len(rejected),
        "raw_sessions": len(raw),
        "approved_sessions": len(approved),
        "rejected_sessions": len(rejected),
        "avg_auto_score": round(avg_score, 1) if avg_score else 0,
        "curated_sessions": len(approved) + len(rejected),
    }
