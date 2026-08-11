# @file plugins/curators/openclaw/__init__.py
# @brief OpenClaw 审核器插件入口
# @create 2026-08-11

from plugins.curators.openclaw.hooks import *          # noqa: F401,F403
from plugins.curators.openclaw.backend import on_load  # noqa: F401
from plugins.common import call_on_load

call_on_load(on_load, "[OpenClawCurator]")
