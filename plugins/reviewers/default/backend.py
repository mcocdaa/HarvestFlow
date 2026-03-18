# @file plugins/reviewers/default/backend.py
# @brief 默认人工审核插件
# @create 2026-03-18

from typing import Dict, List


class DefaultReviewer:
    name = "default"
    description = "Default human reviewer - basic review interface"

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def get_extra_fields(self) -> List[Dict]:
        return [
            {
                "name": "quality_notes",
                "label": "Quality Notes",
                "type": "textarea",
                "required": False,
            },
            {
                "name": "reviewer_tags",
                "label": "Reviewer Tags",
                "type": "tags",
                "required": False,
            },
        ]

    def validate(self, session: Dict) -> bool:
        if not session.get("messages"):
            return False
        return True


reviewer_plugin = DefaultReviewer()


def on_load():
    print("[DefaultReviewer] Plugin loaded")


def get_reviewer():
    return reviewer_plugin
