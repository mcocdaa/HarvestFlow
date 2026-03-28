# @file plugins/collectors/default/backend.py
# @brief 默认采集器插件
# @create 2026-03-18

import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DefaultCollector:
    name = "default"
    description = "Default file collector - scans folder for JSON files"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.watch_folders = self.config.get("watch_folders", [])

    def scan(self) -> List[str]:
        """扫描文件夹获取 JSON 文件列表

        Returns:
            JSON 文件路径列表
        """
        json_files = []
        for folder in self.watch_folders:
            if not os.path.exists(folder):
                continue
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith('.json'):
                        json_files.append(os.path.join(root, file))
        return json_files

    def parse(self, file_path: str) -> Optional[Dict]:
        """解析会话文件

        Args:
            file_path: 会话文件路径

        Returns:
            解析后的会话数据，失败返回 None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[DefaultCollector] Parse error: {e}")
            return {}


collector_plugin = DefaultCollector()


def on_load():
    logger.info("[DefaultCollector] Plugin loaded")


def get_collector():
    return collector_plugin
