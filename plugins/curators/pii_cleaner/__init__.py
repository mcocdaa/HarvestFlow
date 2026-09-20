# @file plugins/curators/pii_cleaner/__init__.py
# @brief PII 脱敏清洗插件入口
# @create 2026-09-20

from plugins.curators.pii_cleaner.hooks import *          # noqa: F401,F403
from plugins.curators.pii_cleaner.backend import on_load, clean_text, clean_session_content  # noqa: F401
from plugins.common import call_on_load

call_on_load(on_load, "[PIICleaner]")
