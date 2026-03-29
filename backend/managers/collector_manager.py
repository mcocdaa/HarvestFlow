# @file backend/managers/collector_manager.py
# @brief 采集管理器 - 负责扫描文件夹和导入会话
# @create 2026-03-18

import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import argparse

from core import hook_manager, setting_manager
from managers.session_manager import session_manager


DEFAULT_POLL_INTERVAL = 60


class CollectorManager:
    """采集管理器

    职责：
    1. 扫描文件夹导入会话
    2. 解析会话文件
    3. 管理监控文件夹列表

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("collector_manager_construct_before", "collector_manager_construct_after")
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.watch_folders: List[str] = []
        self.poll_interval: int = DEFAULT_POLL_INTERVAL

    @hook_manager.wrap_hooks(after="collector_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数

        Args:
            parser: argparse.ArgumentParser 实例
        """
        group = parser.add_argument_group("Collector", "Collector Settings")
        group.add_argument(
            "--watch-folders",
            type=str,
            default="",
            help="监控文件夹列表，逗号分隔"
        )
        group.add_argument(
            "--poll-interval",
            type=int,
            default=DEFAULT_POLL_INTERVAL,
            help=f"轮询间隔（秒）(默认: {DEFAULT_POLL_INTERVAL})"
        )

    @hook_manager.wrap_hooks("collector_manager_init_before", "collector_manager_init_after")
    def init(self, args: argparse.Namespace):
        """初始化采集管理器

        Args:
            args: 解析后的参数
        """
        self.watch_folders = []
        watch_folders_val = getattr(args, 'watch_folders', setting_manager.get("WATCH_FOLDERS", ""))
        if watch_folders_val:
            for folder in watch_folders_val.split(","):
                folder = folder.strip()
                if folder:
                    self.watch_folders.append(folder)

        self.poll_interval = getattr(args, 'poll_interval', setting_manager.get("POLL_INTERVAL", DEFAULT_POLL_INTERVAL))
        self.poll_interval = int(self.poll_interval)

    @hook_manager.wrap_hooks("collector_manager_scan_before", "collector_manager_scan_after")
    def scan_folder(self, folder_path: str = None) -> List[str]:
        """扫描文件夹获取 JSON 文件列表

        Args:
            folder_path: 文件夹路径，默认使用第一个监控文件夹

        Returns:
            JSON 文件路径列表
        """
        if folder_path is None:
            folder_path = self.watch_folders[0] if self.watch_folders else None

        if not folder_path or not os.path.exists(folder_path):
            return []

        json_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))

        return json_files

    @hook_manager.wrap_hooks("collector_manager_parse_before", "collector_manager_parse_after")
    def parse_session_file(self, file_path: str) -> Optional[Dict]:
        """解析会话文件

        Args:
            file_path: 会话文件路径

        Returns:
            解析后的会话数据，失败返回 None
        """
        try:
            # 首先尝试使用 jsonl 解析器（OpenClaw 等）
            if file_path.endswith('.jsonl'):
                # jsonl 文件需要特殊处理，逐行读取
                messages = []
                session_id = None
                agent_id = None

                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            msg = json.loads(line)
                            msg_type = msg.get('type', '')
                            if msg_type == 'message':
                                message_data = msg.get('message', {})
                                role = message_data.get('role', 'user')
                                content_list = message_data.get('content', [])

                                # 提取文本内容
                                text_content = ""
                                if isinstance(content_list, list):
                                    for item in content_list:
                                        if isinstance(item, dict) and item.get('type') == 'text':
                                            text_content += item.get('text', '')
                                elif isinstance(content_list, str):
                                    text_content = content_list

                                if text_content:
                                    messages.append({
                                        "role": role,
                                        "content": text_content
                                    })

                            # 提取 session_id
                            if not session_id and msg.get('id'):
                                session_id = msg.get('id')

                        except json.JSONDecodeError:
                            continue

                if messages and session_id:
                    # 从文件路径提取 agent_id
                    parts = file_path.split(os.sep)
                    if 'agents' in parts:
                        idx = parts.index('agents')
                        if idx + 1 < len(parts):
                            agent_id = parts[idx + 1]

                    return {
                        "session_id": session_id,
                        "agent_id": agent_id,
                        "messages": messages,
                        "message_count": len(messages),
                        "has_tool_calls": False,
                        "tools_used": [],
                    }

            # 默认处理：尝试作为普通 JSON 文件读取
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            session_id = data.get("session_id")
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
                data["session_id"] = session_id

            return data
        except Exception as e:
            self.logger.error(f"解析文件失败 {file_path}: {e}")
            return None

    @hook_manager.wrap_hooks("collector_manager_import_before", "collector_manager_import_after")
    def import_session(self, file_path: str) -> Optional[str]:
        """导入单个会话

        Args:
            file_path: 源文件路径

        Returns:
            导入的会话 ID，失败返回 None
        """
        session_data = self.parse_session_file(file_path)
        if not session_data:
            return None

        session_id = session_data.get("session_id")

        session_data["file_path"] = file_path
        session_data["content"] = session_data

        try:
            session_manager.create_session(session_data)
        except Exception as e:
            self.logger.error(f"创建会话记录失败：{e}")
            return None

        return session_id

    @hook_manager.wrap_hooks("collector_manager_import_all_before", "collector_manager_import_all_after")
    def import_all(self, folder_path: str = None) -> Dict:
        """导入所有会话

        Args:
            folder_path: 文件夹路径，默认使用第一个监控文件夹

        Returns:
            导入结果统计字典
        """
        files = self.scan_folder(folder_path)

        imported = []
        failed = []

        for file_path in files:
            session_id = self.import_session(file_path)
            if session_id:
                imported.append(session_id)
            else:
                failed.append(file_path)

        return {
            "total": len(files),
            "imported": len(imported),
            "failed": len(failed),
            "session_ids": imported,
            "failed_files": failed,
        }

    def add_watch_folder(self, folder_path: str):
        """添加监控文件夹

        Args:
            folder_path: 要添加的文件夹路径
        """
        if folder_path not in self.watch_folders:
            self.watch_folders.append(folder_path)

    def remove_watch_folder(self, folder_path: str):
        """移除监控文件夹

        Args:
            folder_path: 要移除的文件夹路径
        """
        if folder_path in self.watch_folders:
            self.watch_folders.remove(folder_path)


collector_manager = CollectorManager()
