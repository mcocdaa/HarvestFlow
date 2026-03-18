# @file backend/managers/reviewer_manager.py
# @brief 人工审核管理器
# @create 2026-03-18

import json
import os
import shutil
from typing import Dict, Optional, List
from datetime import datetime
from core.database import get_database
from config import HUMAN_APPROVED_DIR
from managers.session_manager import session_manager


class ReviewerManager:
    def __init__(self):
        self.db = None

    def get_db(self):
        if not self.db:
            self.db = get_database()
        return self.db

    def approve_session(self, session_id: str, notes: str = None) -> Optional[Dict]:
        session = session_manager.get_session(session_id)
        if not session:
            return None

        current_status = session.get("status")

        if current_status == "curated" or current_status == "raw":
            source_path = session.get("file_path")
            if source_path and os.path.exists(source_path):
                dest_path = os.path.join(HUMAN_APPROVED_DIR, f"{session_id}.json")
                try:
                    shutil.copy2(source_path, dest_path)
                    session_manager.update_session(session_id, {
                        "file_path": dest_path,
                        "status": "approved"
                    })
                except Exception as e:
                    print(f"[ReviewerManager] 复制文件失败: {e}")
                    return None
        else:
            session_manager.update_session(session_id, {"status": "approved"})

        self._log_action(session_id, "approve", "user", notes)

        return session_manager.get_session(session_id)

    def reject_session(self, session_id: str, notes: str = None) -> Optional[Dict]:
        session = session_manager.get_session(session_id)
        if not session:
            return None

        session_manager.update_session(session_id, {"status": "rejected"})
        self._log_action(session_id, "reject", "user", notes)

        return session_manager.get_session(session_id)

    def update_session(self, session_id: str, updates: Dict) -> Optional[Dict]:
        session = session_manager.get_session(session_id)
        if not session:
            return None

        session_manager.update_session(session_id, updates)
        self._log_action(session_id, "modify", "user", json.dumps(updates))

        return session_manager.get_session(session_id)

    def batch_approve(self, session_ids: List[str]) -> Dict:
        results = []
        for session_id in session_ids:
            result = self.approve_session(session_id)
            results.append({
                "session_id": session_id,
                "success": result is not None
            })

        return {
            "total": len(session_ids),
            "success": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results,
        }

    def batch_reject(self, session_ids: List[str]) -> Dict:
        results = []
        for session_id in session_ids:
            result = self.reject_session(session_id)
            results.append({
                "session_id": session_id,
                "success": result is not None
            })

        return {
            "total": len(session_ids),
            "success": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results,
        }

    def get_pending_sessions(self, page: int = 1, page_size: int = 20) -> Dict:
        return session_manager.get_sessions(status="curated", page=page, page_size=page_size)

    def _log_action(self, session_id: str, action: str, operator: str, details: str = None):
        db = self.get_db()
        db.execute(
            "INSERT INTO audit_logs (session_id, action, operator, details) VALUES (?, ?, ?, ?)",
            (session_id, action, operator, details)
        )

    def get_audit_logs(self, session_id: str = None) -> List[Dict]:
        db = self.get_db()

        if session_id:
            rows = db.fetchall(
                "SELECT * FROM audit_logs WHERE session_id = ? ORDER BY created_at DESC",
                (session_id,)
            )
        else:
            rows = db.fetchall("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100")

        return [dict(row) for row in rows]


reviewer_manager = ReviewerManager()
