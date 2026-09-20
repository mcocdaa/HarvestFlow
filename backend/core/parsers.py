# @file backend/core/parsers.py
# @brief 会话文件解析与多格式互通解析器 (支持 OpenAI Messages, ShareGPT, Alpaca, HarvestFlow)
# @create 2026-08-10

import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_json_file(file_path: str) -> Optional[Dict]:
    """解析普通 json 会话文件

    返回原字典；缺少 session_id 时生成
    "session_{YYYYmmdd_HHMMSS}_{basename}" 并写回 data["session_id"]。

    Args:
        file_path: json 文件路径

    Returns:
        会话数据字典，解析失败返回 None

    Note:
        .jsonl 文件的解析由采集器插件负责（如 openclaw 采集器经
        collector_manager_parse_before 钩子接入），核心层不再内置。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        session_id = data.get("session_id")
        if not session_id:
            session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{Path(file_path).name}"
            data["session_id"] = session_id

        # 兼容 ShareGPT 格式
        if "conversations" in data and "messages" not in data:
            data["messages"] = [
                {
                    "role": "user" if str(t.get("from", "")).lower() in ("human", "user") else "assistant",
                    "content": t.get("value", "")
                }
                for t in data["conversations"]
            ]
            if "system" in data and "system_prompt" not in data:
                data["system_prompt"] = data["system"]

        # 兼容 Alpaca 格式
        if "instruction" in data and "messages" not in data:
            inp = data.get("input", "")
            user_content = f"{data['instruction']}\n\n{inp}".strip() if inp else data["instruction"]
            data["messages"] = [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": data.get("output", "")}
            ]

        return data
    except Exception as e:
        logger.error(f"解析文件失败 {file_path}: {e}")
        return None


def normalize_to_session_record(data: Dict[str, Any], default_name: str = "") -> Optional[Dict[str, Any]]:
    """将多种异构格式统一规整为 HarvestFlow 标准会话字典"""
    if not isinstance(data, dict):
        return None

    session_id = data.get("session_id")
    if not session_id:
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')[:19]
        safe_name = Path(default_name).stem if default_name else "import"
        session_id = f"session_{timestamp}_{safe_name}"

    # 1. 检查是否为原生 HarvestFlow 格式
    if "content" in data and isinstance(data["content"], dict) and "messages" in data["content"]:
        record = dict(data)
        record["session_id"] = session_id
        record["status"] = data.get("status", "raw")
        return record

    # 2. 检查是否为包含 messages 键的对象 (如 OpenAI Messages)
    if "messages" in data and isinstance(data["messages"], list):
        messages = data["messages"]
        system_prompt = data.get("system_prompt", "")
        if not system_prompt and messages and messages[0].get("role") == "system":
            system_prompt = messages[0].get("content", "")

        return {
            "session_id": session_id,
            "status": "raw",
            "agent_role": data.get("agent_role", "assistant"),
            "task_type": data.get("task_type", "chat"),
            "tools_used": data.get("tools_used", []),
            "tags": data.get("tags", ["openai"]),
            "content": {
                "messages": messages,
                "system_prompt": system_prompt,
                "tools": data.get("tools", []),
            }
        }

    # 3. 检查是否为 ShareGPT 格式
    if "conversations" in data and isinstance(data["conversations"], list):
        converted_messages = []
        for turn in data["conversations"]:
            sender = str(turn.get("from", "")).lower()
            val = turn.get("value", "")

            if sender in ("human", "user"):
                role = "user"
            elif sender in ("gpt", "assistant", "chatgpt", "bot"):
                role = "assistant"
            elif sender in ("system",):
                role = "system"
            else:
                role = "user"

            converted_messages.append({"role": role, "content": val})

        system_prompt = data.get("system", "")
        return {
            "session_id": session_id,
            "status": "raw",
            "agent_role": "gpt",
            "task_type": "chat",
            "tools_used": data.get("tools", []),
            "tags": data.get("tags", ["sharegpt"]),
            "content": {
                "messages": converted_messages,
                "system_prompt": system_prompt,
                "tools": data.get("tools", []),
            }
        }

    # 4. 检查是否为 Alpaca 格式
    if "instruction" in data:
        instruction = data.get("instruction", "")
        input_text = data.get("input", "")
        output_text = data.get("output", "")
        system_text = data.get("system", "")

        user_content = f"{instruction}\n\n{input_text}".strip() if input_text else instruction
        messages = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output_text}
        ]

        return {
            "session_id": session_id,
            "status": "raw",
            "agent_role": "assistant",
            "task_type": "instruction",
            "tools_used": [],
            "tags": data.get("tags", ["alpaca"]),
            "content": {
                "messages": messages,
                "system_prompt": system_text,
                "tools": [],
            }
        }

    return data


def parse_multiformat_content(content_str: str, source_name: str = "import") -> List[Dict[str, Any]]:
    """解析字符串内容，支持 JSON 数组、单对象或 JSONL 流式行"""
    records = []
    content_str = content_str.strip()
    if not content_str:
        return []

    try:
        parsed = json.loads(content_str)
        if isinstance(parsed, list):
            for i, item in enumerate(parsed):
                if isinstance(item, dict):
                    norm = normalize_to_session_record(item, default_name=f"{source_name}_{i}")
                    if norm:
                        records.append(norm)
            return records
        elif isinstance(parsed, dict):
            norm = normalize_to_session_record(parsed, default_name=source_name)
            if norm:
                return [norm]
    except json.JSONDecodeError:
        pass

    for i, line in enumerate(content_str.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                norm = normalize_to_session_record(item, default_name=f"{source_name}_{i}")
                if norm:
                    records.append(norm)
        except Exception:
            continue

    return records
