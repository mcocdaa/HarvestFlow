# @file plugins/examples/collector-example/backend.py
# @brief Example collector plugin implementation
# @create 2026-03-28

import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ExampleCollector:
    name = "collector-example"
    description = "Example collector plugin - demonstrates how to build a custom collector"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.watch_folders = self.config.get("watch_folders", [])
        self.custom_config = self.config.get("custom_config", {})

    def scan(self) -> List[str]:
        """扫描文件夹获取文件列表

        Returns:
            文件路径列表
        """
        logger.info(f"[ExampleCollector] Scanning folders: {self.watch_folders}")

        files = []
        for folder in self.watch_folders:
            if not os.path.exists(folder):
                logger.warning(f"[ExampleCollector] Folder not found: {folder}")
                continue

            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    if self._should_include_file(filename):
                        files.append(os.path.join(root, filename))

        logger.info(f"[ExampleCollector] Found {len(files)} files")
        return files

    def parse(self, file_path: str) -> Optional[Dict]:
        """解析会话文件

        Args:
            file_path: 会话文件路径

        Returns:
            解析后的会话数据，失败返回 None
        """
        try:
            logger.debug(f"[ExampleCollector] Parsing file: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 在这里可以添加自定义解析逻辑
            # 例如：转换数据格式、验证数据结构等
            parsed_data = self._transform_data(data)

            return parsed_data

        except Exception as e:
            logger.error(f"[ExampleCollector] Parse error for {file_path}: {e}")
            return None

    def _should_include_file(self, filename: str) -> bool:
        """判断是否应该包含该文件

        Args:
            filename: 文件名

        Returns:
            是否包含
        """
        # 示例：只包含 .json 文件
        return filename.endswith('.json')

    def _transform_data(self, data: Dict) -> Dict:
        """转换数据格式

        Args:
            data: 原始数据

        Returns:
            转换后的数据
        """
        # 示例：添加时间戳
        if 'metadata' not in data:
            data['metadata'] = {}

        data['metadata']['collected_by'] = self.name
        data['metadata']['version'] = '1.0.0'

        return data


collector_plugin = ExampleCollector()


def on_load():
    logger.info("[ExampleCollector] Plugin loaded")


def get_collector():
    return collector_plugin
