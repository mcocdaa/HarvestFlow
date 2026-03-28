# @file plugins/services/infisical/hooks.py
# @brief Infisical 服务插件 hooks
# @create 2026-03-26

import logging

from core.hook_manager import hook_manager
from core import secrets_manager
from plugins.services.infisical.backend import InfisicalSDKClient

logger = logging.getLogger(__name__)


@hook_manager.hook(after="secrets_manager_register_arguments")
def register_infisical_client(parser):
    """在 secrets_manager 注册参数后注册 Infisical SDK 客户端"""
    secrets_manager.register_client("infisical", InfisicalSDKClient)
    secrets_manager.set_client_class(InfisicalSDKClient)
    InfisicalSDKClient().register_arguments(parser)
    logger.info("Infisical SDK 客户端已注册为默认密钥客户端")
