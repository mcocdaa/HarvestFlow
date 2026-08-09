# @file plugins/services/infisical/hooks.py
# @brief Infisical 服务插件 hooks
# @create 2026-03-26

import logging

from core.hook_manager import hook_manager
from core import secrets_manager
from plugins.services.infisical.backend import InfisicalSDKClient, get_client

logger = logging.getLogger(__name__)


@hook_manager.hook("secrets_manager_register_arguments")
def register_infisical_arguments(result, manager, parser):
    """在 secrets_manager 注册参数后追加 Infisical SDK 参数"""
    InfisicalSDKClient().register_arguments(parser)
    logger.info("Infisical SDK 参数已注册")


@hook_manager.hook("secrets_manager_init_before")
def register_infisical_client(manager, args, plugin_secrets):
    """在 secrets_manager 初始化前启用 Infisical SDK 客户端（仅当凭证已配置）

    未配置凭证时保持默认的本地密钥客户端，避免服务启动失败。
    """
    client = get_client()
    if client.is_configured(args):
        secrets_manager.set_client_class(InfisicalSDKClient)
        logger.info("Infisical SDK 客户端已注册为默认密钥客户端")
    else:
        logger.info("Infisical 凭证未配置，使用本地密钥客户端")
