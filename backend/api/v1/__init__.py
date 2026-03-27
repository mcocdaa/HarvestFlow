# @file backend/api/v1/__init__.py
# @brief API v1 模块路由汇总
# @create 2026-03-22

from fastapi import APIRouter
from pathlib import Path
from core.router_loader import include_routers_from_directory

router = APIRouter()

include_routers_from_directory(
    parent_router=router,
    package_name=__package__,
    directory_path=Path(__file__).parent,
    auto_tag=True,
    auto_prefix=False,
    skip_modules=[],
)
