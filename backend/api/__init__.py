# @file backend/api/__init__.py
# @brief API 路由总入口 - 支持版本控制
# @create 2026-03-06

import importlib
import logging
from fastapi import FastAPI
from core import setting_manager

logger = logging.getLogger(__name__)


def register_routers(app: FastAPI):
    """
    自动注册指定版本的 API 路由：
    1. 从 setting_manager 获取 api_version 动态导入版本包 (如 api.v1)
    2. 查找该包下的全局 `router` 对象并挂载
    """
    api_version = setting_manager.api_version
    version_package_name = f"{__name__}.{api_version}"

    try:
        version_package = importlib.import_module(version_package_name)
    except ModuleNotFoundError:
        raise RuntimeError(f"API 版本模块不存在: {version_package_name}")

    if hasattr(version_package, "router"):
        app.include_router(
            version_package.router,
            prefix=f"/api",
            tags=[api_version.upper()]
        )
        logger.info(f"[Route] 已注册 API 版本: {api_version}")
    else:
        raise AttributeError(f"模块 {version_package_name} 中未找到 'router' 对象")
