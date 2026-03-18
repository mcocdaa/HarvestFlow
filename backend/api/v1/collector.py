# @file backend/api/v1/collector.py
# @brief 数据采集 API
# @create 2026-03-18

import importlib.util
import os
from fastapi import APIRouter, HTTPException
from typing import Optional
from managers.collector_manager import collector_manager
from config import COLLECTOR_CONFIG, PLUGINS_DIR

router = APIRouter()


def _load_openclaw_collector():
    """动态加载 OpenClaw collector 插件（避免路径依赖问题）"""
    plugin_path = os.path.join(PLUGINS_DIR, "collectors", "openclaw", "backend.py")
    spec = importlib.util.spec_from_file_location("openclaw_collector", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OpenClawCollector


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


@router.post("/collector/scan/openclaw")
async def scan_openclaw():
    """扫描 OpenClaw 会话并返回 jsonl 文件列表"""
    try:
        OpenClawCollector = _load_openclaw_collector()
        openclaw_config = COLLECTOR_CONFIG.get("openclaw", {})
        collector = OpenClawCollector(openclaw_config)
        files = collector.scan()
        return {
            "total": len(files),
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/collector/import/openclaw")
async def import_openclaw_sessions():
    """扫描并导入所有 OpenClaw 会话"""
    try:
        OpenClawCollector = _load_openclaw_collector()
        openclaw_config = COLLECTOR_CONFIG.get("openclaw", {})
        collector = OpenClawCollector(openclaw_config)

        files = collector.scan()

        imported = []
        failed = []

        for file_path in files:
            session_data = collector.parse(file_path)
            if session_data:
                try:
                    from managers.session_manager import session_manager
                    result = session_manager.create_session(session_data)
                    if result:
                        imported.append(session_data.get("session_id", file_path))
                    else:
                        failed.append(file_path)
                except Exception as e:
                    print(f"[import_openclaw_sessions] Error: {e}")
                    failed.append(file_path)
            else:
                failed.append(file_path)

        return {
            "total": len(files),
            "imported": len(imported),
            "failed": len(failed),
            "session_ids": imported,
            "failed_files": failed,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
