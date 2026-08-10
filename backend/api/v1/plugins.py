# @file backend/api/v1/plugins.py
# @brief Plugins API 路由
# @create 2026-03-25

from fastapi import APIRouter, HTTPException
from core import plugin_manager

router = APIRouter()


@router.get("/plugins")
def get_plugins() -> dict:
    plugins = plugin_manager.get_all()
    return {"plugins": plugins}


@router.get("/plugins/{plugin_type}")
def get_plugins_by_type(plugin_type: str) -> dict:
    plugins = plugin_manager.get_all()
    filtered = [p for p in plugins if p.get("plugin_type") == plugin_type]
    return {"plugins": filtered}


@router.post("/plugins/enable")
def enable_plugin(key: str) -> dict:
    success = plugin_manager.set_enabled(key, True)
    if not success:
        raise HTTPException(404, detail="Plugin not found")
    return {"success": True}


@router.post("/plugins/disable")
def disable_plugin(key: str) -> dict:
    success = plugin_manager.set_enabled(key, False)
    if not success:
        raise HTTPException(404, detail="Plugin not found")
    return {"success": True}
