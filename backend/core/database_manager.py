# @file backend/core/database_manager.py
# @brief 数据库管理器 - 封装所有数据库操作，基于 1 写 + 4~8 读连接池架构
# @create 2026-03-22

import os
import sqlite3
import json
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
import argparse

from core import hook_manager
from core import setting_manager
from core.constants import (
    MAX_PAGE_SIZE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_HISTORY_LIMIT,
    SessionStatus,
)
from core.db import DatabasePool, encode_cursor, decode_cursor


class DatabaseManager:
    """数据库管理器

    职责：
    1. 管理 SQLite 数据库读写分离连接池 (1 写连接 + 4~8 读连接池)
    2. 初始化数据库表结构与复合索引
    3. 封装所有数据库业务操作（外部不允许调用 raw SQL）
    4. 支持传统分页与 Keyset 游标分页

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("database_manager_construct_before", "database_manager_construct_after")
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path: str = ""
        self._pool: Optional[DatabasePool] = None
        self.connection: Optional[sqlite3.Connection] = None
        self._write_lock = threading.RLock()

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
        """初始化数据库连接池与表结构

        Args:
            args: 解析后的参数
        """
        self.db_path = getattr(args, 'db_path', setting_manager.get("DB_PATH", "./data/db/harvestflow.db"))

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._pool = DatabasePool(self.db_path)
        self.connection = self._pool.write_conn
        self._write_lock = self._pool._write_lock

        self._initialize_tables()
        self.logger.info(f"✓ 数据库连接池已建立 (1 写 + 4~8 读): {self.db_path}")

    def _initialize_tables(self):
        """初始化数据库表结构与复合索引"""
        conn = self._ensure()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY NOT NULL,
                file_path TEXT,
                content TEXT,
                status TEXT DEFAULT 'raw',
                quality_auto_score INTEGER,
                quality_manual_score INTEGER,
                agent_role TEXT,
                task_type TEXT,
                tools_used TEXT,
                tags TEXT,
                review_meta TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # 添加 content / review_meta 列（如果不存在，兼容旧数据库）
        existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()]
        if "content" not in existing_columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN content TEXT")
            conn.commit()
        if "review_meta" not in existing_columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN review_meta TEXT")
            conn.commit()

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

        # 加固复合索引以消除深分页与筛选的全表扫描
        if self._pool:
            self._pool.create_indexes()

        self.logger.debug("✓ 数据库表结构与索引已初始化")

    def _ensure(self) -> sqlite3.Connection:
        """确保连接可用并返回写连接对象，未初始化时抛错"""
        if not self._pool or not self.connection:
            raise RuntimeError("数据库未初始化")
        return self.connection

    def _write(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """写操作统一入口：写连接 + 独占锁 + 执行 + 提交

        Returns:
            execute 返回的 Cursor
        """
        self._ensure()
        with self._pool.writer() as conn:
            cursor = conn.execute(sql, params)
        return cursor

    def _create_table(self, sql: str):
        """创建表（内部方法）"""
        self._write(sql)

    def close(self):
        """关闭数据库读写连接池"""
        if self._pool:
            self._pool.close()
            self._pool = None
        self.connection = None
        self.logger.info("✓ 数据库连接已关闭")

    def session_create(self, session_data: Dict) -> Dict:
        """创建会话（重复 session_id 时返回已有记录）"""
        self._ensure()

        if not session_data.get("session_id"):
            return None

        content_json = None
        if "content" in session_data:
            content_json = json.dumps(session_data["content"])

        self._write(
            """INSERT OR IGNORE INTO sessions (session_id, file_path, content, status, agent_role, task_type, tools_used, tags)
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
        return self.session_get(session_data.get("session_id"))

    def session_get(self, session_id: str) -> Optional[Dict]:
        """获取单个会话（从读连接池查询）"""
        self._ensure()

        with self._pool.reader() as conn:
            cursor = conn.execute(
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
        sort: str = "recent",
        cursor: str = None
    ) -> Dict:
        """获取会话列表（支持传统分页与 Keyset 游标分页，消除深分页全表扫描）

        Args:
            status: 会话状态过滤
            page: 传统分页页码（当 cursor 为空时生效）
            page_size: 每页条数
            sort: "recent" (降序) 或 "oldest" (升序)
            cursor: Keyset 分页游标

        Returns:
            {"sessions", "total", "page", "page_size", "next_cursor", "has_more"}
        """
        self._ensure()

        page_size = self._clamp_limit(page_size, DEFAULT_PAGE_SIZE)
        sort_order = "DESC" if sort == "recent" else "ASC"

        with self._pool.reader() as conn:
            # 1. 优先使用 Keyset 游标分页
            if cursor:
                cursor_info = decode_cursor(cursor)
                if cursor_info:
                    cur_time, cur_id = cursor_info
                    where_clauses = []
                    params = []

                    if status:
                        where_clauses.append("status = ?")
                        params.append(status)

                    if sort == "recent":
                        where_clauses.append("(created_at < ? OR (created_at = ? AND session_id < ?))")
                        params.extend([cur_time, cur_time, cur_id])
                        order_clause = "ORDER BY created_at DESC, session_id DESC"
                    else:
                        where_clauses.append("(created_at > ? OR (created_at = ? AND session_id > ?))")
                        params.extend([cur_time, cur_time, cur_id])
                        order_clause = "ORDER BY created_at ASC, session_id ASC"

                    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

                    count_params = [status] if status else []
                    count_where = "WHERE status = ?" if status else ""
                    count_cursor = conn.execute(f"SELECT COUNT(*) as total FROM sessions {count_where}", tuple(count_params))
                    total = count_cursor.fetchone()["total"]

                    query = f"""SELECT session_id, file_path, status, quality_auto_score,
                                       quality_manual_score, agent_role, task_type, tools_used,
                                       tags, created_at, updated_at
                                FROM sessions {where_sql}
                                {order_clause}
                                LIMIT ?"""
                    params.append(page_size + 1)
                    rows = conn.execute(query, tuple(params)).fetchall()

                    has_more = len(rows) > page_size
                    result_rows = rows[:page_size]

                    next_cursor = None
                    if result_rows and has_more:
                        last = result_rows[-1]
                        next_cursor = encode_cursor(last["created_at"], last["session_id"])

                    sessions = [self._deserialize_session_fields(self._row_to_dict(r)) for r in result_rows]
                    return {
                        "sessions": sessions,
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                        "next_cursor": next_cursor,
                        "has_more": has_more,
                    }

            # 2. 传统 Offset 分页（向后兼容）
            page = max(1, page)
            where_clause = ""
            params = []
            if status:
                where_clause = "WHERE status = ?"
                params = [status]

            offset = (page - 1) * page_size

            count_cursor = conn.execute(
                f"SELECT COUNT(*) as total FROM sessions {where_clause}", tuple(params)
            )
            total = dict(count_cursor.fetchone())["total"]

            query = f"""SELECT session_id, file_path, status, quality_auto_score,
                               quality_manual_score, agent_role, task_type, tools_used,
                               tags, created_at, updated_at
                        FROM sessions {where_clause}
                        ORDER BY created_at {sort_order}, session_id {sort_order}
                        LIMIT ? OFFSET ?"""
            params.extend([page_size, offset])

            cursor_res = conn.execute(query, tuple(params))
            rows = cursor_res.fetchall()

            sessions = []
            for row in rows:
                session = self._row_to_dict(row)
                session = self._deserialize_session_fields(session)
                sessions.append(session)

            has_more = (offset + len(sessions)) < total
            next_cursor = None
            if sessions and has_more:
                last_session = sessions[-1]
                next_cursor = encode_cursor(last_session.get("created_at", ""), last_session.get("session_id", ""))

            return {
                "sessions": sessions,
                "total": total,
                "page": page,
                "page_size": page_size,
                "next_cursor": next_cursor,
                "has_more": has_more,
            }

    def session_update(self, session_id: str, updates: Dict) -> Optional[Dict]:
        """更新会话"""
        self._ensure()

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
        self._write(query, tuple(params))

        return self.session_get(session_id)

    def session_delete(self, session_id: str) -> bool:
        """删除会话记录

        Args:
            session_id: 会话 ID

        Returns:
            记录是否被删除（不存在返回 False）
        """
        cursor = self._write(
            "DELETE FROM sessions WHERE session_id = ?", (session_id,)
        )
        return cursor.rowcount > 0

    def session_get_by_status(self, status: str) -> List[Dict]:
        """按状态获取会话"""
        self._ensure()

        with self._pool.reader() as conn:
            cursor = conn.execute(
                "SELECT session_id FROM sessions WHERE status = ?", (status,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def audit_log_create(self, session_id: str, action: str, operator: str = "system", details: str = None) -> None:
        """创建审计日志"""
        self._write(
            "INSERT INTO audit_logs (session_id, action, operator, details) VALUES (?, ?, ?, ?)",
            (session_id, action, operator, details)
        )

    def audit_log_get(self, session_id: str = None, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        self._ensure()

        limit = self._clamp_limit(limit, 100)

        with self._pool.reader() as conn:
            if session_id:
                cursor = conn.execute(
                    "SELECT * FROM audit_logs WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                    (session_id, limit)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def session_review_apply(self, session_id: str, status: str, score: int, action: str,
                             notes: str = None, review_meta: Dict = None) -> Optional[Dict]:
        """原子性地更新状态+评分（可选扩展字段）并创建审计日志"""
        self._ensure()

        with self._pool.writer() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if review_meta is not None:
                    conn.execute(
                        "UPDATE sessions SET status = ?, quality_manual_score = ?, review_meta = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                        (status, score, json.dumps(review_meta, ensure_ascii=False), session_id)
                    )
                else:
                    conn.execute(
                        "UPDATE sessions SET status = ?, quality_manual_score = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                        (status, score, session_id)
                    )
                conn.execute(
                    "INSERT INTO audit_logs (session_id, action, operator, details) VALUES (?, ?, 'user', ?)",
                    (session_id, action, notes)
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return self.session_get(session_id)

    def export_record_create(
        self,
        export_format: str,
        file_path: str,
        filters: Dict,
        record_count: int,
        version: str
    ) -> None:
        """创建导出记录"""
        self._write(
            """INSERT INTO export_records
               (export_format, file_path, filters, record_count, version)
               VALUES (?, ?, ?, ?, ?)""",
            (export_format, file_path, json.dumps(filters), record_count, version)
        )

    def export_record_get_history(self, limit: int = 20) -> List[Dict]:
        """获取导出历史"""
        self._ensure()

        limit = self._clamp_limit(limit, DEFAULT_HISTORY_LIMIT)

        with self._pool.reader() as conn:
            cursor = conn.execute(
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
        self._ensure()

        query = "SELECT * FROM sessions WHERE status = ?"
        params = [SessionStatus.APPROVED.value]

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

        with self._pool.reader() as conn:
            cursor = conn.execute(query, tuple(params))
            sessions = [self._deserialize_session_fields(self._row_to_dict(row)) for row in cursor.fetchall()]
        return sessions

    def stats_get(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        self._ensure()

        with self._pool.reader() as conn:
            status_counts = conn.execute(
                "SELECT status, COUNT(*) AS c FROM sessions GROUP BY status"
            ).fetchall()
            avg_row = conn.execute(
                "SELECT AVG(quality_auto_score) AS avg_score FROM sessions WHERE quality_auto_score IS NOT NULL"
            ).fetchone()

        counts = {row["status"]: row["c"] for row in status_counts}
        raw = counts.get(SessionStatus.RAW.value, 0)
        approved = counts.get(SessionStatus.APPROVED.value, 0)
        rejected = counts.get(SessionStatus.REJECTED.value, 0)
        curated = counts.get(SessionStatus.CURATED.value, 0)
        total = sum(counts.values())

        avg_score = avg_row["avg_score"] if avg_row and avg_row["avg_score"] else 0
        return {
            "total_sessions": total,
            "raw_sessions": raw,
            "approved_sessions": approved,
            "rejected_sessions": rejected,
            "curated_sessions": curated,
            "reviewed_sessions": approved + rejected,
            "avg_auto_score": round(avg_score, 1) if avg_score else 0,
        }

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将 Row 转换为字典"""
        return dict(row)

    def _clamp_limit(self, limit: Optional[int], default: int,
                     max_value: int = MAX_PAGE_SIZE) -> int:
        """将 limit 限制在 [1, max_value]，None 使用 default"""
        if limit is None:
            return default
        return max(1, min(limit, max_value))

    def _deserialize_json_field(self, data: Dict, key: str) -> None:
        """就地反序列化指定 JSON 字段，失败保留原值并记 warning"""
        raw = data.get(key)
        if not raw:
            return
        try:
            data[key] = json.loads(raw)
        except json.JSONDecodeError as e:
            self.logger.warning(f"字段 {key} JSON 反序列化失败: {e}")

    def _deserialize_session_fields(self, session: Dict) -> Dict:
        """反序列化会话的 JSON 字段"""
        for key in ("tags", "tools_used", "content", "review_meta"):
            self._deserialize_json_field(session, key)
        return session


database_manager = DatabaseManager()
