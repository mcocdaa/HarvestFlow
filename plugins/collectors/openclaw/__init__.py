# @file plugins/collectors/openclaw/__init__.py
# @brief OpenClaw 采集器插件入口
# @create 2026-03-27

from plugins.collectors.openclaw.hooks import *

# 调用 on_load 来初始化采集器
try:
    from plugins.collectors.openclaw.backend import on_load
    on_load()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"[OpenClaw] 调用 on_load 失败：{e}")
