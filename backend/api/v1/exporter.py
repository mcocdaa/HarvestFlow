# @file backend/api/v1/exporter.py
# @brief 数据导出 API
# @create 2026-03-18

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from managers.exporter_manager import exporter_manager

router = APIRouter()


class ExportRequest(BaseModel):
    format: str = "sharegpt"
    min_score: Optional[int] = None
    agent_role: Optional[str] = None
    task_type: Optional[str] = None
    tags: Optional[List[str]] = None
    version: str = "v1"


@router.post("/export")
async def export_sessions(request: ExportRequest):
    try:
        return exporter_manager.export(
            format=request.format,
            min_score=request.min_score,
            agent_role=request.agent_role,
            task_type=request.task_type,
            tags=request.tags,
            version=request.version,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/history")
async def get_export_history(limit: int = 20):
    try:
        return exporter_manager.get_export_history(limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/formats")
async def get_supported_formats():
    return {
        "formats": ["sharegpt", "alpaca"],
        "default": exporter_manager.default_format,
    }
