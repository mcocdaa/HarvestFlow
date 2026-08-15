# @file backend/core/constants.py
# @brief 全局枚举与通用业务常量
# @create 2026-08-11

from enum import StrEnum, unique


@unique
class SessionStatus(StrEnum):
    """会话状态枚举（值即数据库存储字符串，Python 3.11+ StrEnum）"""

    RAW = "raw"
    CURATED = "curated"
    APPROVED = "approved"
    REJECTED = "rejected"


@unique
class ExportFormat(StrEnum):
    """导出格式枚举"""

    SHAREGPT = "sharegpt"
    ALPACA = "alpaca"


# ---- 通用业务常量（收敛重复魔法数字）----

# 分页/历史查询 limit 上限
MAX_PAGE_SIZE = 100
# 默认分页大小
DEFAULT_PAGE_SIZE = 20
# 导出历史默认条数
DEFAULT_HISTORY_LIMIT = 20
