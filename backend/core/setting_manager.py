# @file backend/core/setting_manager.py
# @brief 配置管理器 - 负责参数解析和全局配置
# @create 2026-03-22

import os
import argparse
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from core import hook_manager

ROOT_DIR = Path(__file__).parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

# 默认配置单一来源：register_arguments 与 init 共用，避免两处默认值漂移
DEFAULTS = {
    "HOST": "0.0.0.0",
    "PORT": 3000,
    "DATA_DIR": "./data",
    "LOG_LEVEL": "INFO",
    "CORS_ORIGINS": "*",
}


class SettingManager:
    """配置管理器

    职责：
    1. 管理全局配置（动态+静态）
    2. 注册核心参数到 argparse
    3. 通过 get() 或属性访问配置

    使用流程：
    1. __init__() 初始化配置存储，加载 .env 文件
    2. register_arguments(parser) 注册参数
    3. init(args) 解析参数
    """

    @hook_manager.wrap_hooks("setting_manager_construct_before", "setting_manager_construct_after")
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self._load_env()

    def _load_env(self):
        """从 .env 文件加载环境变量"""
        env_path = ROOT_DIR / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        for key, value in os.environ.items():
            self.config[key] = value
        self.config.setdefault("API_VERSION", "v1")
        self.config['ROOT_DIR'] = str(ROOT_DIR)
        self.config['BACKEND_DIR'] = str(BACKEND_DIR)

    @hook_manager.wrap_hooks(after="setting_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册核心参数

        Args:
            parser: argparse.ArgumentParser 实例
        """
        group = parser.add_argument_group("Core", "Core Parameters")

        group.add_argument(
            "--host",
            type=str,
            default=os.getenv("HOST", DEFAULTS["HOST"]),
            help=f"绑定地址 (默认: {DEFAULTS['HOST']})"
        )

        group.add_argument(
            "--port",
            type=int,
            default=int(os.getenv("PORT", str(DEFAULTS["PORT"]))),
            help=f"绑定端口 (默认: {DEFAULTS['PORT']})"
        )

        group.add_argument(
            "--data-dir",
            type=str,
            default=os.getenv("DATA_DIR", DEFAULTS["DATA_DIR"]),
            help=f"数据目录 (默认: {DEFAULTS['DATA_DIR']})"
        )

        group.add_argument(
            "--log-level",
            type=str,
            default=os.getenv("LOG_LEVEL", DEFAULTS["LOG_LEVEL"]),
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            help=f"日志级别 (默认: {DEFAULTS['LOG_LEVEL']})"
        )

        group.add_argument(
            "--cors-origins",
            type=str,
            default=os.getenv("CORS_ORIGINS", DEFAULTS["CORS_ORIGINS"]),
            help=f"CORS 允许的源，逗号分隔 (默认: {DEFAULTS['CORS_ORIGINS']})"
        )

    @hook_manager.wrap_hooks("setting_manager_init_before", "setting_manager_init_after")
    def init(self, args: argparse.Namespace):
        """解析并设置配置

        Args:
            args: 解析后的 argparse.Namespace
        """
        self.config["HOST"] = getattr(args, 'host', self.config.get("HOST", DEFAULTS["HOST"]))
        self.config["PORT"] = getattr(args, 'port', self.config.get("PORT", DEFAULTS["PORT"]))
        self.config["DATA_DIR"] = getattr(args, 'data_dir', self.config.get("DATA_DIR", DEFAULTS["DATA_DIR"]))
        self.config["LOG_LEVEL"] = getattr(args, 'log_level', self.config.get("LOG_LEVEL", DEFAULTS["LOG_LEVEL"]))
        cors_raw = getattr(args, 'cors_origins', self.config.get("CORS_ORIGINS", DEFAULTS["CORS_ORIGINS"]))
        if isinstance(cors_raw, list):
            self.config["CORS_ORIGINS"] = cors_raw
        else:
            self.config["CORS_ORIGINS"] = [o.strip() for o in cors_raw.split(",")]

        logging.basicConfig(
            level=getattr(logging, self.config["LOG_LEVEL"]),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self._log_config()

    def _log_config(self):
        """记录配置（敏感值已脱敏）"""
        logger = logging.getLogger(__name__)
        logger.info("=" * 50)
        logger.info("应用配置")
        logger.info("=" * 50)
        SENSITIVE_KEYWORDS = ("SECRET", "KEY", "PASSWORD", "TOKEN", "CREDENTIAL")
        for key, value in self.config.items():
            if any(kw in key.upper() for kw in SENSITIVE_KEYWORDS):
                value = "***"
            logger.info(f"{key}: {value}")
        logger.info("=" * 50)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（key 自动转大写）"""
        return self.config.get(key.upper(), default)

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            raise AttributeError(name)
        return self.config.get(name.upper())

    def set(self, key: str, value: Any):
        """设置配置项（key 自动转大写）"""
        self.config[key.upper()] = value


setting_manager = SettingManager()
