# @file backend/core/__init__.py
# @brief 核心模块导出

from .database import Database, get_database, close_database
from .plugin_loader import PluginLoader, plugin_loader
from .router_loader import include_routers_from_directory
