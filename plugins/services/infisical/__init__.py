# @file plugins/services/infisical/__init__.py
# @brief Infisical 服务插件
# @create 2026-03-26

from plugins.services.infisical.hooks import *  # noqa: F403
from plugins.services.infisical.backend import InfisicalSDKClient as InfisicalSDKClient
from plugins.services.infisical.backend import get_client as get_client
