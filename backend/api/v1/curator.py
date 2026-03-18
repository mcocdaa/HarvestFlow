# @file backend/api/v1/curator.py
# @brief 自动审核 API
# @create 2026-03-18

from fastapi import APIRouter, HTTPException
from managers.curator_manager import curator_manager

router = APIRouter()


@router.post("/curator/evaluate/{session_id}")
async def evaluate_session(session_id: str):
    try:
        result = curator_manager.evaluate_session(session_id)
        if result:
            return result
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/curator/evaluate/all")
async def evaluate_all_sessions():
    try:
        return curator_manager.evaluate_all()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/curator/config")
async def get_curator_config():
    return {
        "enabled": curator_manager.enabled,
        "auto_approve_threshold": curator_manager.auto_approve_threshold,
    }


@router.put("/curator/config")
async def update_curator_config(config: dict):
    if "enabled" in config:
        curator_manager.enabled = config["enabled"]
    if "auto_approve_threshold" in config:
        curator_manager.auto_approve_threshold = config["auto_approve_threshold"]

    return {
        "enabled": curator_manager.enabled,
        "auto_approve_threshold": curator_manager.auto_approve_threshold,
    }
