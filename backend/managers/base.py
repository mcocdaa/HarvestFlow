# @file backend/managers/base.py
# @brief 业务管理器基类 - 统一生命周期接口
# @create 2026-08-10

import argparse
import logging
from typing import Dict


class BaseManager:
    """业务管理器基类。

    所有业务管理器继承本类，实现统一生命周期接口：
    - __init__()：基类统一创建 self.logger（以子类类名命名）
    - register_arguments(parser)：注册 argparse 参数（默认空实现）
    - init(args)：初始化（args 为 argparse.Namespace，默认空实现）

    子类覆写时按需使用 @hook_manager.wrap_hooks 包装
    （命名规范 "{manager_name}_{method}_before/after"），基类不强制包装。
    """

    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数（默认无参数）"""

    def init(self, args: argparse.Namespace):
        """初始化管理器（默认空实现）

        Args:
            args: 解析后的命令行参数
        """

    def error_result(self, session_id: str, error: str) -> Dict:
        """构造统一错误结果

        Args:
            session_id: 会话 ID
            error: 错误描述（文案由各调用方提供，保持与既有 API 契约一致）

        Returns:
            {"session_id": ..., "error": ...}
        """
        return {"session_id": session_id, "error": error}
