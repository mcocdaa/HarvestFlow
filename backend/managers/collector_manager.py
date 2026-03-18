# @file backend/managers/collector_manager.py
# @brief 采集管理器
# @create 2026-03-18

import json
import os
import shutil
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from core.database import get_database
from config import RAW_SESSIONS_DIR, COLLECTOR_CONFIG
from managers.session_manager import session_manager


class CollectorManager:
    def __init__(self):
        self.db = None
        self.watch_folders = COLLECTOR_CONFIG.get("watch_folders", [])
        self.poll_interval = COLLECTOR_CONFIG.get("poll_interval", 60)

    def get_db(self):
        if not self.db:
            self.db = get_database()
        return self.db

    def scan_folder(self, folder_path: str = None) -> List[str]:
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

    def parse_session_file(self, file_path: str) -> Optional[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            session_id = data.get("session_id")
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
                data["session_id"] = session_id

            return data
        except Exception as e:
            print(f"[CollectorManager] 解析文件失败 {file_path}: {e}")
            return None

    def import_session(self, file_path: str, target_dir: str = None) -> Optional[str]:
        if target_dir is None:
            target_dir = RAW_SESSIONS_DIR

        session_data = self.parse_session_file(file_path)
        if not session_data:
            return None

        session_id = session_data.get("session_id")

        date_folder = datetime.now().strftime("%Y-%m-%d")
        dest_dir = os.path.join(target_dir, date_folder)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, f"{session_id}.json")

        try:
            shutil.copy2(file_path, dest_path)
        except Exception as e:
            print(f"[CollectorManager] 复制文件失败: {e}")
            return None

        session_data["file_path"] = dest_path
        try:
            session_manager.create_session(session_data)
        except Exception as e:
            print(f"[CollectorManager] 创建会话记录失败: {e}")
            return None

        return session_id

    def import_all(self, folder_path: str = None) -> Dict:
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
        if folder_path not in self.watch_folders:
            self.watch_folders.append(folder_path)

    def remove_watch_folder(self, folder_path: str):
        if folder_path in self.watch_folders:
            self.watch_folders.remove(folder_path)


collector_manager = CollectorManager()
