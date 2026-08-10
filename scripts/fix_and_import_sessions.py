#!/usr/bin/env python3
# @file scripts/fix_and_import_sessions.py
# @brief 修复并导入会话数据
# @create 2026-03-29

import sys
import os
import sqlite3
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import database_manager, setting_manager
from managers.collector_manager import collector_manager

SESSIONS_DIR = Path(__file__).parent.parent / "backend" / "data" / "raw_sessions"
DATA_DIR = Path(__file__).parent.parent / "backend" / "data"
RAW_SESSIONS_DIR = DATA_DIR / "raw_sessions"


def import_sessions(dry_run=False):
    """导入会话"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=dry_run,
        help="Scan sessions without actually importing them",
    )
    setting_manager.register_arguments(parser)
    database_manager.register_arguments(parser)
    args = parser.parse_args()
    dry_run = args.dry_run

    setting_manager.init(args)
    database_manager.init(args)

    RAW_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== 开始导入会话 {'(dry-run)' if dry_run else ''} ===")
    print(f"SESSIONS_DIR: {SESSIONS_DIR}")
    print(f"RAW_SESSIONS_DIR: {RAW_SESSIONS_DIR}")

    imported_count = 0
    jsonl_files = list(SESSIONS_DIR.glob("*.jsonl"))
    print(f"\n找到 {len(jsonl_files)} 个 jsonl 文件")

    for jsonl_file in jsonl_files:
        target_path = RAW_SESSIONS_DIR / jsonl_file.name
        print(f"\n处理文件: {jsonl_file.name}")

        try:
            if dry_run:
                print(f"  [dry-run] 将复制到: {target_path}")
            else:
                with open(jsonl_file, 'rb') as fsrc, open(target_path, 'wb') as fdst:
                    fdst.write(fsrc.read())
                print(f"  ✓ 已复制到: {target_path}")

            parsed = collector_manager.parse_session_file(str(target_path))
            if parsed:
                session_id = parsed["session_id"]
                print(f"  ✓ 解析会话: {session_id}")

                existing = database_manager.session_get(session_id)
                if existing:
                    print(f"  - 会话已存在，跳过: {session_id}")
                    continue

                if dry_run:
                    print(f"  [dry-run] 将创建会话记录: {session_id}")
                    imported_count += 1
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
    args = parser.parse_args()

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
                parsed = collector_manager.parse_session_file(file_path)
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
