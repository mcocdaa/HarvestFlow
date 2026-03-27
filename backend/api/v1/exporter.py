# @file backend/api/v1/exporter.py
# @brief Exporter API 路由
# @create 2026-03-22

from fastapi import APIRouter
from typing import Optional, List
from managers.exporter_manager import exporter_manager

router = APIRouter()


@router.post("/exporter/export")
async def export_sessions(
    format: Optional[str] = None,
    min_score: Optional[int] = None,
    agent_role: Optional[str] = None,
    task_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    version: Optional[str] = "v1"
) -> dict:
    result = exporter_manager.export(
        format=format,
        min_score=min_score,
        agent_role=agent_role,
        task_type=task_type,
        tags=tags,
        version=version
    )
    return result


@router.get("/exporter/history")
async def get_export_history(limit: int = 20) -> dict:
    records = exporter_manager.get_export_history(limit)
    return {"exports": records}


@router.get("/exporter/formats")
async def get_supported_formats() -> dict:
    return {"formats": ["sharegpt", "alpaca"]}
