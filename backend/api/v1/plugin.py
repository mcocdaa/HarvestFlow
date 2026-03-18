# @file backend/api/v1/plugin.py
# @brief 插件管理 API
# @create 2026-03-18

from fastapi import APIRouter, HTTPException
from typing import Optional
from core.plugin_loader import plugin_loader

router = APIRouter()


@router.get("/plugins")
async def get_all_plugins():
    try:
        return {
            "plugins": plugin_loader.get_plugin_manifests(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins/{plugin_type}")
async def get_plugins_by_type(plugin_type: str):
    try:
        plugins = plugin_loader.get_enabled_plugins(plugin_type)
        return {"plugins": plugins}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins/{plugin_type}/{plugin_name}")
async def get_plugin_details(plugin_type: str, plugin_name: str):
    config = plugin_loader.get_plugin_config(plugin_name)
    if not config:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
    return config


@router.get("/plugins/{plugin_type}/{plugin_name}/frontend")
async def get_plugin_frontend(plugin_type: str, plugin_name: str):
    code = plugin_loader.get_plugin_frontend_code(plugin_name)
    if code is None:
        raise HTTPException(status_code=404, detail=f"Frontend code for plugin {plugin_name} not found")
    return {"code": code}


@router.post("/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    try:
        await plugin_loader.enable_plugin(plugin_name)
        return {"success": True, "plugin_name": plugin_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    try:
        await plugin_loader.disable_plugin(plugin_name)
        return {"success": True, "plugin_name": plugin_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
