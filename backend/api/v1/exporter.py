# @file backend/api/v1/exporter.py
# @brief Exporter API 路由
# @create 2026-03-22

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
from managers.exporter_manager import exporter_manager
from api.v1.common import bad_request, not_found


class ExportRequest(BaseModel):
    format: Optional[str] = None
    min_score: Optional[int] = None
    agent_role: Optional[str] = None
    task_type: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = "v1"


class ZipDownloadRequest(BaseModel):
    filenames: List[str]


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
    if not result.get("success"):
        raise HTTPException(400, detail=result.get("message", "Export failed"))
    return result


@router.get("/exporter/history")
def get_export_history(limit: int = 20) -> dict:
    records = exporter_manager.get_export_history(limit)
    return {"exports": records}


@router.get("/exporter/formats")
def get_supported_formats(all: bool = False) -> dict:
    from core.constants import ExportFormat
    if all:
        return {"formats": [f.value for f in ExportFormat]}
    return {"formats": ["sharegpt", "alpaca"]}


@router.get("/exporter/download")
def download_export(filename: str):
    """下载单个导出文件（仅限导出输出目录内的 .jsonl）"""
    try:
        file_path = exporter_manager.resolve_export_file(filename)
    except ValueError:
        raise bad_request("Invalid filename")
    except FileNotFoundError:
        raise not_found("Export file not found")
    return FileResponse(file_path, media_type="application/x-ndjson", filename=filename)


@router.post("/exporter/download-zip")
def download_export_zip(request: ZipDownloadRequest) -> Response:
    """将多个导出文件打包下载"""
    try:
        data = exporter_manager.build_export_zip(request.filenames)
    except ValueError:
        raise bad_request("No valid files to download")
    except FileNotFoundError as e:
        raise not_found(f"Export file not found: {e}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"harvestflow-exports-{timestamp}.zip"
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
