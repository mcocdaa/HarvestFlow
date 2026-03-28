# @file backend/api/v1/plugins.py
# @brief Plugins API 路由
# @create 2026-03-25

from fastapi import APIRouter
from core import plugin_manager

router = APIRouter()


@router.get("/plugins")
async def get_plugins() -> dict:
    plugins = plugin_manager.get_all()
    return {"plugins": plugins}


@router.get("/plugins/{plugin_type}")
async def get_plugins_by_type(plugin_type: str) -> dict:
    plugins = plugin_manager.get_all()
    filtered = [p for p in plugins if p.get("plugin_type") == plugin_type]
    return {"plugins": filtered}
