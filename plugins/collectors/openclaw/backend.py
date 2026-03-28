# @file plugins/collectors/openclaw/backend.py
# @brief OpenClaw 会话采集器插件
# @create 2026-03-18

import os
import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_AGENTS_DIR = "C:/Users/20211/.openclaw/agents"
DEFAULT_TARGET_AGENTS = ["backend_dev", "req_analyst", "qa_ops", "coord"]
DEFAULT_MIN_MESSAGE_COUNT = 5


class OpenClawCollector:
    name = "openclaw"
    description = "OpenClaw Agent session collector - reads from local OpenClaw session files"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.agents_dir = self.config.get("agents_dir", DEFAULT_AGENTS_DIR)
        self.target_agents = self.config.get("target_agents", DEFAULT_TARGET_AGENTS)
        self.skip_cron = self.config.get("skip_cron_sessions", True)
        self.min_message_count = self.config.get("min_message_count", DEFAULT_MIN_MESSAGE_COUNT)

    def scan(self) -> List[str]:
        """扫描所有目标 agent 的 sessions.json，返回 jsonl 文件路径列表

        Returns:
            jsonl 文件路径列表
        """
        jsonl_files = []
        logger.info(f"[OpenClawCollector] 开始扫描，agents_dir: {self.agents_dir}, target_agents: {self.target_agents}")

        if not os.path.exists(self.agents_dir):
            logger.warning(f"[OpenClawCollector] agents_dir not found: {self.agents_dir}")
            return jsonl_files

        for agent_id in self.target_agents:
            logger.info(f"[OpenClawCollector] 扫描 agent: {agent_id}")
            agent_sessions_path = os.path.join(self.agents_dir, agent_id, "sessions", "sessions.json")
            logger.info(f"[OpenClawCollector] sessions.json 路径：{agent_sessions_path}, 存在：{os.path.exists(agent_sessions_path)}")
            if not os.path.exists(agent_sessions_path):
                # 如果 sessions.json 不存在，直接扫描目录中的 jsonl 文件
                sessions_dir = os.path.join(self.agents_dir, agent_id, "sessions")
                logger.info(f"[OpenClawCollector] sessions.json 不存在，扫描目录：{sessions_dir}")
                if os.path.exists(sessions_dir):
                    for file in os.listdir(sessions_dir):
                        logger.info(f"[OpenClawCollector] 发现文件：{file}")
                        if file.endswith('.jsonl'):
                            jsonl_files.append(os.path.join(sessions_dir, file))
                continue

            try:
                with open(agent_sessions_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sessions_data = json.load(f)

                for session_key, session_info in sessions_data.items():
                    if self.skip_cron and ":cron:" in session_key:
                        continue

                    session_file = session_info.get("sessionFile")
                    if session_file:
                        # 尝试将 Windows 路径转换为 Linux 路径
                        if 'C:' in session_file or 'c:' in session_file:
                            # 提取文件名（处理 Windows 路径分隔符）
                            file_name = session_file.split('\\')[-1].split('/')[-1]
                            session_file = os.path.join(self.agents_dir, agent_id, "sessions", file_name)
                            logger.info(f"[OpenClawCollector] 转换 Windows 路径：{session_info.get('sessionFile')} -> {session_file}")
                        if os.path.exists(session_file):
                            jsonl_files.append(session_file)
                        else:
                            logger.warning(f"[OpenClawCollector] 文件不存在：{session_file}")
            except Exception as e:
                logger.error(f"[OpenClawCollector] Error scanning {agent_id}: {e}")

        logger.info(f"[OpenClawCollector] 扫描完成，找到 {len(jsonl_files)} 个文件：{jsonl_files}")
        return jsonl_files

    def parse(self, file_path: str) -> Optional[Dict[str, Any]]:
        """读取 jsonl 文件，解析为标准格式

        Args:
            file_path: jsonl 文件路径

        Returns:
            解析后的会话数据，失败返回 None
        """
        try:
            messages = []
            tools_used = set()
            has_tool_calls = False
            session_id = None
            session_key = None
            agent_id = None

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

                    parsed_content = self._parse_content(content)

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

                    if not session_id:
                        session_id = msg.get("sessionId")

            if agent_id and session_id:
                session_key = f"agent:{agent_id}:{session_id[:8]}"

            metadata = self._extract_metadata(file_path, agent_id)

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
            logger.error(f"[OpenClawCollector] Parse error: {e}")
            return None

    def _parse_content(self, content: Any) -> str:
        """解析 content，可能是字符串或数组

        Args:
            content: 内容，可能是字符串或数组

        Returns:
            解析后的字符串
        """
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
                        text_parts.append("[tool_result]")
                elif isinstance(item, str):
                    text_parts.append(item)
            return "".join(text_parts)
        return str(content) if content else ""

    def _extract_metadata(self, file_path: str, agent_id: str) -> Dict[str, Any]:
        """从 sessions.json 提取元数据

        Args:
            file_path: 会话文件路径
            agent_id: agent ID

        Returns:
            元数据字典
        """
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

            for session_key, session_info in sessions_data.items():
                sf = session_info.get("sessionFile", "")
                if sf == file_path or os.path.basename(sf) == os.path.basename(file_path):
                    metadata["model"] = session_info.get("model", "")
                    metadata["updated_at"] = session_info.get("updatedAt", 0)
                    metadata["label"] = session_info.get("label", "")
                    break
        except Exception as e:
            logger.error(f"[OpenClawCollector] Error extracting metadata: {e}")

        return metadata


collector_plugin = None


def on_load():
    global collector_plugin
    import os
    import yaml

    logger.info("[OpenClawCollector] Plugin loaded")

    # 从 plugin.yaml 读取配置
    plugin_yaml_path = os.path.join(os.path.dirname(__file__), 'plugin.yaml')
    config = {}
    if os.path.exists(plugin_yaml_path):
        with open(plugin_yaml_path, 'r', encoding='utf-8') as f:
            plugin_data = yaml.safe_load(f)
            config = plugin_data.get('config', {})

    collector_plugin = OpenClawCollector(config)


def get_collector():
    return collector_plugin
