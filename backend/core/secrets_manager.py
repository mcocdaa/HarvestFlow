# @file backend/core/secrets_manager.py
# @brief 密钥管理器 - 支持 Infisical SDK 和本地模式
# @create 2026-03-22

import os
import json
import yaml
import base64
import secrets
import logging
import time
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
import argparse
import threading

from core import hook_manager
from core import setting_manager


SECRET_TOKEN_BYTES = 24
REFRESH_WAIT_MAX_ITERATIONS = 50
REFRESH_WAIT_INTERVAL = 0.1


class BaseSecretsClient(ABC):
    """密钥客户端抽象基类"""

    @abstractmethod
    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册客户端相关参数"""
        pass

    @abstractmethod
    def init(self, args: argparse.Namespace) -> bool:
        """初始化客户端（尝试连接），返回是否成功"""
        pass

    @abstractmethod
    def get_secret(self, name: str) -> Optional[str]:
        """获取密钥值"""
        pass

    @abstractmethod
    def set_secret(self, name: str, value: str) -> bool:
        """设置密钥值"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        pass


class InfisicalSDKClient(BaseSecretsClient):
    """使用 Infisical SDK 的密钥客户端"""

    def __init__(self):
        self.client_id: str = ""
        self.client_secret: str = ""
        self.project_id: str = ""
        self.environment: str = "dev"
        self.host: str = "https://app.infisical.com"
        self.cache_ttl: int = 300
        self.timeout: int = 10
        self._client = None
        self._connected = False

    def register_arguments(self, parser: argparse.ArgumentParser):
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
            default=os.getenv("INFISICAL_ENVIRONMENT", "dev"),
            help="Infisical Environment (dev/staging/prod)",
        )
        group.add_argument(
            "--infisical-host",
            type=str,
            default=os.getenv("INFISICAL_HOST", "https://app.infisical.com"),
            help="Infisical Host (默认: https://app.infisical.com)",
        )
        group.add_argument(
            "--infisical-timeout",
            type=int,
            default=int(os.getenv("INFISICAL_TIMEOUT", "10")),
            help="Infisical 连接超时（秒）(默认: 10)",
        )

    def init(self, args: argparse.Namespace) -> bool:
        self.client_id = getattr(args, "infisical_client_id", setting_manager.get("INFISICAL_CLIENT_ID", ""))
        self.client_secret = getattr(args, "infisical_client_secret", setting_manager.get("INFISICAL_CLIENT_SECRET", ""))
        self.project_id = getattr(args, "infisical_project_id", setting_manager.get("INFISICAL_PROJECT_ID", ""))
        self.environment = getattr(args, "infisical_environment", setting_manager.get("INFISICAL_ENVIRONMENT", "dev"))
        self.host = getattr(args, "infisical_host", setting_manager.get("INFISICAL_HOST", "https://app.infisical.com"))
        self.timeout = getattr(args, "infisical_timeout", setting_manager.get("INFISICAL_TIMEOUT", 10))

        if not self.client_id or not self.client_secret:
            logging.getLogger(__name__).info("Infisical SDK: 未配置 client_id 或 client_secret")
            return False

        if not self.project_id:
            logging.getLogger(__name__).info("Infisical SDK: 未配置 project_id")
            return False

        result = [False]
        error = [None]

        def try_connect():
            try:
                from infisical_sdk import InfisicalSDKClient

                self._client = InfisicalSDKClient(host=self.host, cache_ttl=self.cache_ttl)
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
            logging.getLogger(__name__).warning(f"Infisical SDK 连接超时（{self.timeout}秒）")
            return False

        if error[0]:
            logging.getLogger(__name__).warning(f"Infisical SDK 连接失败: {error[0]}")
            return False

        if result[0]:
            self._connected = True
            logging.getLogger(__name__).info(f"✓ Infisical SDK 已连接 (Project: {self.project_id}, Env: {self.environment})")
            return True

        return False

    def get_secret(self, name: str) -> Optional[str]:
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
        return self._connected


class LocalSecretsClient(BaseSecretsClient):
    """本地密钥客户端（无远程服务时使用）"""

    def __init__(self):
        self._secrets: Dict[str, str] = {}
        self._connected = True

    def register_arguments(self, parser: argparse.ArgumentParser):
        pass

    def init(self, args: argparse.Namespace) -> bool:
        self._connected = True
        return True

    def get_secret(self, name: str) -> Optional[str]:
        return self._secrets.get(name)

    def set_secret(self, name: str, value: str) -> bool:
        self._secrets[name] = value
        return True

    def is_available(self) -> bool:
        return self._connected


class SecretsManager:
    """密钥管理器

    职责：
    1. 注册密钥相关参数
    2. 初始化时加载密钥定义
    3. 从 Infisical SDK 或本地获取密钥值
    4. 提供密钥缓存和刷新机制

    使用流程：
    1. register_arguments(parser) 注册参数
    2. init(args, plugin_secrets) 初始化
    """

    @hook_manager.wrap_hooks("secrets_manager_construct_before", "secrets_manager_construct_after")
    def __init__(self, client_type: str = "local"):
        self.logger = logging.getLogger(__name__)
        self.secrets_yaml_path: str = ""
        self.cache_ttl: int = 300
        self.client: Optional[BaseSecretsClient] = None
        self.sdk_available: bool = False
        self.secret_defs: List[Dict[str, Any]] = []
        self.secrets_cache: Dict[str, tuple] = {}
        self.refreshing: set = set()

        if client_type == "infisical":
            self._client_class: Type[BaseSecretsClient] = InfisicalSDKClient
        else:
            self._client_class: Type[BaseSecretsClient] = LocalSecretsClient

    @hook_manager.wrap_hooks(after="secrets_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_argument_group("Secrets", "Secrets Management")

        group.add_argument(
            "--secrets-yaml",
            type=str,
            default=os.getenv("SECRETS_YAML", ""),
            help="密钥定义文件路径",
        )

        group.add_argument(
            "--cache-ttl",
            type=int,
            default=int(os.getenv("SECRETS_CACHE_TTL", "300")),
            help="密钥缓存过期时间（秒）(默认: 300)",
        )

        self._client_class().register_arguments(parser)

    @hook_manager.wrap_hooks("secrets_manager_init_before", "secrets_manager_init_after")
    def init(self, args: argparse.Namespace, plugin_secrets: List[Dict[str, Any]]):
        """初始化密钥管理器

        Args:
            args: 解析后的参数
            plugin_secrets: 插件密钥定义列表
        """
        self.logger.info("=" * 50)
        self.logger.info("开始初始化密钥管理器")
        self.logger.info("=" * 50)

        self.secrets_yaml_path = getattr(args, "secrets_yaml", setting_manager.get("SECRETS_YAML", ""))
        self.cache_ttl = getattr(args, "cache_ttl", setting_manager.get("SECRETS_CACHE_TTL", 300))

        self.client = self._client_class()
        self.sdk_available = isinstance(self.client, InfisicalSDKClient)

        if not self.client.init(args):
            self.logger.error("✗ 密钥客户端初始化失败")
            self.logger.info("=" * 50)
            return False

        self.secret_defs = self._collect_secret_defs(plugin_secrets)
        self.logger.info(f"已注册 {len(self.secret_defs)} 个密钥定义")

        self._load_all_secrets()

        success = self._validate_required()

        if success:
            mode = "Infisical SDK" if self.sdk_available else "本地"
            self.logger.info(f"✓ 密钥管理器初始化完成（{mode}模式）")
        else:
            self.logger.error("✗ 密钥管理器初始化失败")

        self.logger.info("=" * 50)
        return success

    def _collect_secret_defs(self, plugin_secret_defs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """收集所有密钥定义"""
        all_defs = []

        if self.secrets_yaml_path:
            path = Path(self.secrets_yaml_path)
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}

                    for secret in data.get("secrets", []):
                        all_defs.append(
                            {
                                "name": secret["name"],
                                "description": secret.get("description", ""),
                                "level": secret.get("level", "optional"),
                                "default": secret.get("default"),
                                "source": "core",
                            }
                        )
                    self.logger.info(f"从 {path} 加载了 {len(data.get('secrets', []))} 个核心密钥")
                except Exception as e:
                    self.logger.error(f"加载核心密钥定义失败: {e}")
            else:
                self.logger.warning(f"核心密钥定义文件不存在: {path}")

        for secret in plugin_secret_defs:
            existing = next((d for d in all_defs if d["name"] == secret["name"]), None)
            if existing:
                self.logger.warning(f"密钥定义重复，跳过: {secret['name']}")
                continue
            all_defs.append(secret)

        if plugin_secret_defs:
            self.logger.info(f"从插件加载了 {len(plugin_secret_defs)} 个密钥定义")

        return all_defs

    def _load_all_secrets(self):
        """加载所有密钥值到缓存"""
        self.logger.info("加载密钥值...")

        for def_ in self.secret_defs:
            name = def_["name"]
            value = self._resolve_secret_value(def_)
            self._set_cache(name, value)

            source = self._get_value_source(def_)
            self.logger.info(f"  [{def_['level']:8}] {name}: {source}")

    def _resolve_secret_value(self, def_: Dict[str, Any]) -> str:
        """解析密钥值"""
        name = def_["name"]
        level = def_.get("level", "optional")
        default = def_.get("default")

        if self.client and self.client.is_available():
            secret_value = self.client.get_secret(name)
            if secret_value is not None:
                return secret_value

            if level == "required":
                random_value = self._generate_random_secret()
                if self.client.set_secret(name, random_value):
                    self.logger.info(f"  {name}: required 密钥已上传到 Infisical")
                else:
                    self.logger.warning(f"  {name}: required 密钥上传失败，使用本地随机值")
                return random_value

        if level == "required":
            random_value = self._generate_random_secret()
            self.logger.warning(f"  {name}: required 密钥未配置，已自动生成随机值")
            return random_value

        if default is not None:
            return str(default)

        return ""

    def _get_value_source(self, def_: Dict[str, Any]) -> str:
        """获取值的来源描述"""
        name = def_["name"]
        level = def_.get("level", "optional")

        if self.client and self.client.is_available():
            secret_value = self.client.get_secret(name)
            if secret_value is not None:
                return "Infisical"

        if level == "required":
            return "随机生成"

        if def_.get("default") is not None:
            return "默认值"

        return "空值"

    def _generate_random_secret(self) -> str:
        """生成 32 位 URL-safe base64 随机字符串"""
        return base64.urlsafe_b64encode(secrets.token_bytes(SECRET_TOKEN_BYTES)).decode("ascii")

    def _validate_required(self) -> bool:
        """验证所有 required 密钥都有值"""
        missing = []

        for def_ in self.secret_defs:
            if def_.get("level") == "required":
                name = def_["name"]
                value = self._get_cache(name)
                if not value:
                    missing.append(name)

        if missing:
            self.logger.error(f"缺少必需密钥: {missing}")
            return False

        return True

    def _set_cache(self, name: str, value: str):
        """设置缓存值"""
        self.secrets_cache[name] = (value, time.time())

    def _get_cache(self, name: str) -> Optional[str]:
        """获取缓存值"""
        if name not in self.secrets_cache:
            return None

        value, timestamp = self.secrets_cache[name]

        if time.time() - timestamp > self.cache_ttl:
            return None

        return value

    def is_cache_expired(self, name: str) -> bool:
        """检查缓存是否过期"""
        if name not in self.secrets_cache:
            return True

        timestamp = self.secrets_cache[name][1]
        return time.time() - timestamp > self.cache_ttl

    def refresh_secret(self, name: str) -> Optional[str]:
        """强制刷新指定密钥"""
        if name in self.refreshing:
            for _ in range(REFRESH_WAIT_MAX_ITERATIONS):
                if name not in self.refreshing:
                    break
                time.sleep(REFRESH_WAIT_INTERVAL)
            return self._get_cache(name)

        self.refreshing.add(name)
        try:
            if self.client and self.client.is_available():
                new_value = self.client.get_secret(name)
                if new_value is not None:
                    self._set_cache(name, new_value)
                    self.logger.info(f"密钥 {name} 已刷新")
                    return new_value

            return self._get_cache(name)
        finally:
            self.refreshing.discard(name)

    def refresh_all_secrets(self):
        """强制刷新所有密钥"""
        self.logger.info("刷新所有密钥...")
        for def_ in self.secret_defs:
            self.refresh_secret(def_["name"])
        self.logger.info("所有密钥刷新完成")

    def get_secret(self, name: str) -> str:
        """获取密钥值（从缓存）"""
        value = self._get_cache(name)
        return value if value is not None else ""

    def get_secret_force_refresh(self, name: str) -> str:
        """获取密钥值（强制刷新）"""
        value = self.refresh_secret(name)
        return value if value is not None else ""

    def is_sdk_available(self) -> bool:
        """Infisical SDK 是否可用"""
        return self.sdk_available

    def is_agent_available(self) -> bool:
        """兼容性别名（已废弃，推荐使用 is_sdk_available）"""
        return self.sdk_available

    def list_secrets(self) -> List[str]:
        """列出所有已注册的密钥名称"""
        return [d["name"] for d in self.secret_defs]


secrets_manager = SecretsManager()
