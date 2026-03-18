# @file backend/api/__init__.py
# @brief API 路由总入口
# @create 2026-03-18

import importlib
from fastapi import FastAPI
from config import API_VERSION


def register_routers(app: FastAPI):
    version_package_name = f"{__name__}.{API_VERSION}"

    try:
        version_package = importlib.import_module(version_package_name)
    except ModuleNotFoundError:
        raise RuntimeError(f"API 版本模块不存在: {version_package_name}")

    if hasattr(version_package, "router"):
        app.include_router(
            version_package.router,
            prefix=f"/api",
            tags=[API_VERSION.upper()]
        )
        print(f"[Route] 已注册 API 版本: {API_VERSION}")
    else:
        raise AttributeError(f"模块 {version_package_name} 中未找到 'router' 对象")
