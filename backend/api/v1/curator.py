# @file backend/api/v1/curator.py
# @brief 自动审核 API
# @create 2026-03-18

import importlib.util
import os
from fastapi import APIRouter, HTTPException
from managers.curator_manager import curator_manager
from config import PLUGINS_DIR, ACTIVE_CURATOR, get_plugin_config

router = APIRouter()


def _load_curator_plugin(plugin_name: str):
    """动态加载指定 curator 插件，返回插件类和配置"""
    plugin_path = os.path.join(PLUGINS_DIR, "curators", plugin_name, "backend.py")
    if not os.path.exists(plugin_path):
        raise FileNotFoundError(f"Curator plugin '{plugin_name}' not found at {plugin_path}")
    spec = importlib.util.spec_from_file_location(f"curator_{plugin_name}", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    class_name = f"{''.join(w.capitalize() for w in plugin_name.split('_'))}Curator"
    plugin_class = getattr(module, class_name, None)
    if plugin_class is None:
        for attr in dir(module):
            if "Curator" in attr and not attr.startswith("_"):
                plugin_class = getattr(module, attr)
                break
    if plugin_class is None:
        raise AttributeError(f"No Curator class found in plugin '{plugin_name}'")
    plugin_config = get_plugin_config("curators", plugin_name)
    return plugin_class, plugin_config


@router.post("/curator/evaluate/{session_id}")
async def evaluate_session(session_id: str):
    try:
        result = curator_manager.evaluate_session(session_id)
        if result:
            return result
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/curator/evaluate/all")
async def evaluate_all_sessions():
    try:
        return curator_manager.evaluate_all()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/curator/config")
async def get_curator_config():
    return {
        "active_curator": ACTIVE_CURATOR,
        "enabled": curator_manager.enabled,
        "auto_approve_threshold": curator_manager.auto_approve_threshold,
        "plugin_config": get_plugin_config("curators", ACTIVE_CURATOR),
    }


@router.put("/curator/config")
async def update_curator_config(config: dict):
    if "enabled" in config:
        curator_manager.enabled = config["enabled"]
    if "auto_approve_threshold" in config:
        curator_manager.auto_approve_threshold = config["auto_approve_threshold"]

    return {
        "active_curator": ACTIVE_CURATOR,
        "enabled": curator_manager.enabled,
        "auto_approve_threshold": curator_manager.auto_approve_threshold,
    }


@router.post("/curator/evaluate/active/{session_id}")
async def evaluate_with_active_plugin(session_id: str):
    """使用当前激活的 curator 插件评分（由 config.yaml plugins.active_curator 决定）"""
    try:
        from managers.session_manager import session_manager
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        content = session_manager.get_session_content(session_id)
        if not content:
            raise HTTPException(status_code=404, detail=f"Session content not found")

        CuratorClass, plugin_config = _load_curator_plugin(ACTIVE_CURATOR)
        curator = CuratorClass(plugin_config)
        result = curator.evaluate(content)
        result["plugin"] = ACTIVE_CURATOR
        result["session_id"] = session_id
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
