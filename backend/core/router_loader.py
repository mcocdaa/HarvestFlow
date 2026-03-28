# @file backend/core/router_loader.py
# @brief 自动路由加载器 - 从目录自动发现并加载 FastAPI 路由
# @create 2026-03-18

import logging
from fastapi import APIRouter
import importlib
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def include_routers_from_directory(
    parent_router: APIRouter,
    package_name: str,
    directory_path: Path,
    *,
    skip_modules: Optional[List[str]] = None,
    auto_tag: bool = False,
    auto_prefix: bool = False
) -> None:
    """自动从目录加载并挂载路由

    扫描指定目录下的 Python 模块，查找 router 属性并挂载到父路由

    Args:
        parent_router: 父级 APIRouter，所有找到的路由都会挂载到这里
        package_name: Python 包名（用于导入模块）
        directory_path: 要扫描的目录路径
        skip_modules: 要跳过的模块名称列表
        auto_tag: 是否自动为路由添加标签（使用模块名）
        auto_prefix: 是否自动添加路由前缀（使用模块名）
    """
    if skip_modules is None:
        skip_modules = []

    base_name = package_name.split(".")[-1]

    for path in directory_path.iterdir():
        if path.name == "__init__.py":
            continue

        module_name = None

        if path.is_file() and path.suffix == ".py":
            module_name = path.stem
        elif path.is_dir() and (path / "__init__.py").exists():
            module_name = path.name

        if not module_name or module_name in skip_modules:
            continue

        try:
            module = importlib.import_module(f".{module_name}", package=package_name)

            if hasattr(module, "router"):
                sub_router = getattr(module, "router")

                kwargs = {"prefix": f"/{base_name}"}
                if auto_tag:
                    kwargs["tags"] = [module_name]
                if auto_prefix:
                    kwargs["prefix"] += f"/{module_name}"

                parent_router.include_router(sub_router, **kwargs)
                logger.info(f"[RouterLoader] 已挂载: {package_name}.{module_name}, **{kwargs}")

        except Exception as e:
            logger.error(f"[RouterLoader] 挂载失败 {module_name}: {str(e)}")
