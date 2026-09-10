# @file backend/core/parsers.py
# @brief 会话文件解析器 - json 通用解析
# @create 2026-08-10

import json
import logging
from typing import Dict, Optional
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

        session_id = data.get("session_id")
        if not session_id:
            session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{Path(file_path).name}"
            data["session_id"] = session_id

        return data
    except Exception as e:
        logger.error(f"解析文件失败 {file_path}: {e}")
        return None
