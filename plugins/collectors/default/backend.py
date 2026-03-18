# @file plugins/collectors/default/backend.py
# @brief 默认采集器插件
# @create 2026-03-18

import os
import json
from typing import List, Dict
from pathlib import Path


class DefaultCollector:
    name = "default"
    description = "Default file collector - scans folder for JSON files"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.watch_folders = self.config.get("watch_folders", [])

    def scan(self) -> List[str]:
        json_files = []
        for folder in self.watch_folders:
            if not os.path.exists(folder):
                continue
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith('.json'):
                        json_files.append(os.path.join(root, file))
        return json_files

    def parse(self, file_path: str) -> Dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[DefaultCollector] Parse error: {e}")
            return {}


collector_plugin = DefaultCollector()


def on_load():
    print("[DefaultCollector] Plugin loaded")


def get_collector():
    return collector_plugin
