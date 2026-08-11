# @file backend/managers/base.py
# @brief 业务管理器基类 - 统一生命周期接口
# @create 2026-08-10

import argparse


class BaseManager:
    """业务管理器基类。

    所有业务管理器继承本类，实现统一生命周期接口：
    - register_arguments(parser)：注册 argparse 参数
    - init(args)：初始化（args 为 argparse.Namespace）

    子类覆写时按需使用 @hook_manager.wrap_hooks 包装
    （命名规范 "{manager_name}_{method}_before/after"），基类不强制包装。
    """

    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数（默认空实现）

        Args:
            parser: argparse.ArgumentParser 实例
        """

    def init(self, args: argparse.Namespace):
        """初始化管理器（默认空实现）

        Args:
            args: 解析后的命令行参数
        """
