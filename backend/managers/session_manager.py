# @file backend/managers/session_manager.py
# @brief 会话管理器 - 管理会话生命周期和文件读写
# @create 2026-03-18

import json
import os
import logging
from typing import Optional, Dict, Any
import argparse

from core import database_manager, setting_manager, hook_manager


class SessionManager:
    """会话管理器

    职责：
    1. 管理会话的生命周期
    2. 会话内容的文件读写
    3. 调用 DatabaseManager 封装的数据库操作

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("session_manager_construct_before", "session_manager_construct_after")
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_dir: str = ""

    @hook_manager.wrap_hooks(after="session_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数

        Args:
            parser: argparse.ArgumentParser 实例
        """
        group = parser.add_argument_group("Session", "Session Management")
        group.add_argument(
            "--session-data-dir",
            type=str,
            default=None,
            help="会话数据目录"
        )

    @hook_manager.wrap_hooks("session_manager_init_before", "session_manager_init_after")
    def init(self, args: argparse.Namespace):
        """初始化会话管理器

        Args:
            args: 解析后的参数
        """
        if getattr(args, 'session_data_dir', None):
            self.data_dir = args.session_data_dir
        else:
            self.data_dir = setting_manager.get("DATA_DIR", "./data")

    @property
    def raw_sessions_dir(self) -> str:
        return os.path.join(self.data_dir, "raw_sessions")

    @property
    def agent_curated_dir(self) -> str:
        return os.path.join(self.data_dir, "agent_curated")

    @property
    def human_approved_dir(self) -> str:
        return os.path.join(self.data_dir, "human_approved")

    @hook_manager.wrap_hooks("session_manager_create_before", "session_manager_create_after")
    def create_session(self, session_data: Dict) -> Dict:
        """创建会话

        Args:
            session_data: 会话数据字典

        Returns:
            创建后的会话数据
        """
        return database_manager.session_create(session_data)

    @hook_manager.wrap_hooks("session_manager_get_before", "session_manager_get_after")
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话

        Args:
            session_id: 会话 ID

        Returns:
            会话数据，不存在返回 None
        """
        return database_manager.session_get(session_id)

    @hook_manager.wrap_hooks("session_manager_list_before", "session_manager_list_after")
    def get_sessions(
        self,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "recent"
    ) -> Dict:
        """获取会话列表

        Args:
            status: 会话状态过滤
            page: 页码
            page_size: 每页数量
            sort: 排序方式

        Returns:
            会话列表分页结果
        """
        return database_manager.session_get_all(
            status=status,
            page=page,
            page_size=page_size,
            sort=sort
        )

    @hook_manager.wrap_hooks("session_manager_update_before", "session_manager_update_after")
    def update_session(self, session_id: str, updates: Dict) -> Optional[Dict]:
        """更新会话

        Args:
            session_id: 会话 ID
            updates: 更新数据字典

        Returns:
            更新后的会话数据，失败返回 None
        """
        return database_manager.session_update(session_id, updates)

    @hook_manager.wrap_hooks("session_manager_delete_before", "session_manager_delete_after")
    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否删除成功
        """
        return database_manager.session_delete(session_id)

    @hook_manager.wrap_hooks("session_manager_content_get_before", "session_manager_content_get_after")
    def get_session_content(self, session_id: str) -> Optional[Dict]:
        """获取会话内容

        Args:
            session_id: 会话 ID

        Returns:
            会话内容，失败返回 None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        file_path = session.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None


session_manager = SessionManager()
