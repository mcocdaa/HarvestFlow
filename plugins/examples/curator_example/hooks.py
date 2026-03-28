# @file plugins/examples/curator-example/hooks.py
# @brief Example curator plugin hooks
# @create 2026-03-28

import logging

logger = logging.getLogger(__name__)


def on_load():
    """插件加载时调用"""
    logger.info("[CuratorExample] Plugin loaded")


def on_unload():
    """插件卸载时调用"""
    logger.info("[CuratorExample] Plugin unloaded")
