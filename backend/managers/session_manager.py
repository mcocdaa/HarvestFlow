# @file backend/managers/session_manager.py
# @brief 会话管理器
# @create 2026-03-18

import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.database import get_database
from config import RAW_SESSIONS_DIR, AGENT_CURATED_DIR, HUMAN_APPROVED_DIR


class SessionManager:
    def __init__(self):
        self.db = None

    def get_db(self):
        if not self.db:
            self.db = get_database()
        return self.db

    def create_session(self, session_data: Dict) -> Dict:
        db = self.get_db()
        session_id = session_data.get("session_id")
        file_path = session_data.get("file_path", "")

        db.execute(
            """INSERT INTO sessions (session_id, file_path, status, agent_role, task_type, tools_used, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                file_path,
                session_data.get("status", "raw"),
                session_data.get("agent_role"),
                session_data.get("task_type"),
                json.dumps(session_data.get("tools_used", [])),
                json.dumps(session_data.get("tags", [])),
            )
        )
        return session_data

    def get_session(self, session_id: str) -> Optional[Dict]:
        db = self.get_db()
        row = db.fetchone("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        if row:
            return dict(row)
        return None

    def get_sessions(
        self,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "recent"
    ) -> Dict:
        db = self.get_db()

        where_clause = ""
        params = []
        if status:
            where_clause = "WHERE status = ?"
            params = [status]

        sort_order = "DESC" if sort == "recent" else "ASC"
        offset = (page - 1) * page_size

        count_query = f"SELECT COUNT(*) as total FROM sessions {where_clause}"
        total_result = db.fetchone(count_query, tuple(params))
        total = dict(total_result)["total"] if total_result else 0

        query = f"""SELECT * FROM sessions {where_clause}
                    ORDER BY created_at {sort_order}
                    LIMIT ? OFFSET ?"""
        params.extend([page_size, offset])

        rows = db.fetchall(query, tuple(params))
        sessions = [dict(row) for row in rows]

        for session in sessions:
            if session.get("tags"):
                session["tags"] = json.loads(session["tags"])
            if session.get("tools_used"):
                session["tools_used"] = json.loads(session["tools_used"])

        return {
            "sessions": sessions,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def update_session(self, session_id: str, updates: Dict) -> Optional[Dict]:
        db = self.get_db()

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
        db.execute(query, tuple(params))

        return self.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        db = self.get_db()
        session = self.get_session(session_id)
        if not session:
            return False

        if session.get("file_path") and os.path.exists(session["file_path"]):
            try:
                os.remove(session["file_path"])
            except Exception:
                pass

        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        return True

    def get_session_content(self, session_id: str) -> Optional[Dict]:
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
