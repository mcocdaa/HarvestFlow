# @file backend/managers/exporter_manager.py
# @brief 导出管理器
# @create 2026-03-18

import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from core.database import get_database
from config import EXPORT_DIR, HUMAN_APPROVED_DIR, EXPORT_CONFIG
from managers.session_manager import session_manager


class ExporterManager:
    def __init__(self):
        self.db = None
        self.default_format = EXPORT_CONFIG.get("default_format", "sharegpt")
        self.output_dir = EXPORT_CONFIG.get("output_dir", EXPORT_DIR)

    def get_db(self):
        if not self.db:
            self.db = get_database()
        return self.db

    def export(
        self,
        format: str = None,
        min_score: int = None,
        agent_role: str = None,
        task_type: str = None,
        tags: List[str] = None,
        version: str = "v1"
    ) -> Optional[Dict]:
        if format is None:
            format = self.default_format

        filters = {
            "min_score": min_score,
            "agent_role": agent_role,
            "task_type": task_type,
            "tags": tags,
        }

        sessions = self._get_sessions_for_export(min_score, agent_role, task_type, tags)

        if not sessions:
            return {
                "success": False,
                "message": "No sessions found with the given filters",
                "record_count": 0,
            }

        if format == "sharegpt":
            data = self._convert_to_sharegpt(sessions)
        elif format == "alpaca":
            data = self._convert_to_alpaca(sessions)
        else:
            return {
                "success": False,
                "message": f"Unsupported format: {format}",
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{format}_{timestamp}_{version}.jsonl"
        file_path = os.path.join(self.output_dir, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to write file: {str(e)}",
            }

        self._save_export_record(format, file_path, filters, len(data), version)

        return {
            "success": True,
            "file_path": file_path,
            "filename": filename,
            "record_count": len(data),
            "format": format,
            "version": version,
        }

    def _get_sessions_for_export(
        self,
        min_score: int = None,
        agent_role: str = None,
        task_type: str = None,
        tags: List[str] = None
    ) -> List[Dict]:
        db = self.get_db()

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

        rows = db.fetchall(query, tuple(params))
        sessions = []

        for row in rows:
            session = dict(row)
            content = session_manager.get_session_content(session["session_id"])
            if content:
                session["content"] = content

            if tags:
                session_tags = json.loads(session.get("tags", "[]")) if session.get("tags") else []
                if not any(tag in session_tags for tag in tags):
                    continue

            sessions.append(session)

        return sessions

    def _convert_to_sharegpt(self, sessions: List[Dict]) -> List[Dict]:
        result = []
        for session in sessions:
            content = session.get("content", {})

            messages = content.get("messages", [])
            if not messages:
                continue

            conversations = []
            for msg in messages:
                role = msg.get("role", "user")
                if role == "assistant":
                    role = "gpt"

                content_text = msg.get("content", "")
                if isinstance(content_text, list):
                    content_text = str(content_text)

                conversations.append({
                    "from": role,
                    "value": content_text,
                })

            result.append({
                "conversations": conversations,
                "system": content.get("system_prompt", ""),
                "tools": content.get("tools", []),
            })

        return result

    def _convert_to_alpaca(self, sessions: List[Dict]) -> List[Dict]:
        result = []
        for session in sessions:
            content = session.get("content", {})

            messages = content.get("messages", [])
            if not messages:
                continue

            instruction = ""
            input_text = ""
            output_text = ""

            for i, msg in enumerate(messages):
                role = msg.get("role", "")
                msg_content = msg.get("content", "")
                if isinstance(msg_content, list):
                    msg_content = str(msg_content)

                if role == "system":
                    instruction = msg_content
                elif role == "user" and not input_text:
                    input_text = msg_content
                elif role == "assistant":
                    output_text = msg_content

            if output_text:
                result.append({
                    "instruction": instruction or input_text,
                    "input": input_text if instruction else "",
                    "output": output_text,
                })

        return result

    def _save_export_record(
        self,
        export_format: str,
        file_path: str,
        filters: Dict,
        record_count: int,
        version: str
    ):
        db = self.get_db()
        db.execute(
            """INSERT INTO export_records
               (export_format, file_path, filters, record_count, version)
               VALUES (?, ?, ?, ?, ?)""",
            (export_format, file_path, json.dumps(filters), record_count, version)
        )

    def get_export_history(self, limit: int = 20) -> List[Dict]:
        db = self.get_db()
        rows = db.fetchall(
            "SELECT * FROM export_records ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in rows]


exporter_manager = ExporterManager()
