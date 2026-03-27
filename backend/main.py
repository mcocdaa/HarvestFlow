# @file backend/main.py
# @brief 项目入口 - HarvestFlow FastAPI 应用启动器
# @create 2026-03-22

import sys
import logging
import argparse
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import (
    hook_manager,
    setting_manager,
    secrets_manager,
    database_manager,
    plugin_manager,
)

from api import register_routers

from managers import (
    session_manager,
    collector_manager,
    curator_manager,
    reviewer_manager,
    exporter_manager,
)

APP_TITLE = "HarvestFlow"
APP_VERSION = "1.0.0"
LOG_SEPARATOR_LENGTH = 50
LOG_SEPARATOR_CHAR = "="

logger = logging.getLogger(__name__)


def log_separator(message: str = None):
    """打印日志分隔符

    Args:
        message: 可选的消息内容
    """
    separator = LOG_SEPARATOR_CHAR * LOG_SEPARATOR_LENGTH
    logger.info(separator)
    if message:
        logger.info(message)
        logger.info(separator)


CORE_MANAGERS = [
    setting_manager,
    secrets_manager,
    database_manager,
    plugin_manager,
]

BUSINESS_MANAGERS = [
    session_manager,
    collector_manager,
    curator_manager,
    reviewer_manager,
    exporter_manager,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_separator("FastAPI 应用启动")

    await hook_manager.run("app_lifespan_start", app)

    log_separator("应用启动完成")

    yield

    logger.info("应用关闭，执行清理...")
    await hook_manager.run("app_lifespan_shutdown", app)
    database_manager.close()
    logger.info("✓ 数据库连接已关闭")


@hook_manager.wrap_hooks(before="init_app_before", after="init_app_after")
def init_app(args: argparse.Namespace):
    """初始化应用

    Args:
        args: 解析后的命令行参数
    """
    setting_manager.init(args)
    plugin_manager.init(args)

    plugin_secrets = plugin_manager.get_plugin_secrets()
    if not secrets_manager.init(args, plugin_secrets):
        logger.error("初始化失败：密钥管理器初始化失败")
        sys.exit(1)

    database_manager.init(args)

    for manager in BUSINESS_MANAGERS:
        manager.init(args)


@hook_manager.wrap_hooks(before="create_app_before", after="create_app_after")
def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    Returns:
        配置好的 FastAPI 应用实例
    """
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=setting_manager.get("cors_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routers(app)

    hook_manager.run_sync("register_routes", app)

    @app.get("/health")
    async def health_check():
        """健康检查接口"""
        return {"status": "ok"}

    return app


def register_all_arguments(parser: argparse.ArgumentParser):
    """注册所有管理器的命令行参数

    Args:
        parser: argparse.ArgumentParser 实例
    """
    for manager in CORE_MANAGERS:
        manager.register_arguments(parser)
    for manager in BUSINESS_MANAGERS:
        manager.register_arguments(parser)


def main():
    """主函数 - 解析参数并启动应用"""
    parser = argparse.ArgumentParser(
        prog=APP_TITLE,
        description=f"{APP_TITLE} - AI Agent 会话数据采集与审核系统"
    )
    plugin_manager.register_hooks()

    register_all_arguments(parser)

    args = parser.parse_args()

    init_app(args)

    log_separator("所有 Manager 初始化完成")

    app = create_app()

    uvicorn.run(
        app,
        host=setting_manager.get("host"),
        port=setting_manager.get("port"),
        log_level=setting_manager.get("log_level", "INFO").lower()
    )


if __name__ == "__main__":
    main()
