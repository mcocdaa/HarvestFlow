# @file plugins/curators/pii_cleaner/backend.py
# @brief PII 隐私脱敏与高熵密钥遮蔽核心实现
# @create 2026-09-20

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# 常用高熵密钥与敏感凭证正则
API_KEY_PATTERNS = [
    # OpenAI & generic sk- keys
    (re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b'), 'sk-[REDACTED_API_KEY]'),
    # GitHub personal access tokens
    (re.compile(r'\bghp_[A-Za-z0-9]{36}\b'), 'ghp_[REDACTED_GITHUB_TOKEN]'),
    # AWS Access Key ID
    (re.compile(r'\b(AKIA[0-9A-Z]{16})\b'), '[REDACTED_AWS_KEY]'),
    # Google API Key
    (re.compile(r'\b(AIza[0-9A-Za-z-_]{35})\b'), '[REDACTED_GOOGLE_KEY]'),
    # Bearer Token
    (re.compile(r'(?i)(Bearer\s+)[A-Za-z0-9\-_.~+/]{20,}'), r'\1[REDACTED_TOKEN]'),
    # Key-value secret assignments (e.g. api_key="...", secret_key: '...')
    (
        re.compile(r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*([:=])\s*(["\']?)[A-Za-z0-9\-_.~+/]{16,}(["\']?)'),
        r'\1\2\3[REDACTED_SECRET]\4'
    ),
]

# 手机号码正则 (支持中国大陆 11 位手机号及国际常见格式)
PHONE_PATTERNS = [
    # 中国大陆手机号
    (re.compile(r'(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)'), '[REDACTED_PHONE]'),
    # 国际标准格式 e.g. +1-555-123-4567, (555) 123-4567
    (re.compile(r'(?<!\d)\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)'), '[REDACTED_PHONE]'),
]

# 电子邮箱正则
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# 身份证号码 (中国大陆二代 18 位身份证)
ID_CARD_PATTERN = re.compile(r'(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)')


def clean_text(text: str) -> str:
    """对单段文本进行 PII 与机密数据脱敏替换

    Args:
        text: 待脱敏原始文本

    Returns:
        遮蔽后的安全文本
    """
    if not isinstance(text, str) or not text:
        return text

    # 1. 密钥与高熵凭证脱敏
    for pattern, replacement in API_KEY_PATTERNS:
        text = pattern.sub(replacement, text)

    # 2. 手机号码脱敏
    for pattern, replacement in PHONE_PATTERNS:
        text = pattern.sub(replacement, text)

    # 3. 电子邮箱脱敏
    text = EMAIL_PATTERN.sub('[REDACTED_EMAIL]', text)

    # 4. 身份证号码脱敏
    text = ID_CARD_PATTERN.sub('[REDACTED_ID_CARD]', text)

    return text


def clean_session_content(data: Any) -> Any:
    """递归清洗会话字典、列表或消息中的 PII 数据"""
    if isinstance(data, str):
        return clean_text(data)
    elif isinstance(data, dict):
        return {k: clean_session_content(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_session_content(item) for item in data]
    return data


def on_load():
    """插件加载回调"""
    logger.info("✓ [PIICleaner] 隐私脱敏插件已初始化就绪，自动防护 API 密钥与手机号等敏感资产")
