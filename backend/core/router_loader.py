# @file backend/core/router_loader.py
# @brief 自动路由加载器
# @create 2026-03-18

from fastapi import APIRouter
import importlib
from pathlib import Path
from typing import List, Optional


def include_routers_from_directory(
    parent_router: APIRouter,
    package_name: str,
    directory_path: Path,
    *,
    skip_modules: Optional[List[str]] = None,
    auto_tag: bool = False,
    auto_prefix: bool = False
) -> None:
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
                print(f"[RouterLoader] 已挂载: {package_name}.{module_name}, **{kwargs}")

        except Exception as e:
            print(f"[RouterLoader] 挂载失败 {module_name}: {str(e)}")
