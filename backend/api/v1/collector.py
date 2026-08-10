# @file backend/api/v1/collector.py
# @brief Collector API 路由
# @create 2026-03-22

from fastapi import APIRouter, HTTPException
from typing import Optional
from managers.collector_manager import collector_manager

router = APIRouter()


@router.get("/collector/scan")
def scan_folder(folder_path: Optional[str] = None) -> dict:
    files = collector_manager.scan_folder(folder_path)
    return {"folder_path": folder_path, "files_found": len(files), "files": files}


@router.post("/collector/import")
def import_session(file_path: str) -> dict:
    session_id = collector_manager.import_session(file_path)
    if not session_id:
        raise HTTPException(400, detail="Failed to import session")
    return {"success": True, "session_id": session_id}


@router.post("/collector/import-all")
def import_all(folder_path: Optional[str] = None) -> dict:
    result = collector_manager.import_all(folder_path)
    return result


@router.post("/collector/watch-folder")
def add_watch_folder(folder_path: str) -> dict:
    collector_manager.add_watch_folder(folder_path)
    return {"success": True, "watch_folders": collector_manager.watch_folders}


@router.delete("/collector/watch-folder")
def remove_watch_folder(folder_path: str) -> dict:
    collector_manager.remove_watch_folder(folder_path)
    return {"success": True, "watch_folders": collector_manager.watch_folders}


@router.get("/collector/watch-folders")
def get_watch_folders() -> dict:
    return {"watch_folders": collector_manager.watch_folders}
