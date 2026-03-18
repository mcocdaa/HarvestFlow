# @file backend/managers/curator_manager.py
# @brief 自动审核管理器
# @create 2026-03-18

import json
import os
import shutil
from typing import Dict, Optional, List
from datetime import datetime
from core.database import get_database
from config import AGENT_CURATED_DIR, CURATOR_CONFIG
from managers.session_manager import session_manager


class CuratorManager:
    def __init__(self):
        self.db = None
        self.enabled = CURATOR_CONFIG.get("default_enabled", True)
        self.auto_approve_threshold = CURATOR_CONFIG.get("auto_approve_threshold", 4)

    def get_db(self):
        if not self.db:
            self.db = get_database()
        return self.db

    def evaluate_session(self, session_id: str) -> Optional[Dict]:
        session = session_manager.get_session(session_id)
        if not session:
            return None

        content = session_manager.get_session_content(session_id)
        if not content:
            return None

        score = self._calculate_score(content)
        is_high_value = score >= self.auto_approve_threshold

        tags = self._extract_tags(content)
        tools_used = self._extract_tools(content)

        updates = {
            "quality_auto_score": score,
            "tags": tags,
            "tools_used": tools_used,
        }

        session_manager.update_session(session_id, updates)

        result = {
            "session_id": session_id,
            "score": score,
            "is_high_value": is_high_value,
            "tags": tags,
            "tools_used": tools_used,
        }

        if is_high_value:
            self._move_to_curated(session_id)

        return result

    def _calculate_score(self, content: Dict) -> int:
        score = 3

        if content.get("messages"):
            message_count = len(content.get("messages", []))
            if message_count > 10:
                score += 1
            if message_count > 20:
                score += 1

        if content.get("tool_calls") or content.get("tools_used"):
            score += 1

        if content.get("final_output") or content.get("result"):
            score += 1

        return min(score, 5)

    def _extract_tags(self, content: Dict) -> List[str]:
        tags = []

        if content.get("task_type"):
            tags.append(content.get("task_type"))

        if content.get("agent_role"):
            tags.append(content.get("agent_role"))

        if content.get("tool_calls"):
            for tool_call in content.get("tool_calls", []):
                if isinstance(tool_call, dict) and tool_call.get("name"):
                    tags.append(tool_call.get("name"))

        return list(set(tags))

    def _extract_tools(self, content: Dict) -> List[str]:
        tools = []

        if content.get("tools_used"):
            tools.extend(content.get("tools_used", []))

        if content.get("tool_calls"):
            for tool_call in content.get("tool_calls", []):
                if isinstance(tool_call, dict) and tool_call.get("name"):
                    tools.append(tool_call.get("name"))

        return list(set(tools))

    def _move_to_curated(self, session_id: str):
        session = session_manager.get_session(session_id)
        if not session:
            return

        source_path = session.get("file_path")
        if not source_path or not os.path.exists(source_path):
            return

        dest_path = os.path.join(AGENT_CURATED_DIR, f"{session_id}.json")

        try:
            shutil.copy2(source_path, dest_path)
            session_manager.update_session(session_id, {
                "file_path": dest_path,
                "status": "curated"
            })
        except Exception as e:
            print(f"[CuratorManager] 移动文件失败: {e}")

    def evaluate_all(self) -> Dict:
        db = self.get_db()
        rows = db.fetchall("SELECT session_id FROM sessions WHERE status = 'raw'")

        results = []
        for row in rows:
            session_id = row["session_id"]
            result = self.evaluate_session(session_id)
            if result:
                results.append(result)

        return {
            "total": len(results),
            "high_value": len([r for r in results if r["is_high_value"]]),
            "low_value": len([r for r in results if not r["is_high_value"]]),
            "results": results,
        }


curator_manager = CuratorManager()
