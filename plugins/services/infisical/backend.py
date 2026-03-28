# @file plugins/services/infisical/backend.py
# @brief Infisical SDK 密钥客户端
# @create 2026-03-26

import os
import logging
import threading
import argparse
from typing import Optional

from core import setting_manager


logger = logging.getLogger(__name__)

DEFAULT_ENVIRONMENT = "dev"
DEFAULT_HOST = "https://app.infisical.com"
DEFAULT_CACHE_TTL = 300
DEFAULT_TIMEOUT = 10


class InfisicalSDKClient:
    """使用 Infisical SDK 的密钥客户端"""

    def __init__(self):
        self.client_id: str = ""
        self.client_secret: str = ""
        self.project_id: str = ""
        self.environment: str = DEFAULT_ENVIRONMENT
        self.host: str = DEFAULT_HOST
        self.cache_ttl: int = DEFAULT_CACHE_TTL
        self.timeout: int = DEFAULT_TIMEOUT
        self._client = None
        self._connected = False

    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册客户端相关参数"""
        group = parser.add_argument_group("Infisical SDK", "Infisical SDK 配置")
        group.add_argument(
            "--infisical-client-id",
            type=str,
            default=os.getenv("INFISICAL_CLIENT_ID", ""),
            help="Infisical Client ID",
        )
        group.add_argument(
            "--infisical-client-secret",
            type=str,
            default=os.getenv("INFISICAL_CLIENT_SECRET", ""),
            help="Infisical Client Secret",
        )
        group.add_argument(
            "--infisical-project-id",
            type=str,
            default=os.getenv("INFISICAL_PROJECT_ID", ""),
            help="Infisical Project ID",
        )
        group.add_argument(
            "--infisical-environment",
            type=str,
            default=os.getenv("INFISICAL_ENVIRONMENT", DEFAULT_ENVIRONMENT),
            help=f"Infisical Environment (dev/staging/prod) (默认: {DEFAULT_ENVIRONMENT})",
        )
        group.add_argument(
            "--infisical-host",
            type=str,
            default=os.getenv("INFISICAL_HOST", DEFAULT_HOST),
            help=f"Infisical Host (默认: {DEFAULT_HOST})",
        )
        group.add_argument(
            "--infisical-timeout",
            type=int,
            default=int(os.getenv("INFISICAL_TIMEOUT", str(DEFAULT_TIMEOUT))),
            help=f"Infisical 连接超时（秒）(默认: {DEFAULT_TIMEOUT})",
        )

    def init(self, args: argparse.Namespace) -> bool:
        """初始化客户端（尝试连接），返回是否成功"""
        self.client_id = getattr(args, "infisical_client_id", setting_manager.get("INFISICAL_CLIENT_ID", ""))
        self.client_secret = getattr(args, "infisical_client_secret", setting_manager.get("INFISICAL_CLIENT_SECRET", ""))
        self.project_id = getattr(args, "infisical_project_id", setting_manager.get("INFISICAL_PROJECT_ID", ""))
        self.environment = getattr(args, "infisical_environment", setting_manager.get("INFISICAL_ENVIRONMENT", DEFAULT_ENVIRONMENT))
        self.host = getattr(args, "infisical_host", setting_manager.get("INFISICAL_HOST", DEFAULT_HOST))
        self.timeout = getattr(args, "infisical_timeout", setting_manager.get("INFISICAL_TIMEOUT", DEFAULT_TIMEOUT))

        if not self.client_id or not self.client_secret:
            logger.info("Infisical SDK: 未配置 client_id 或 client_secret")
            return False

        if not self.project_id:
            logger.info("Infisical SDK: 未配置 project_id")
            return False

        result = [False]
        error = [None]

        def try_connect():
            try:
                from infisical_sdk import InfisicalSDKClient as SDKClient

                self._client = SDKClient(host=self.host, cache_ttl=self.cache_ttl)
                self._client.auth.universal_auth.login(
                    client_id=self.client_id, client_secret=self.client_secret
                )
                result[0] = True
            except Exception as e:
                error[0] = e

        thread = threading.Thread(target=try_connect)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            logger.warning(f"Infisical SDK 连接超时（{self.timeout}秒）")
            return False

        if error[0]:
            logger.warning(f"Infisical SDK 连接失败: {error[0]}")
            return False

        if result[0]:
            self._connected = True
            logger.info(f"✓ Infisical SDK 已连接 (Project: {self.project_id}, Env: {self.environment})")
            return True

        return False

    def get_secret(self, name: str) -> Optional[str]:
        """获取密钥值"""
        if not self._connected or not self._client:
            return None

        try:
            secret = self._client.secrets.get_secret_by_name(
                secret_name=name,
                project_id=self.project_id,
                environment_slug=self.environment,
                secret_path="/"
            )
            if secret:
                return secret.secret_value
            return None
        except Exception:
            return None

    def set_secret(self, name: str, value: str) -> bool:
        """设置密钥值"""
        if not self._connected or not self._client:
            return False

        try:
            self._client.secrets.create_secret(
                secret_name=name,
                secret_value=value,
                project_id=self.project_id,
                environment_slug=self.environment,
                secret_path="/"
            )
            return True
        except Exception:
            try:
                self._client.secrets.update_secret(
                    secret_name=name,
                    secret_value=value,
                    project_id=self.project_id,
                    environment_slug=self.environment,
                    secret_path="/"
                )
                return True
            except Exception:
                return False

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._connected


_infisical_client = None


def get_client():
    """获取 Infisical SDK 客户端单例"""
    global _infisical_client
    if _infisical_client is None:
        _infisical_client = InfisicalSDKClient()
    return _infisical_client
