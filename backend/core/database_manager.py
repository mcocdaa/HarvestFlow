# @file backend/core/database_manager.py
# @brief 数据库管理器 - 封装所有数据库操作
# @create 2026-03-22

import os
import sqlite3
import json
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import argparse

from core import hook_manager
from core import setting_manager

class DatabaseManager:
    """数据库管理器

    职责：
    1. 管理 SQLite 数据库连接
    2. 初始化数据库表结构
    3. 封装所有数据库业务操作（外部不允许调用 raw SQL）

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("database_manager_construct_before", "database_manager_construct_after")
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path: str = ""
        self.connection: Optional[sqlite3.Connection] = None
        self._write_lock = threading.Lock()

    @hook_manager.wrap_hooks(after="database_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数

        Args:
            parser: argparse.ArgumentParser 实例
        """
        group = parser.add_argument_group("Database", "Database Settings")

        group.add_argument(
            "--db-path",
            type=str,
            default=os.getenv("DB_PATH", "./data/db/harvestflow.db"),
            help="数据库路径 (默认: ./data/db/harvestflow.db)"
        )

    @hook_manager.wrap_hooks("database_manager_initialize_before", "database_manager_initialize_after")
    def init(self, args: argparse.Namespace):
        """初始化数据库连接

        Args:
            args: 解析后的参数
        """
        self.db_path = getattr(args, 'db_path', setting_manager.get("DB_PATH", "./data/db/harvestflow.db"))

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")

        self._initialize_tables()
        self.logger.info(f"✓ 数据库连接已建立: {self.db_path}")

    def _initialize_tables(self):
        """初始化数据库表结构"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        self._create_table("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                file_path TEXT,
                content TEXT,
                status TEXT DEFAULT 'raw',
                quality_auto_score INTEGER,
                quality_manual_score INTEGER,
                agent_role TEXT,
                task_type TEXT,
                tools_used TEXT,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 添加 content 列（如果不存在，兼容旧数据库）
        existing_columns = [row[1] for row in self.connection.execute("PRAGMA table_info(sessions)").fetchall()]
        if "content" not in existing_columns:
            self.connection.execute("ALTER TABLE sessions ADD COLUMN content TEXT")
            self.connection.commit()

        self._create_table("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                action TEXT NOT NULL,
                operator TEXT DEFAULT 'system',
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self._create_table("""
            CREATE TABLE IF NOT EXISTS export_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                export_format TEXT NOT NULL,
                file_path TEXT NOT NULL,
                filters TEXT,
                record_count INTEGER,
                version TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self._create_table("""
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                plugin_type TEXT NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                config TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.logger.debug("✓ 数据库表结构已初始化")

    def _create_table(self, sql: str):
        """创建表（内部方法）"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")
        self.connection.execute(sql)
        self.connection.commit()

    @contextmanager
    def transaction(self):
        """事务上下文管理器（持有写锁）"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        with self._write_lock:
            try:
                yield self.connection
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                raise e

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("✓ 数据库连接已关闭")

    def session_create(self, session_data: Dict) -> Dict:
        """创建会话"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        content_json = None
        if "content" in session_data:
            content_json = json.dumps(session_data["content"])

        with self._write_lock:
            self.connection.execute(
                """INSERT INTO sessions (session_id, file_path, content, status, agent_role, task_type, tools_used, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_data.get("session_id"),
                    session_data.get("file_path", ""),
                    content_json,
                    session_data.get("status", "raw"),
                    session_data.get("agent_role"),
                    session_data.get("task_type"),
                    json.dumps(session_data.get("tools_used", [])),
                    json.dumps(session_data.get("tags", [])),
                )
            )
            self.connection.commit()
        return session_data

    def session_get(self, session_id: str) -> Optional[Dict]:
        """获取单个会话"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        cursor = self.connection.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            session = self._row_to_dict(row)
            session = self._deserialize_session_fields(session)
            return session
        return None

    def session_get_all(
        self,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "recent"
    ) -> Dict:
        """获取会话列表"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        where_clause = ""
        params = []
        if status:
            where_clause = "WHERE status = ?"
            params = [status]

        sort_order = "DESC" if sort == "recent" else "ASC"
        offset = (page - 1) * page_size

        count_cursor = self.connection.execute(
            f"SELECT COUNT(*) as total FROM sessions {where_clause}", tuple(params)
        )
        total = dict(count_cursor.fetchone())["total"]

        query = f"""SELECT * FROM sessions {where_clause}
                    ORDER BY created_at {sort_order}
                    LIMIT ? OFFSET ?"""
        params.extend([page_size, offset])

        cursor = self.connection.execute(query, tuple(params))
        rows = cursor.fetchall()

        sessions = []
        for row in rows:
            session = self._row_to_dict(row)
            session = self._deserialize_session_fields(session)
            sessions.append(session)

        return {
            "sessions": sessions,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def session_update(self, session_id: str, updates: Dict) -> Optional[Dict]:
        """更新会话"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        allowed_fields = [
            "status", "quality_auto_score", "quality_manual_score",
            "agent_role", "task_type", "tools_used", "tags"
        ]

        set_clauses = []
        params = []
        for field in allowed_fields:
            if field in updates:
                value = updates[field]
                if field in ("tools_used", "tags"):
                    value = json.dumps(value) if isinstance(value, list) else value
                set_clauses.append(f"{field} = ?")
                params.append(value)

        if not set_clauses:
            return None

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(session_id)

        query = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
        with self._write_lock:
            self.connection.execute(query, tuple(params))
            self.connection.commit()

        return self.session_get(session_id)

    def session_delete(self, session_id: str) -> bool:
        """删除会话"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        session = self.session_get(session_id)
        if not session:
            return False

        if session.get("file_path") and os.path.exists(session["file_path"]):
            try:
                os.remove(session["file_path"])
            except Exception:
                pass

        with self._write_lock:
            self.connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            self.connection.commit()
        return True

    def session_get_by_status(self, status: str) -> List[Dict]:
        """按状态获取会话"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        cursor = self.connection.execute(
            "SELECT session_id FROM sessions WHERE status = ?", (status,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def audit_log_create(self, session_id: str, action: str, operator: str = "system", details: str = None) -> None:
        """创建审计日志"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        with self._write_lock:
            self.connection.execute(
                "INSERT INTO audit_logs (session_id, action, operator, details) VALUES (?, ?, ?, ?)",
                (session_id, action, operator, details)
            )
            self.connection.commit()

    def audit_log_get(self, session_id: str = None, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        if session_id:
            cursor = self.connection.execute(
                "SELECT * FROM audit_logs WHERE session_id = ? ORDER BY created_at DESC",
                (session_id,)
            )
        else:
            cursor = self.connection.execute(
                "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]

    def export_record_create(
        self,
        export_format: str,
        file_path: str,
        filters: Dict,
        record_count: int,
        version: str
    ) -> None:
        """创建导出记录"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        with self._write_lock:
            self.connection.execute(
                """INSERT INTO export_records
                   (export_format, file_path, filters, record_count, version)
                   VALUES (?, ?, ?, ?, ?)""",
                (export_format, file_path, json.dumps(filters), record_count, version)
            )
            self.connection.commit()

    def export_record_get_history(self, limit: int = 20) -> List[Dict]:
        """获取导出历史"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        cursor = self.connection.execute(
            "SELECT * FROM export_records ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def session_get_for_export(
        self,
        min_score: int = None,
        agent_role: str = None,
        task_type: str = None,
        tags: List[str] = None
    ) -> List[Dict]:
        """获取用于导出的会话"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        query = "SELECT * FROM sessions WHERE status = 'approved'"
        params = []

        if min_score is not None:
            query += " AND quality_manual_score >= ?"
            params.append(min_score)

        if agent_role:
            query += " AND agent_role = ?"
            params.append(agent_role)

        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)

        if tags:
            placeholders = ",".join("?" * len(tags))
            query += (
                f" AND EXISTS ("
                f"SELECT 1 FROM json_each(sessions.tags) WHERE value IN ({placeholders})"
                f")"
            )
            params.extend(tags)

        cursor = self.connection.execute(query, tuple(params))
        sessions = [self._row_to_dict(row) for row in cursor.fetchall()]
        return sessions

    def plugin_upsert(self, name: str, plugin_type: str, config: Dict) -> None:
        """插入或更新插件信息"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        with self._write_lock:
            self.connection.execute(
                """INSERT OR REPLACE INTO plugins
                   (name, plugin_type, is_enabled, config)
                   VALUES (?, ?, ?, ?)""",
                (name, plugin_type, 1, json.dumps(config))
            )
            self.connection.commit()

    def plugin_get_all(self) -> List[Dict]:
        """获取所有插件"""
        if not self.connection:
            raise RuntimeError("数据库未初始化")

        cursor = self.connection.execute(
            "SELECT * FROM plugins ORDER BY plugin_type, name"
        )
        plugins = []
        for row in cursor.fetchall():
            plugin = self._row_to_dict(row)
            if plugin.get("config"):
                plugin["config"] = json.loads(plugin["config"])
            plugins.append(plugin)
        return plugins

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将 Row 转换为字典"""
        return dict(row)

    def _deserialize_session_fields(self, session: Dict) -> Dict:
        """反序列化会话的 JSON 字段"""
        if session.get("tags"):
            session["tags"] = json.loads(session["tags"])
        if session.get("tools_used"):
            session["tools_used"] = json.loads(session["tools_used"])
        if session.get("content"):
            try:
                session["content"] = json.loads(session["content"])
            except json.JSONDecodeError:
                pass
        return session


database_manager = DatabaseManager()
