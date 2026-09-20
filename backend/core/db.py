# @file backend/core/db.py
# @brief SQLite 读写分离连接池与游标分页工具
# @create 2026-09-20

import queue
import sqlite3
import logging
import base64
import json
import threading
from contextlib import contextmanager
from typing import Optional, Tuple, Generator

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_BUSY_TIMEOUT_MS = 10000
DEFAULT_CACHE_SIZE_KB = -64000  # -64000 KiB ≈ 64MB 缓存
DEFAULT_MIN_READERS = 4
DEFAULT_MAX_READERS = 8


def encode_cursor(created_at: str, session_id: str) -> str:
    """编码 Keyset 分页游标

    Args:
        created_at: 创建时间字符串 (ISO 8601 / SQLite DATETIME)
        session_id: 会话 ID

    Returns:
        URL 安全的 Base64 游标字符串
    """
    payload = json.dumps({"c": str(created_at), "id": str(session_id)}, separators=(',', ':'))
    return base64.urlsafe_b64encode(payload.encode('utf-8')).decode('ascii')


def decode_cursor(cursor_str: str) -> Optional[Tuple[str, str]]:
    """解码 Keyset 分页游标

    Args:
        cursor_str: Base64 游标字符串

    Returns:
        (created_at, session_id) 元组，解码失败返回 None
    """
    if not cursor_str:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode('ascii')).decode('utf-8')
        data = json.loads(raw)
        if isinstance(data, dict) and "c" in data and "id" in data:
            return str(data["c"]), str(data["id"])
    except Exception as e:
        logger.warning(f"游标解码失败: {cursor_str!r} - {e}")
    return None


class DatabasePool:
    """SQLite 读写分离连接池架构

    设计：
    1. 单写连接 (Dedicated Write Connection)：搭配 threading.RLock() 互斥锁，保证原子写入与事务一致性；
    2. 读连接池 (Read Connection Pool)：预分配 4~8 个并发读连接，配置 PRAGMA query_only=ON 防止意外写操作；
    3. 全局优化参数：
       - PRAGMA journal_mode = WAL（读写并发，读不阻塞写，写不阻塞读）
       - PRAGMA busy_timeout = 10000（10 秒超时，杜绝 SQLite 锁争用异常）
       - PRAGMA cache_size = -64000（64MB 页面缓存，加速高频热点检索）
       - PRAGMA synchronous = NORMAL（WAL 模式下的推荐安全性能平衡）
    """

    def __init__(
        self,
        db_path: str,
        min_readers: int = DEFAULT_MIN_READERS,
        max_readers: int = DEFAULT_MAX_READERS,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
        cache_size_kb: int = DEFAULT_CACHE_SIZE_KB,
    ):
        self.db_path = db_path
        self.min_readers = min_readers
        self.max_readers = max(min_readers, max_readers)
        self.busy_timeout_ms = busy_timeout_ms
        self.cache_size_kb = cache_size_kb

        self._write_lock = threading.RLock()
        self._write_conn: Optional[sqlite3.Connection] = None

        self._read_pool: queue.Queue[sqlite3.Connection] = queue.Queue(maxsize=self.max_readers)
        self._total_readers = 0
        self._closed = False
        self._init_lock = threading.Lock()

        self._open_connections()

    def _configure_connection(self, conn: sqlite3.Connection, read_only: bool = False):
        """配置连接的核心 PRAGMA 参数"""
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        conn.execute(f"PRAGMA cache_size = {self.cache_size_kb}")
        if read_only:
            try:
                conn.execute("PRAGMA query_only = ON")
            except sqlite3.OperationalError:
                pass
        else:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")

    def _create_raw_connection(self, read_only: bool = False) -> sqlite3.Connection:
        """创建单个配置好的 SQLite 连接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.busy_timeout_ms / 1000.0,
        )
        self._configure_connection(conn, read_only=read_only)
        return conn

    def _open_connections(self):
        """初始化写连接与初始读连接池"""
        with self._init_lock:
            # 1. 创建专用写连接
            self._write_conn = self._create_raw_connection(read_only=False)

            # 2. 预热初始读连接池
            for _ in range(self.min_readers):
                reader_conn = self._create_raw_connection(read_only=True)
                self._read_pool.put(reader_conn)
                self._total_readers += 1

            logger.info(
                f"[DatabasePool] 已建立读写分离架构: 1 写连接 + {self._total_readers} 读连接 (max={self.max_readers}), "
                f"busy_timeout={self.busy_timeout_ms}ms, cache={abs(self.cache_size_kb)//1000}MB"
            )

    @property
    def write_conn(self) -> sqlite3.Connection:
        """获取写连接（用于需要直接访问底层连接的兼容场景）"""
        if self._closed or not self._write_conn:
            raise RuntimeError("数据库写连接未就绪或已关闭")
        return self._write_conn

    @contextmanager
    def writer(self) -> Generator[sqlite3.Connection, None, None]:
        """写操作上下文管理器：独占写锁 + 自动事务提交/回滚"""
        if self._closed or not self._write_conn:
            raise RuntimeError("数据库写连接未就绪或已关闭")

        with self._write_lock:
            try:
                yield self._write_conn
                self._write_conn.commit()
            except Exception:
                try:
                    self._write_conn.rollback()
                except Exception as rb_err:
                    logger.warning(f"写操作事务回滚异常: {rb_err}")
                raise

    @contextmanager
    def reader(self) -> Generator[sqlite3.Connection, None, None]:
        """读操作上下文管理器：从连接池借出读连接，用毕归还"""
        if self._closed:
            raise RuntimeError("数据库已关闭")

        conn = None
        try:
            conn = self._read_pool.get_nowait()
        except queue.Empty:
            with self._init_lock:
                if self._total_readers < self.max_readers:
                    conn = self._create_raw_connection(read_only=True)
                    self._total_readers += 1
                else:
                    # 等待空闲读连接
                    conn = self._read_pool.get(timeout=self.busy_timeout_ms / 1000.0)

        try:
            yield conn
        finally:
            if conn is not None and not self._closed:
                try:
                    self._read_pool.put_nowait(conn)
                except queue.Full:
                    conn.close()
                    with self._init_lock:
                        self._total_readers -= 1

    def create_indexes(self):
        """创建复合索引以消除深分页全表扫描与状态过滤扫描"""
        with self.writer() as conn:
            # 复合索引：状态与时间降序（工作台与导出核心检索场景）
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_status_created_at
                ON sessions (status, created_at DESC)
            """)
            # 复合索引：时间与主键降序（Keyset 游标分页基石）
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_created_at_id
                ON sessions (created_at DESC, session_id DESC)
            """)
            # 审计日志会话关联索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_session_created
                ON audit_logs (session_id, created_at DESC)
            """)
            # 导出记录时间索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_export_records_created
                ON export_records (created_at DESC)
            """)
        logger.debug("✓ SQLite 复合索引加固完成")

    def close(self):
        """关闭所有写连接与读连接池"""
        with self._init_lock:
            self._closed = True
            if self._write_conn:
                try:
                    self._write_conn.close()
                except Exception as e:
                    logger.warning(f"关闭写连接异常: {e}")
                self._write_conn = None

            while not self._read_pool.empty():
                try:
                    conn = self._read_pool.get_nowait()
                    conn.close()
                except Exception:
                    pass
            self._total_readers = 0
            logger.info("✓ 数据库连接池已安全关闭")
