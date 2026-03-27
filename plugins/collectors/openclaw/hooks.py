# @file plugins/collectors/openclaw/hooks.py
# @brief OpenClaw 采集器插件 hooks
# @create 2026-03-26

from core.hook_manager import hook_manager


@hook_manager.hook("collector_manager_scan_after")
def openclaw_collector_scan(args, result):
    """OpenClaw 采集器扫描钩子"""
    pass
