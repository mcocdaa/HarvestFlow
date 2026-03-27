# @file backend/core/__init__.py
# @brief 核心模块 - 基础设施层
# @create 2026-03-22

from .hook_manager import HookManager, hook_manager
from .setting_manager import SettingManager, setting_manager
from .secrets_manager import SecretsManager, secrets_manager
from .database_manager import DatabaseManager, database_manager
from .plugin_manager import PluginManager, plugin_manager

__all__ = [
    "hook_manager",
    "setting_manager",
    "secrets_manager",
    "database_manager",
    "plugin_manager",
]
