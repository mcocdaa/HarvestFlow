# @file plugins/collectors/openclaw/hooks.py
# @brief OpenClaw 采集器插件 hooks
# @create 2026-03-26

import logging

from core.hook_manager import hook_manager
from plugins.collectors.openclaw.backend import get_collector

logger = logging.getLogger(__name__)


@hook_manager.hook("collector_manager_scan_after")
def openclaw_collector_scan(result, self, folder_path=None):
    """OpenClaw 采集器扫描钩子 - 将 openclaw 采集的 jsonl 文件合并进扫描结果

    Args:
        result: 内置扫描结果（文件路径列表）
        self: CollectorManager 实例
        folder_path: 被包装方法的 folder_path 参数

    Returns:
        合并后的文件路径列表
    """
    collector = get_collector()
    if not collector:
        return result

    logger.info(f"[OpenClaw] 采集器已加载，agents_dir: {collector.agents_dir}")
    jsonl_files = collector.scan()
    if jsonl_files:
        logger.info(f"[OpenClaw] 扫描到 {len(jsonl_files)} 个 jsonl 文件")
        result.extend(jsonl_files)
        logger.info(f"[OpenClaw] 扫描完成，总计 {len(result)} 个文件")
    return result


@hook_manager.hook("collector_manager_parse_before")
def openclaw_collector_parse_before(self, file_path):
    """OpenClaw 采集器解析前钩子 - 拦截 jsonl 文件短路内置解析

    Args:
        self: CollectorManager 实例
        file_path: 待解析文件路径

    Returns:
        解析结果（非 None 时短路内置解析器）
    """
    if not file_path.endswith('.jsonl'):
        return None

    collector = get_collector()
    if not collector:
        return None

    parsed_data = collector.parse(file_path)
    if parsed_data:
        logger.info(f"[OpenClaw] 成功解析 {file_path}")
    return parsed_data
