# @file plugins/collectors/default/hooks.py
# @brief 默认采集器插件 hooks
# @create 2026-03-26

from core.hook_manager import hook_manager


@hook_manager.hook("collector_manager_scan_after")
def default_collector_scan(args, result):
    """默认采集器扫描钩子"""
    pass


@hook_manager.hook("collector_manager_import_after")
def default_collector_import(args, result):
    """默认采集器导入钩子"""
    pass
