# @file backend/api/v1/exporter.py
# @brief Exporter API 路由
# @create 2026-03-22

from fastapi import APIRouter
from typing import Optional, List
from pydantic import BaseModel
from managers.exporter_manager import exporter_manager


class ExportRequest(BaseModel):
    format: Optional[str] = None
    min_score: Optional[int] = None
    agent_role: Optional[str] = None
    task_type: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = "v1"


router = APIRouter()


@router.post("/exporter/export")
def export_sessions(request: ExportRequest) -> dict:
    result = exporter_manager.export(
        format=request.format,
        min_score=request.min_score,
        agent_role=request.agent_role,
        task_type=request.task_type,
        tags=request.tags,
        version=request.version
    )
    return result


@router.get("/exporter/history")
def get_export_history(limit: int = 20) -> dict:
    records = exporter_manager.get_export_history(limit)
    return {"exports": records}


@router.get("/exporter/formats")
def get_supported_formats() -> dict:
    return {"formats": ["sharegpt", "alpaca"]}
