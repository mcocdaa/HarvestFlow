#!/usr/bin/env python3
# @file scripts/fix_and_import_sessions.py
# @brief 修复并导入会话数据
# @create 2026-03-29

import sys
import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import database_manager, setting_manager
import argparse

SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
DATA_DIR = Path(__file__).parent.parent / "backend" / "data"
RAW_SESSIONS_DIR = DATA_DIR / "raw_sessions"


def parse_jsonl_file(file_path: str):
    """解析 jsonl 文件"""
    try:
        messages = []
        session_id = None
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
                        text_content = ""
                        if isinstance(content_list, list):
                            for item in content_list:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text_content += item.get('text', '')
                        elif isinstance(content_list, str):
                            text_content = content_list
                        if text_content:
                            messages.append({"role": role, "content": text_content})
                    if not session_id and msg.get('id'):
                        session_id = msg.get('id')
                except json.JSONDecodeError:
                    continue
        if not session_id:
            session_id = Path(file_path).stem
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        print(f"解析文件失败 {file_path}: {e}")
        return None


def import_sessions():
    """导入会话"""
    parser = argparse.ArgumentParser()
    setting_manager.register_arguments(parser)
    database_manager.register_arguments(parser)
    args = parser.parse_args([])

    setting_manager.init(args)
    database_manager.init(args)

    RAW_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== 开始导入会话 ===")
    print(f"SESSIONS_DIR: {SESSIONS_DIR}")
    print(f"RAW_SESSIONS_DIR: {RAW_SESSIONS_DIR}")

    imported_count = 0
    jsonl_files = list(SESSIONS_DIR.glob("*.jsonl"))
    print(f"\n找到 {len(jsonl_files)} 个 jsonl 文件")

    for jsonl_file in jsonl_files:
        target_path = RAW_SESSIONS_DIR / jsonl_file.name
        print(f"\n处理文件: {jsonl_file.name}")

        try:
            with open(jsonl_file, 'rb') as fsrc, open(target_path, 'wb') as fdst:
                fdst.write(fsrc.read())

            print(f"  ✓ 已复制到: {target_path}")

            parsed = parse_jsonl_file(str(target_path))
            if parsed:
                session_id = parsed["session_id"]
                print(f"  ✓ 解析会话: {session_id}")

                existing = database_manager.session_get(session_id)
                if existing:
                    print(f"  - 会话已存在，跳过: {session_id}")
                    continue

                session_data = {
                    "session_id": session_id,
                    "file_path": str(target_path.resolve()),
                    "status": "raw",
                    "agent_role": "unknown",
                    "task_type": None,
                    "tools_used": [],
                    "tags": []
                }

                database_manager.session_create(session_data)
                print(f"  ✓ 已创建会话记录: {session_id}")
                imported_count += 1
            else:
                print(f"  ✗ 解析失败: {jsonl_file.name}")

        except Exception as e:
            print(f"  ✗ 导入失败 {jsonl_file.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n=== 导入完成 ===")
    print(f"成功导入 {imported_count} 个会话")

    print(f"\n=== 数据库中的会话 ===")
    result = database_manager.session_get_all(page_size=100)
    for s in result["sessions"]:
        print(f"  - {s['session_id']}: {s['file_path']}")


def check_sessions():
    """检查会话是否正常"""
    parser = argparse.ArgumentParser()
    setting_manager.register_arguments(parser)
    database_manager.register_arguments(parser)
    args = parser.parse_args([])

    setting_manager.init(args)
    database_manager.init(args)

    print("=== 检查会话 ===")
    result = database_manager.session_get_all(page_size=100)
    print(f"共 {result['total']} 个会话")

    for s in result["sessions"]:
        session_id = s['session_id']
        file_path = s['file_path']
        exists = os.path.exists(file_path)
        print(f"\n会话: {session_id}")
        print(f"  文件路径: {file_path}")
        print(f"  文件存在: {'✓' if exists else '✗'}")

        if exists:
            try:
                parsed = parse_jsonl_file(file_path)
                if parsed and parsed["messages"]:
                    print(f"  ✓ 有 {len(parsed['messages'])} 条消息")
                else:
                    print(f"  ✗ 没有消息内容")
            except Exception as e:
                print(f"  ✗ 读取失败: {e}")


if __name__ == "__main__":
    import_sessions()
    print("\n" + "="*50)
    check_sessions()
