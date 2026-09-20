# @file plugins/curators/pii_cleaner/hooks.py
# @brief PII 脱敏插件钩子 - 在数据入库与解析时自动遮蔽机密
# @create 2026-09-20

import logging
from core.hook_manager import hook_manager
from plugins.curators.pii_cleaner.backend import clean_session_content

logger = logging.getLogger(__name__)


@hook_manager.hook("collector_manager_parse_after")
def pii_cleaner_parse_after(result, *args):
    """解析后脱敏钩子：替换采集器解析出的原始会话内容中的敏感机密"""
    if result and isinstance(result, dict):
        cleaned = clean_session_content(result)
        logger.debug("[PIICleaner] 已对采集会话进行 PII 脱敏清洗")
        return cleaned
    return result


@hook_manager.hook("session_manager_create_before")
def pii_cleaner_create_before(self, session_data):
    """会话落库前置脱敏钩子：就地脱敏，保证落库 100% 不含明文密钥与隐私"""
    if session_data and isinstance(session_data, dict):
        if "content" in session_data and session_data["content"]:
            session_data["content"] = clean_session_content(session_data["content"])
    return None
