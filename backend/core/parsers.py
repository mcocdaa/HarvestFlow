# @file backend/core/parsers.py
# @brief 会话文件解析器 - jsonl 与 json 通用解析
# @create 2026-08-10

import json
import logging
import os
from typing import Dict, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_jsonl_file(file_path: str) -> Optional[Dict]:
    """解析 jsonl 会话文件

    逐行读取，type == "message" 的行提取 role 与文本内容；
    session_id 取第一个带 id 的行；agent_id 从文件路径 "agents" 段之后提取。

    Args:
        file_path: jsonl 文件路径

    Returns:
        解析后的会话数据，格式：
        {"session_id", "agent_id", "messages", "message_count",
         "has_tool_calls", "tools_used"}
        解析失败或无有效内容返回 None
    """
    try:
        messages = []
        session_id = None
        agent_id = None

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    msg_type = msg.get('type', '')
                    if msg_type == 'message':
                        message_data = msg.get('message', {})
                        role = message_data.get('role', 'user')
                        content_list = message_data.get('content', [])

                        # 提取文本内容
                        text_content = ""
                        if isinstance(content_list, list):
                            for item in content_list:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text_content += item.get('text', '')
                        elif isinstance(content_list, str):
                            text_content = content_list

                        if text_content:
                            messages.append({
                                "role": role,
                                "content": text_content
                            })

                    # 提取 session_id
                    if not session_id and msg.get('id'):
                        session_id = msg.get('id')

                except json.JSONDecodeError:
                    continue

        if messages and session_id:
            # 从文件路径提取 agent_id
            parts = file_path.split(os.sep)
            if 'agents' in parts:
                idx = parts.index('agents')
                if idx + 1 < len(parts):
                    agent_id = parts[idx + 1]

            return {
                "session_id": session_id,
                "agent_id": agent_id,
                "messages": messages,
                "message_count": len(messages),
                "has_tool_calls": False,
                "tools_used": [],
            }

        return None
    except Exception as e:
        logger.error(f"解析文件失败 {file_path}: {e}")
        return None


def parse_json_file(file_path: str) -> Optional[Dict]:
    """解析普通 json 会话文件

    返回原字典；缺少 session_id 时生成
    "session_{YYYYmmdd_HHMMSS}_{basename}" 并写回 data["session_id"]。

    Args:
        file_path: json 文件路径

    Returns:
        会话数据字典，解析失败返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        session_id = data.get("session_id")
        if not session_id:
            session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{Path(file_path).name}"
            data["session_id"] = session_id

        return data
    except Exception as e:
        logger.error(f"解析文件失败 {file_path}: {e}")
        return None
