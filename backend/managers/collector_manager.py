# @file backend/managers/collector_manager.py
# @brief 采集管理器 - 负责扫描文件夹和导入会话
# @create 2026-03-18

import os
import json
import threading
from typing import List, Dict, Optional
from datetime import datetime, timezone
import argparse

from core import hook_manager, setting_manager, parsers
from managers.base import BaseManager
from managers.session_manager import session_manager


WATCH_CONFIG_FILENAME = "watch_folders.json"
DEFAULT_WATCH_INTERVAL = 30


class CollectorManager(BaseManager):
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
        super().__init__()
        self.watch_folders: List[str] = []
        self.watch_enabled: bool = False
        self.watch_interval: int = DEFAULT_WATCH_INTERVAL
        self.last_runs: Dict[str, Dict] = {}
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None

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
            default=None,
            help="监控文件夹列表，逗号分隔"
        )

    @hook_manager.wrap_hooks("collector_manager_init_before", "collector_manager_init_after")
    def init(self, args: argparse.Namespace):
        """初始化采集管理器

        Args:
            args: 解析后的参数
        """
        self.watch_folders = []
        watch_folders_val = getattr(args, 'watch_folders', None)
        if watch_folders_val is None:
            watch_folders_val = setting_manager.get("WATCH_FOLDERS", "")
        if watch_folders_val:
            for folder in watch_folders_val.split(","):
                folder = folder.strip()
                if folder:
                    self.watch_folders.append(folder)

        self.watch_enabled = str(setting_manager.get("WATCH_ENABLED", "false")).lower() in ("1", "true", "yes", "on")
        try:
            self.watch_interval = int(setting_manager.get("WATCH_INTERVAL_SECONDS", DEFAULT_WATCH_INTERVAL))
        except (TypeError, ValueError):
            self.watch_interval = DEFAULT_WATCH_INTERVAL
        if self.watch_interval <= 0:
            self.watch_interval = DEFAULT_WATCH_INTERVAL

        # 运行时配置（JSON）优先于环境变量
        self._load_watch_config()

    def _watch_config_path(self) -> str:
        """监听配置文件路径（DATA_DIR/watch_folders.json）"""
        data_dir = setting_manager.get("DATA_DIR", "./data")
        return os.path.join(data_dir, WATCH_CONFIG_FILENAME)

    def _load_watch_config(self):
        """加载持久化的监听配置，缺失或损坏时保持环境变量配置"""
        path = self._watch_config_path()
        if not os.path.isfile(path):
            return
        try:
            with open(path, encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self.logger.warning(f"监听配置读取失败 {path}: {e}")
            return

        folders = config.get("folders")
        if isinstance(folders, list):
            self.watch_folders = [str(folder) for folder in folders if str(folder).strip()]
        if isinstance(config.get("enabled"), bool):
            self.watch_enabled = config["enabled"]
        interval = config.get("interval")
        if isinstance(interval, int) and interval > 0:
            self.watch_interval = interval

    def _persist_watch_config(self):
        """持久化监听配置（目录增删 / 启停后调用）"""
        path = self._watch_config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "enabled": self.watch_enabled,
                    "interval": self.watch_interval,
                    "folders": self.watch_folders,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

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
        """解析会话文件（.jsonl 由采集器插件经 parse_before 钩子接管）

        Args:
            file_path: 会话文件路径

        Returns:
            解析后的会话数据，失败返回 None
        """
        return parsers.parse_json_file(file_path)

    def _build_session_record(self, file_path: str, session_data: Dict) -> Dict:
        """构造入库记录：content 保存原始数据快照，file_path 附加来源路径"""
        record = dict(session_data)
        record["file_path"] = file_path
        record["content"] = dict(session_data)
        return record

    def _create_session(self, record: Dict) -> Optional[str]:
        """调用 session_manager 创建会话，返回 session_id，失败记录日志返回 None"""
        try:
            session_manager.create_session(record)
        except Exception as e:
            self.logger.error(f"创建会话记录失败：{e}")
            return None
        return record.get("session_id")

    def _import_parsed(self, file_path: str, session_data: Dict) -> Optional[str]:
        """已解析数据的导入公共路径：构造记录 + 入库（import_session / import_all 共用）"""
        record = self._build_session_record(file_path, session_data)
        return self._create_session(record)

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
        return self._import_parsed(file_path, session_data)

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
        skipped = []

        for file_path in files:
            session_data = self.parse_session_file(file_path)
            if not session_data:
                failed.append(file_path)
                continue

            session_id = session_data.get("session_id")
            if session_id and session_manager.get_session(session_id):
                skipped.append(session_id)
                continue

            created_id = self._import_parsed(file_path, session_data)
            if created_id is None:
                failed.append(file_path)
                continue
            imported.append(created_id)

        return {
            "total": len(files),
            "imported": len(imported),
            "skipped": len(skipped),
            "failed": len(failed),
            "session_ids": imported,
            "skipped_ids": skipped,
            "failed_files": failed,
        }

    def add_watch_folder(self, folder_path: str):
        """添加监控文件夹（内存 + 持久化）

        Args:
            folder_path: 要添加的文件夹路径
        """
        if folder_path not in self.watch_folders:
            self.watch_folders.append(folder_path)
            self._persist_watch_config()

    def remove_watch_folder(self, folder_path: str):
        """移除监控文件夹（内存 + 持久化）

        Args:
            folder_path: 要移除的文件夹路径
        """
        if folder_path in self.watch_folders:
            self.watch_folders.remove(folder_path)
            self.last_runs.pop(folder_path, None)
            self._persist_watch_config()

    def _is_watching(self) -> bool:
        """监听线程是否运行中"""
        return self._watch_thread is not None and self._watch_thread.is_alive()

    @hook_manager.wrap_hooks("collector_manager_get_watch_state_before", "collector_manager_get_watch_state_after")
    def get_watch_state(self) -> Dict:
        """获取监听状态（供前端展示）"""
        return {
            "enabled": self.watch_enabled,
            "running": self._is_watching(),
            "interval": self.watch_interval,
            "folders": list(self.watch_folders),
            "last_runs": dict(self.last_runs),
        }

    @hook_manager.wrap_hooks("collector_manager_set_watch_enabled_before", "collector_manager_set_watch_enabled_after")
    def set_watch_enabled(self, enabled: bool) -> Dict:
        """启用/停用目录监听（持久化并即时生效）"""
        self.watch_enabled = bool(enabled)
        self._persist_watch_config()
        if self.watch_enabled:
            self.start_watching()
        else:
            self.stop_watching()
        return self.get_watch_state()

    def start_watching(self):
        """启动后台监听线程（幂等）"""
        if self._is_watching():
            return
        self._stop_event = threading.Event()
        self._watch_thread = threading.Thread(
            target=self._watch_loop, name="harvestflow-watcher", daemon=True
        )
        self._watch_thread.start()
        self.logger.info(
            f"目录监听已启动：interval={self.watch_interval}s, folders={self.watch_folders}"
        )

    def stop_watching(self):
        """停止后台监听线程（幂等）"""
        if self._stop_event is not None:
            self._stop_event.set()
        if self._watch_thread is not None and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=5)
        self._watch_thread = None
        self._stop_event = None

    def _watch_loop(self):
        """后台轮询：按 interval 周期性导入监听目录中的新文件"""
        while self._stop_event is not None and not self._stop_event.wait(self.watch_interval):
            try:
                self.watch_run_once()
            except Exception as e:
                self.logger.error(f"目录监听执行失败：{e}", exc_info=True)

    @hook_manager.wrap_hooks("collector_manager_watch_run_before", "collector_manager_watch_run_after")
    def watch_run_once(self) -> Dict:
        """立即对所有监听目录执行一次导入，并记录结果"""
        results = {}
        for folder in list(self.watch_folders):
            try:
                result = self.import_all(folder)
            except Exception as e:
                self.logger.error(f"监听导入失败 {folder}: {e}", exc_info=True)
                result = {"total": 0, "imported": 0, "skipped": 0, "failed": 0, "error": str(e)}
            result = {**result, "at": datetime.now(timezone.utc).isoformat()}
            self.last_runs[folder] = result
            results[folder] = result
        return results


collector_manager = CollectorManager()


@hook_manager.hook("app_lifespan_start")
async def _collector_start_watcher(app):
    """应用启动时按持久化配置启动监听"""
    if collector_manager.watch_enabled:
        collector_manager.start_watching()


@hook_manager.hook("app_lifespan_shutdown")
async def _collector_stop_watcher(app):
    """应用关闭时停止监听线程"""
    collector_manager.stop_watching()
