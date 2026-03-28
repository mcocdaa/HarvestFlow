# @file backend/tests/managers_tests/curator_manager/test_init.py
# @brief CuratorManager 初始化测试
# @create 2026-03-27

import argparse

from managers.curator_manager import CuratorManager


class TestCuratorManagerInit:
    def setup_method(self):
        self.manager = CuratorManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_init_uses_arguments(self, args_minimal):
        args_minimal.curator_enabled = False
        args_minimal.auto_approve_threshold = 5
        self.manager.init(args_minimal)

        assert self.manager.enabled is False
        assert self.manager.auto_approve_threshold == 5

    def test_init_uses_defaults(self, args_minimal):
        if hasattr(args_minimal, 'curator_enabled'):
            delattr(args_minimal, 'curator_enabled')
        if hasattr(args_minimal, 'auto_approve_threshold'):
            delattr(args_minimal, 'auto_approve_threshold')
        self.manager.init(args_minimal)

        assert self.manager.enabled is True
        assert self.manager.auto_approve_threshold == 4

    def test_agent_curated_dir_property(self, args_minimal):
        from core.setting_manager import setting_manager

        self.manager.init(args_minimal)
        original_data = setting_manager.config.get("DATA_DIR")
        setting_manager.config["DATA_DIR"] = "/test/data"

        assert self.manager.agent_curated_dir == "/test/data/agent_curated"

        if original_data is not None:
            setting_manager.config["DATA_DIR"] = original_data

    def test_init_parses_boolean_values(self, args_minimal):
        cases = [
            (False, False),
            (True, True),
            ("false", False),
            ("true", True),
            ("1", True),
            ("0", False),
        ]
        from core import setting_manager
        original_enabled = setting_manager.get("CURATOR_ENABLED")

        for input_val, expected in cases:
            args_minimal.curator_enabled = input_val
            self.manager.init(args_minimal)
            assert self.manager.enabled == expected

        if original_enabled is not None:
            setting_manager.set("CURATOR_ENABLED", original_enabled)

    def test_init_uses_setting_manager_fallback(self, args_minimal):
        from core import setting_manager
        original_enabled = setting_manager.get("CURATOR_ENABLED")
        original_threshold = setting_manager.get("AUTO_APPROVE_THRESHOLD")

        setting_manager.set("CURATOR_ENABLED", "False")
        setting_manager.set("AUTO_APPROVE_THRESHOLD", "3")

        if hasattr(args_minimal, 'curator_enabled'):
            delattr(args_minimal, 'curator_enabled')
        if hasattr(args_minimal, 'auto_approve_threshold'):
            delattr(args_minimal, 'auto_approve_threshold')

        self.manager.init(args_minimal)

        assert self.manager.enabled is False
        assert self.manager.auto_approve_threshold == 3

        if original_enabled is not None:
            setting_manager.set("CURATOR_ENABLED", original_enabled)
        if original_threshold is not None:
            setting_manager.set("AUTO_APPROVE_THRESHOLD", original_threshold)
