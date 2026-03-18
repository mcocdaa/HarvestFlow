# @file backend/api/v1/session.py
# @brief 会话管理 API
# @create 2026-03-18

from fastapi import APIRouter, HTTPException
from typing import Optional
from managers.session_manager import session_manager

router = APIRouter()


@router.get("/sessions")
async def get_sessions(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort: str = "recent"
):
    try:
        return session_manager.get_sessions(status=status, page=page, page_size=page_size, sort=sort)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions")
async def create_session(session: dict):
    try:
        return session_manager.create_session(session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/content")
async def get_session_content(session_id: str):
    content = session_manager.get_session_content(session_id)
    if not content:
        raise HTTPException(status_code=404, detail=f"Content for session {session_id} not found")
    return content


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


@router.put("/sessions/{session_id}")
async def update_session(session_id: str, updates: dict):
    updated = session_manager.update_session(session_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return updated


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    deleted = session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"message": "Session deleted successfully"}


@router.get("/stats")
async def get_stats():
    from core.database import get_database
    db = get_database()

    stats = {}

    total = db.fetchone("SELECT COUNT(*) as count FROM sessions")
    stats["total_sessions"] = dict(total)["count"] if total else 0

    raw = db.fetchone("SELECT COUNT(*) as count FROM sessions WHERE status = 'raw'")
    stats["raw_sessions"] = dict(raw)["count"] if raw else 0

    curated = db.fetchone("SELECT COUNT(*) as count FROM sessions WHERE status = 'curated'")
    stats["curated_sessions"] = dict(curated)["count"] if curated else 0

    approved = db.fetchone("SELECT COUNT(*) as count FROM sessions WHERE status = 'approved'")
    stats["approved_sessions"] = dict(approved)["count"] if approved else 0

    rejected = db.fetchone("SELECT COUNT(*) as count FROM sessions WHERE status = 'rejected'")
    stats["rejected_sessions"] = dict(rejected)["count"] if rejected else 0

    avg_score = db.fetchone("SELECT AVG(quality_auto_score) as avg FROM sessions WHERE quality_auto_score IS NOT NULL")
    stats["avg_auto_score"] = round(dict(avg_score)["avg"], 2) if avg_score and dict(avg_score)["avg"] else 0

    return stats
