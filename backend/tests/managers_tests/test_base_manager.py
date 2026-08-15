# @file backend/tests/managers_tests/test_base_manager.py
# @brief BaseManager 基类接口测试
# @create 2026-08-10

import argparse

from managers.base import BaseManager
from managers import (
    SessionManager,
    CollectorManager,
    CuratorManager,
    ReviewerManager,
    ExporterManager,
)

ALL_MANAGER_CLASSES = [
    SessionManager,
    CollectorManager,
    CuratorManager,
    ReviewerManager,
    ExporterManager,
]


class TestBaseManagerInterface:
    def test_all_business_managers_inherit_base_manager(self):
        for cls in ALL_MANAGER_CLASSES:
            assert issubclass(cls, BaseManager), f"{cls.__name__} 未继承 BaseManager"

    def test_default_register_arguments_does_not_raise(self):
        manager = BaseManager()
        parser = argparse.ArgumentParser()
        manager.register_arguments(parser)  # 默认空实现，不应抛异常

    def test_default_init_does_not_raise(self):
        manager = BaseManager()
        args = argparse.Namespace()
        manager.init(args)  # 默认空实现，不应抛异常

    def test_each_manager_instance_is_base_manager(self):
        from managers import (
            session_manager,
            collector_manager,
            curator_manager,
            reviewer_manager,
            exporter_manager,
        )

        for instance in [
            session_manager,
            collector_manager,
            curator_manager,
            reviewer_manager,
            exporter_manager,
        ]:
            assert isinstance(instance, BaseManager)


class TestErrorResult:
    def test_structure(self):
        from managers.base import BaseManager

        bm = BaseManager()
        assert bm.error_result("s1", "session not found") == {
            "session_id": "s1",
            "error": "session not found",
        }
