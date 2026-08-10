# @file backend/api/v1/curator.py
# @brief Curator API 路由
# @create 2026-03-22

from fastapi import APIRouter, HTTPException
from managers.curator_manager import curator_manager

router = APIRouter()


@router.post("/curator/evaluate/{session_id}")
def evaluate_session(session_id: str) -> dict:
    result = curator_manager.evaluate_session(session_id)
    if not result:
        raise HTTPException(404, detail="Session not found")
    error = result.get("error")
    if error:
        if error == "session not found":
            raise HTTPException(404, detail=error)
        elif "not in raw" in error or "disabled" in error:
            raise HTTPException(409, detail=error)
        else:
            raise HTTPException(400, detail=error)
    return {"success": True, **result}


@router.post("/curator/evaluate-all")
def evaluate_all() -> dict:
    result = curator_manager.evaluate_all()
    return result


@router.get("/curator/status")
def get_curator_status() -> dict:
    return {
        "enabled": curator_manager.enabled,
        "auto_approve_threshold": curator_manager.auto_approve_threshold,
    }
