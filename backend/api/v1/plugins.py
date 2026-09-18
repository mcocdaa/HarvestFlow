# @file backend/api/v1/plugins.py
# @brief Plugins API 路由
# @create 2026-03-25

from fastapi import APIRouter
from core import plugin_manager
from api.v1.common import ok, not_found, bad_request

router = APIRouter()


def _set_plugin_enabled(key: str, enabled: bool) -> dict:
    """启停插件：不存在 404；存在但持久化失败（如只读挂载）返回 400"""
    if key not in plugin_manager.plugins:
        raise not_found("Plugin not found")
    if not plugin_manager.set_enabled(key, enabled):
        raise bad_request("Failed to persist plugin state (plugins.yaml may be read-only)")
    return ok()


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
    return _set_plugin_enabled(key, True)


@router.post("/plugins/disable")
def disable_plugin(key: str) -> dict:
    return _set_plugin_enabled(key, False)
