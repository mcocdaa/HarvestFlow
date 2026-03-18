# @file plugins/collectors/openclaw/backend.py
# @brief OpenClaw 会话采集器插件
# @create 2026-03-18

import os
import json
from typing import List, Dict, Optional
from pathlib import Path


class OpenClawCollector:
    name = "openclaw"
    description = "OpenClaw Agent session collector - reads from local OpenClaw session files"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.agents_dir = self.config.get("agents_dir", "C:/Users/20211/.openclaw/agents")
        self.target_agents = self.config.get("target_agents", ["backend_dev", "req_analyst", "qa_ops", "coord"])
        self.skip_cron = self.config.get("skip_cron_sessions", True)
        self.min_message_count = self.config.get("min_message_count", 5)

    def scan(self) -> List[str]:
        """扫描所有目标 agent 的 sessions.json，返回 jsonl 文件路径列表"""
        jsonl_files = []

        if not os.path.exists(self.agents_dir):
            print(f"[OpenClawCollector] agents_dir not found: {self.agents_dir}")
            return jsonl_files

        for agent_id in self.target_agents:
            agent_sessions_path = os.path.join(self.agents_dir, agent_id, "sessions", "sessions.json")
            if not os.path.exists(agent_sessions_path):
                continue

            try:
                with open(agent_sessions_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sessions_data = json.load(f)

                for session_key, session_info in sessions_data.items():
                    # 跳过 cron 会话
                    if self.skip_cron and ":cron:" in session_key:
                        continue

                    session_file = session_info.get("sessionFile")
                    if session_file:
                        # sessionFile 存的是完整绝对路径
                        if os.path.exists(session_file):
                            jsonl_files.append(session_file)
            except Exception as e:
                print(f"[OpenClawCollector] Error scanning {agent_id}: {e}")

        return jsonl_files

    def parse(self, file_path: str) -> Optional[Dict]:
        """读取 jsonl 文件，解析为标准格式"""
        try:
            messages = []
            tools_used = set()
            has_tool_calls = False
            session_id = None
            session_key = None
            agent_id = None

            # 从路径中提取 agent_id
            parts = file_path.split(os.sep)
            if "agents" in parts:
                idx = parts.index("agents")
                if idx + 1 < len(parts):
                    agent_id = parts[idx + 1]

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    role = msg.get("role", "user")
                    content = msg.get("content", "")

                    # 处理 content 为数组的情况
                    parsed_content = self._parse_content(content)

                    # 提取 tool_use 和 tool_result
                    tool_calls = []
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                item_type = item.get("type", "")
                                if item_type == "tool_use":
                                    has_tool_calls = True
                                    tool_name = item.get("name", "")
                                    if tool_name:
                                        tools_used.add(tool_name)
                                    tool_calls.append(item)
                                elif item_type == "tool_result":
                                    tool_calls.append(item)

                    messages.append({
                        "role": role,
                        "content": parsed_content,
                        "tool_calls": tool_calls if tool_calls else None,
                    })

                    # 从第一条消息获取 session_id
                    if not session_id:
                        session_id = msg.get("sessionId")

            # 从文件路径推断 session_key
            if agent_id and session_id:
                session_key = f"agent:{agent_id}:{session_id[:8]}"

            # 提取元数据（从最后一条 assistant 消息）
            metadata = self._extract_metadata(file_path, agent_id)

            # 过滤消息数
            if len(messages) < self.min_message_count:
                return None

            return {
                "session_id": session_id or os.path.splitext(os.path.basename(file_path))[0],
                "agent_id": agent_id,
                "session_key": session_key,
                "messages": messages,
                "metadata": metadata,
                "tools_used": list(tools_used),
                "has_tool_calls": has_tool_calls,
                "message_count": len(messages),
            }

        except Exception as e:
            print(f"[OpenClawCollector] Parse error: {e}")
            return None

    def _parse_content(self, content) -> str:
        """解析 content，可能是字符串或数组"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type", "")
                    if item_type == "text":
                        text_parts.append(item.get("text", ""))
                    elif item_type == "tool_use":
                        text_parts.append(f"[tool_use: {item.get('name', 'unknown')}]")
                    elif item_type == "tool_result":
                        # 简化 tool_result 内容
                        text_parts.append("[tool_result]")
                elif isinstance(item, str):
                    text_parts.append(item)
            return "".join(text_parts)
        return str(content) if content else ""

    def _extract_metadata(self, file_path: str, agent_id: str) -> Dict:
        """从 sessions.json 提取元数据"""
        metadata = {
            "model": "",
            "updated_at": 0,
            "label": "",
        }

        parts = file_path.split(os.sep)
        if "agents" not in parts:
            return metadata

        idx = parts.index("agents")
        agent_dir = os.path.join(*parts[:idx + 2])
        sessions_json_path = os.path.join(agent_dir, "sessions", "sessions.json")

        if not os.path.exists(sessions_json_path):
            return metadata

        try:
            with open(sessions_json_path, 'r', encoding='utf-8', errors='ignore') as f:
                sessions_data = json.load(f)

            # 查找匹配的 session（sessionFile 存的是完整绝对路径）
            for session_key, session_info in sessions_data.items():
                sf = session_info.get("sessionFile", "")
                if sf == file_path or os.path.basename(sf) == os.path.basename(file_path):
                    metadata["model"] = session_info.get("model", "")
                    metadata["updated_at"] = session_info.get("updatedAt", 0)
                    metadata["label"] = session_info.get("label", "")
                    break
        except Exception as e:
            print(f"[OpenClawCollector] Error extracting metadata: {e}")

        return metadata


collector_plugin = OpenClawCollector()


def on_load():
    print("[OpenClawCollector] Plugin loaded")


def get_collector():
    return collector_plugin