# @file backend/api/v1/curator.py
# @brief Curator API 路由
# @create 2026-03-22

from fastapi import APIRouter
from typing import Optional
from managers.curator_manager import curator_manager

router = APIRouter()


@router.get("/curator/evaluate/{session_id}")
async def evaluate_session(session_id: str) -> dict:
    result = curator_manager.evaluate_session(session_id)
    if result:
        return {"success": True, **result}
    return {"success": False, "error": "Session not found"}


@router.post("/curator/evaluate-all")
async def evaluate_all() -> dict:
    result = curator_manager.evaluate_all()
    return result


@router.get("/curator/status")
async def get_curator_status() -> dict:
    return {
        "enabled": curator_manager.enabled,
        "auto_approve_threshold": curator_manager.auto_approve_threshold,
    }
