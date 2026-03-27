# @file plugins/services/infisical/hooks.py
# @brief Infisical 服务插件 hooks
# @create 2026-03-26

import logging

from core.hook_manager import hook_manager
from core import secrets_manager

logger = logging.getLogger(__name__)


@hook_manager.hook("secrets_manager_init_after")
def register_infisical_client(args, result):
    """注册 Infisical SDK 客户端作为 secrets manager 的一个 provider

    这个 hook 允许 Infisical SDK 客户端在 secrets_manager 初始化后被注册，
    展示插件如何扩展现有服务的功能。
    """
    if result and hasattr(secrets_manager, 'client'):
        logger.info("Infisical hook: 客户端已就绪")
