# @file backend/api/v1/collector.py
# @brief 数据采集 API
# @create 2026-03-18

from fastapi import APIRouter, HTTPException
from typing import Optional
from managers.collector_manager import collector_manager

router = APIRouter()


@router.post("/collector/scan")
async def scan_folder(folder_path: Optional[str] = None):
    try:
        files = collector_manager.scan_folder(folder_path)
        return {
            "total": len(files),
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/collector/import")
async def import_session(file_path: str):
    try:
        session_id = collector_manager.import_session(file_path)
        if session_id:
            return {"success": True, "session_id": session_id}
        return {"success": False, "message": "Failed to import session"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/collector/import/all")
async def import_all(folder_path: Optional[str] = None):
    try:
        result = collector_manager.import_all(folder_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/collector/config")
async def get_collector_config():
    return {
        "watch_folders": collector_manager.watch_folders,
        "poll_interval": collector_manager.poll_interval,
    }


@router.post("/collector/config/add-folder")
async def add_watch_folder(folder_path: str):
    collector_manager.add_watch_folder(folder_path)
    return {"success": True, "watch_folders": collector_manager.watch_folders}


@router.post("/collector/config/remove-folder")
async def remove_watch_folder(folder_path: str):
    collector_manager.remove_watch_folder(folder_path)
    return {"success": True, "watch_folders": collector_manager.watch_folders}
