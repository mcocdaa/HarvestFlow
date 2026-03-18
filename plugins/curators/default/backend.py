# @file plugins/curators/default/backend.py
# @brief 默认审核器插件
# @create 2026-03-18

from typing import Dict, List


class DefaultCurator:
    name = "default"
    description = "Default curator - passes all sessions without filtering"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.auto_approve_threshold = self.config.get("auto_approve_threshold", 4)

    def evaluate(self, session: Dict) -> Dict:
        score = self._calculate_score(session)

        return {
            "score": score,
            "is_high_value": True,
            "tags": self._extract_tags(session),
            "notes": "Default curator - passed all sessions",
        }

    def _calculate_score(self, session: Dict) -> int:
        score = 3

        if session.get("messages"):
            msg_count = len(session.get("messages", []))
            if msg_count > 10:
                score += 1
            if msg_count > 20:
                score += 1

        if session.get("tool_calls"):
            score += 1

        if session.get("final_output") or session.get("result"):
            score += 1

        return min(score, 5)

    def _extract_tags(self, session: Dict) -> List[str]:
        tags = []

        if session.get("task_type"):
            tags.append(session.get("task_type"))

        if session.get("agent_role"):
            tags.append(session.get("agent_role"))

        return list(set(tags))


curator_plugin = DefaultCurator()


def on_load():
    print("[DefaultCurator] Plugin loaded")


def get_curator():
    return curator_plugin
