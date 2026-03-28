# @file backend/managers/exporter_manager.py
# @brief 导出管理器 - 导出会话为多种格式
# @create 2026-03-18

import json
import os
import logging
from typing import Dict, List
from datetime import datetime
import argparse

from core import database_manager, setting_manager, hook_manager
from managers.session_manager import session_manager


DEFAULT_FORMAT = "sharegpt"
FORMAT_SHAREGPT = "sharegpt"
FORMAT_ALPACA = "alpaca"
DEFAULT_VERSION = "v1"
DEFAULT_HISTORY_LIMIT = 20
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_GPT = "gpt"
ROLE_SYSTEM = "system"


class ExporterManager:
    """导出管理器

    职责：
    1. 导出会话为指定格式（sharegpt, alpaca）
    2. 支持多种过滤条件
    3. 记录导出历史

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args) 初始化
    """

    @hook_manager.wrap_hooks("exporter_manager_construct_before", "exporter_manager_construct_after")
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_format: str = DEFAULT_FORMAT
        self.output_dir: str = os.path.join(setting_manager.get("DATA_DIR", "./data"), "export")

    @hook_manager.wrap_hooks(after="exporter_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_argument_group("Exporter", "Exporter Settings")
        group.add_argument(
            "--export-default-format",
            type=str,
            default=DEFAULT_FORMAT,
            choices=[FORMAT_SHAREGPT, FORMAT_ALPACA],
            help=f"默认导出格式 (默认: {DEFAULT_FORMAT})"
        )
        group.add_argument(
            "--export-output-dir",
            type=str,
            default=None,
            help="导出输出目录"
        )

    @hook_manager.wrap_hooks("exporter_manager_init_before", "exporter_manager_init_after")
    def init(self, args: argparse.Namespace):
        self.default_format = getattr(args, 'export_default_format', setting_manager.get("EXPORT_DEFAULT_FORMAT", DEFAULT_FORMAT))

        export_output_dir_val = getattr(args, 'export_output_dir', setting_manager.get("EXPORT_OUTPUT_DIR"))
        if export_output_dir_val:
            self.output_dir = export_output_dir_val

    @property
    def default_output_dir(self) -> str:
        return os.path.join(setting_manager.get("DATA_DIR", "./data"), "export")

    @hook_manager.wrap_hooks("exporter_manager_export_before", "exporter_manager_export_after")
    def export(
        self,
        format: str = None,
        min_score: int = None,
        agent_role: str = None,
        task_type: str = None,
        tags: List[str] = None,
        version: str = DEFAULT_VERSION
    ) -> Dict:
        """导出会话"""
        if format is None:
            format = self.default_format

        filters = {
            "min_score": min_score,
            "agent_role": agent_role,
            "task_type": task_type,
            "tags": tags,
        }

        sessions = database_manager.session_get_for_export(
            min_score=min_score,
            agent_role=agent_role,
            task_type=task_type,
            tags=tags
        )

        if not sessions:
            return {
                "success": False,
                "message": "No sessions found with the given filters",
                "record_count": 0,
            }

        for session in sessions:
            content = session_manager.get_session_content(session["session_id"])
            if content:
                session["content"] = content

        if format == FORMAT_SHAREGPT:
            data = self._convert_to_sharegpt(sessions)
        elif format == FORMAT_ALPACA:
            data = self._convert_to_alpaca(sessions)
        else:
            return {
                "success": False,
                "message": f"Unsupported format: {format}",
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{format}_{timestamp}_{version}.jsonl"
        file_path = os.path.join(self.output_dir, filename)

        os.makedirs(self.output_dir, exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to write file: {str(e)}",
            }

        database_manager.export_record_create(
            export_format=format,
            file_path=file_path,
            filters=filters,
            record_count=len(data),
            version=version
        )

        return {
            "success": True,
            "file_path": file_path,
            "filename": filename,
            "record_count": len(data),
            "format": format,
            "version": version,
        }

    def _convert_to_sharegpt(self, sessions: List[Dict]) -> List[Dict]:
        """转换为 ShareGPT 格式"""
        result = []
        for session in sessions:
            content = session.get("content", {})

            messages = content.get("messages", [])
            if not messages:
                continue

            conversations = []
            for msg in messages:
                role = msg.get("role", ROLE_USER)
                if role == ROLE_ASSISTANT:
                    role = ROLE_GPT

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
        """转换为 Alpaca 格式"""
        result = []
        for session in sessions:
            content = session.get("content", {})

            messages = content.get("messages", [])
            if not messages:
                continue

            instruction = ""
            input_text = ""
            output_text = ""

            for msg in messages:
                role = msg.get("role", "")
                msg_content = msg.get("content", "")
                if isinstance(msg_content, list):
                    msg_content = str(msg_content)

                if role == ROLE_SYSTEM:
                    instruction = msg_content
                elif role == ROLE_USER and not input_text:
                    input_text = msg_content
                elif role == ROLE_ASSISTANT:
                    output_text = msg_content

            if output_text:
                result.append({
                    "instruction": instruction or input_text,
                    "input": input_text if instruction else "",
                    "output": output_text,
                })

        return result

    @hook_manager.wrap_hooks("exporter_manager_get_history_before", "exporter_manager_get_history_after")
    def get_export_history(self, limit: int = DEFAULT_HISTORY_LIMIT) -> List[Dict]:
        """获取导出历史"""
        return database_manager.export_record_get_history(limit=limit)


exporter_manager = ExporterManager()
