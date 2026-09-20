# @file backend/tests/core_tests/database_manager/test_db_pool_and_keyset.py
# @brief SQLite 读写分离架构、连接池、Keyset 游标分页与复合索引测试
# @create 2026-09-20

import sqlite3
import pytest
from core.db import DatabasePool, encode_cursor, decode_cursor
from core.database_manager import DatabaseManager


class TestDbPoolAndKeyset:
    def test_encode_decode_cursor(self):
        created_at = "2026-09-20 12:00:00"
        session_id = "session_test_123"
        cursor = encode_cursor(created_at, session_id)
        assert isinstance(cursor, str)
        assert len(cursor) > 0

        decoded = decode_cursor(cursor)
        assert decoded is not None
        assert decoded[0] == created_at
        assert decoded[1] == session_id

    def test_decode_invalid_cursor(self):
        assert decode_cursor("") is None
        assert decode_cursor("invalid-base64-!!!") is None
        assert decode_cursor(None) is None

    def test_pool_pragmas_and_architecture(self, tmp_path):
        db_path = str(tmp_path / "test_pool.db")
        pool = DatabasePool(db_path, min_readers=4, max_readers=8, busy_timeout_ms=10000, cache_size_kb=-64000)

        # 检查写连接 PRAGMA
        with pool.writer() as conn:
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            cache_size = conn.execute("PRAGMA cache_size").fetchone()[0]
            assert journal_mode.lower() == "wal"
            assert busy_timeout == 10000
            assert cache_size == -64000

        # 检查读连接池只读保护 PRAGMA query_only
        with pool.reader() as r_conn:
            busy_timeout = r_conn.execute("PRAGMA busy_timeout").fetchone()[0]
            cache_size = r_conn.execute("PRAGMA cache_size").fetchone()[0]
            assert busy_timeout == 10000
            assert cache_size == -64000
            with pytest.raises(sqlite3.OperationalError):
                r_conn.execute("CREATE TABLE test_should_fail (id INT)")

        pool.close()

    def test_composite_indexes_exist(self, tmp_path):
        db_path = str(tmp_path / "test_indexes.db")
        manager = DatabaseManager()
        import argparse
        manager.init(argparse.Namespace(db_path=db_path))

        with manager._pool.reader() as conn:
            indexes = [
                row["name"] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='sessions'"
                ).fetchall()
            ]
            assert "idx_sessions_status_created_at" in indexes
            assert "idx_sessions_created_at_id" in indexes

        manager.close()

    def test_keyset_cursor_pagination(self, tmp_path):
        db_path = str(tmp_path / "test_keyset.db")
        manager = DatabaseManager()
        import argparse
        manager.init(argparse.Namespace(db_path=db_path))

        # 写入 15 条测试数据，时间有序
        for i in range(15):
            manager.session_create({
                "session_id": f"sess_{i:02d}",
                "status": "raw",
                "quality_auto_score": i % 5 + 1
            })

        # 第 1 页：keyset limit 5
        res1 = manager.session_get_all(page_size=5, sort="recent")
        assert len(res1["sessions"]) == 5
        assert res1["has_more"] is True
        assert res1["next_cursor"] is not None

        # 第 2 页：使用 next_cursor 快速定位
        res2 = manager.session_get_all(page_size=5, sort="recent", cursor=res1["next_cursor"])
        assert len(res2["sessions"]) == 5
        assert res2["has_more"] is True
        assert res2["next_cursor"] is not None

        # 确保两页没有重叠
        ids1 = {s["session_id"] for s in res1["sessions"]}
        ids2 = {s["session_id"] for s in res2["sessions"]}
        assert len(ids1.intersection(ids2)) == 0

        # 第 3 页：最后一页
        res3 = manager.session_get_all(page_size=5, sort="recent", cursor=res2["next_cursor"])
        assert len(res3["sessions"]) == 5
        assert res3["has_more"] is False
        assert res3["next_cursor"] is None

        manager.close()
