# @file plugins/common.py
# @brief 插件公共辅助 - 统一的插件生命周期样板
# @create 2026-08-10

import logging


def call_on_load(on_load_func, log_prefix: str) -> None:
    """安全调用插件 on_load：失败记录错误但不中断插件导入

    Args:
        on_load_func: 插件的 on_load 可调用对象（不存在时传入 None 跳过）
        log_prefix: 日志前缀，如 "[OpenClaw]"
    """
    if on_load_func is None:
        return
    try:
        on_load_func()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"{log_prefix} 调用 on_load 失败：{e}")
