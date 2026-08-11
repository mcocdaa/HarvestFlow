# @file plugins/collectors/openclaw/__init__.py
# @brief OpenClaw 采集器插件入口
# @create 2026-03-27

from plugins.collectors.openclaw.hooks import *  # noqa: F403
from plugins.collectors.openclaw.backend import on_load
from plugins.common import call_on_load

# 调用 on_load 来初始化采集器（失败仅记录日志，不中断导入）
call_on_load(on_load, "[OpenClaw]")
