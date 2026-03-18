# @file backend/api/v1/collector.py
# @brief 数据采集 API
# @create 2026-03-18

import importlib.util
import os
from fastapi import APIRouter, HTTPException
from typing import Optional
from managers.collector_manager import collector_manager
from config import PLUGINS_DIR, ACTIVE_COLLECTOR, get_plugin_config

router = APIRouter()


def _load_collector_plugin(plugin_name: str):
    """动态加载指定 collector 插件，返回插件类和配置"""
    plugin_path = os.path.join(PLUGINS_DIR, "collectors", plugin_name, "backend.py")
    if not os.path.exists(plugin_path):
        raise FileNotFoundError(f"Collector plugin '{plugin_name}' not found at {plugin_path}")
    spec = importlib.util.spec_from_file_location(f"collector_{plugin_name}", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # 约定：插件类名为 {Name}Collector，如 OpenClawCollector / DefaultCollector
    class_name = f"{''.join(w.capitalize() for w in plugin_name.split('_'))}Collector"
    plugin_class = getattr(module, class_name, None)
    if plugin_class is None:
        # fallback: 找第一个名字包含 Collector 的类
        for attr in dir(module):
            if "Collector" in attr and not attr.startswith("_"):
                plugin_class = getattr(module, attr)
                break
    if plugin_class is None:
        raise AttributeError(f"No Collector class found in plugin '{plugin_name}'")
    plugin_config = get_plugin_config("collectors", plugin_name)
    return plugin_class, plugin_config


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
        "active_collector": ACTIVE_COLLECTOR,
        "watch_folders": collector_manager.watch_folders,
        "poll_interval": collector_manager.poll_interval,
        "plugin_config": get_plugin_config("collectors", ACTIVE_COLLECTOR),
    }


@router.post("/collector/config/add-folder")
async def add_watch_folder(folder_path: str):
    collector_manager.add_watch_folder(folder_path)
    return {"success": True, "watch_folders": collector_manager.watch_folders}


@router.post("/collector/config/remove-folder")
async def remove_watch_folder(folder_path: str):
    collector_manager.remove_watch_folder(folder_path)
    return {"success": True, "watch_folders": collector_manager.watch_folders}


@router.post("/collector/scan/active")
async def scan_active():
    """使用当前激活的 collector 插件扫描（由 config.yaml plugins.active_collector 决定）"""
    try:
        CollectorClass, plugin_config = _load_collector_plugin(ACTIVE_COLLECTOR)
        collector = CollectorClass(plugin_config)
        files = collector.scan()
        return {
            "plugin": ACTIVE_COLLECTOR,
            "total": len(files),
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/collector/import/active")
async def import_active_sessions():
    """使用当前激活的 collector 插件扫描并导入所有会话"""
    try:
        CollectorClass, plugin_config = _load_collector_plugin(ACTIVE_COLLECTOR)
        collector = CollectorClass(plugin_config)

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
                    print(f"[import_active_sessions] Error: {e}")
                    failed.append(file_path)
            else:
                failed.append(file_path)

        return {
            "plugin": ACTIVE_COLLECTOR,
            "total": len(files),
            "imported": len(imported),
            "failed": len(failed),
            "session_ids": imported,
            "failed_files": failed,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 保留旧端点作为别名（向后兼容）
@router.post("/collector/scan/openclaw")
async def scan_openclaw():
    """已废弃，请使用 /collector/scan/active"""
    return await scan_active()


@router.post("/collector/import/openclaw")
async def import_openclaw_sessions():
    """已废弃，请使用 /collector/import/active"""
    return await import_active_sessions()
