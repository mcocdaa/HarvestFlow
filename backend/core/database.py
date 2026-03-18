# @file backend/core/database.py
# @brief SQLite 数据库连接管理
# @create 2026-03-18

import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from config import DB_PATH


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._ensure_db_dir()
        self._init_connection()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _init_connection(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

    @contextmanager
    def get_cursor(self):
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def execute(self, query: str, params: tuple = None):
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor

    def execute_many(self, query: str, params_list: list):
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor

    def fetchone(self, query: str, params: tuple = None):
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = None):
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()

    def initialize_tables(self):
        with self.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'raw',
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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS export_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    export_format TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    filters TEXT,
                    record_count INTEGER NOT NULL,
                    version TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    plugin_type TEXT NOT NULL,
                    is_enabled INTEGER NOT NULL DEFAULT 1,
                    config TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id)")


_db_instance: Optional[Database] = None


def get_database() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def close_database():
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
