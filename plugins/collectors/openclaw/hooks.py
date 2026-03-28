# @file plugins/collectors/openclaw/hooks.py
# @brief OpenClaw 采集器插件 hooks
# @create 2026-03-26

import logging
from core.hook_manager import hook_manager
from plugins.collectors.openclaw.backend import get_collector

logger = logging.getLogger(__name__)


@hook_manager.hook("collector_manager_scan_after")
def openclaw_collector_scan(self, result):
    """OpenClaw 采集器扫描钩子 - 扫描 jsonl 文件"""
    logger.info(f"[OpenClaw] 扫描钩子被调用，当前结果：{len(result)} 个文件")
    collector = get_collector()
    if collector:
        logger.info(f"[OpenClaw] 采集器已加载，agents_dir: {collector.agents_dir}")
        jsonl_files = collector.scan()
        logger.info(f"[OpenClaw] 扫描到 {len(jsonl_files)} 个 jsonl 文件：{jsonl_files}")
        if jsonl_files:
            result.extend(jsonl_files)
            logger.info(f"[OpenClaw] 扫描完成，总计 {len(result)} 个文件")
    return result


@hook_manager.hook("collector_manager_parse_before")
def openclaw_collector_parse_before(self, file_path):
    """OpenClaw 采集器解析前钩子 - 如果是 jsonl 文件，使用 OpenClaw 解析器"""
    if file_path.endswith('.jsonl'):
        collector = get_collector()
        if collector:
            parsed_data = collector.parse(file_path)
            if parsed_data:
                hook_manager.logger.info(f"[OpenClaw] 成功解析 {file_path}")
                return parsed_data
    return None
