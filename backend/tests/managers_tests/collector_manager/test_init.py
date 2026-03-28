# @file backend/tests/managers_tests/collector_manager/test_init.py
# @brief CollectorManager 初始化测试
# @create 2026-03-27

import argparse

from managers.collector_manager import CollectorManager


class TestCollectorManagerInit:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_init_parses_watch_folders(self, args_minimal):
        args_minimal.watch_folders = "/folder1, /folder2,/folder3"
        args_minimal.poll_interval = 30
        self.manager.init(args_minimal)

        assert self.manager.watch_folders == ["/folder1", "/folder2", "/folder3"]
        assert self.manager.poll_interval == 30

    def test_init_empty_watch_folders(self, args_minimal):
        args_minimal.watch_folders = ""
        self.manager.init(args_minimal)

        assert self.manager.watch_folders == []

    def test_init_uses_default_poll_interval(self, args_minimal):
        if hasattr(args_minimal, 'poll_interval'):
            delattr(args_minimal, 'poll_interval')
        self.manager.init(args_minimal)

        assert self.manager.poll_interval == 60

    def test_raw_sessions_dir_property(self, args_minimal):
        from core.setting_manager import setting_manager

        self.manager.init(args_minimal)
        original_data = setting_manager.config.get("DATA_DIR")
        setting_manager.config["DATA_DIR"] = "/test/data"

        assert self.manager.raw_sessions_dir == "/test/data/raw_sessions"

        if original_data is not None:
            setting_manager.config["DATA_DIR"] = original_data

    def test_init_skips_empty_folders_in_split(self, args_minimal):
        args_minimal.watch_folders = " /folder1,, /folder2 ,"
        self.manager.init(args_minimal)

        assert self.manager.watch_folders == ["/folder1", "/folder2"]
        assert len(self.manager.watch_folders) == 2

    def test_init_uses_setting_manager_fallback(self, args_minimal):
        from core import setting_manager
        original = setting_manager.get("WATCH_FOLDERS")
        setting_manager.set("WATCH_FOLDERS", " /one, /two ")

        if hasattr(args_minimal, 'watch_folders'):
            delattr(args_minimal, 'watch_folders')
        self.manager.init(args_minimal)

        assert self.manager.watch_folders == ["/one", "/two"]

        if original is not None:
            setting_manager.set("WATCH_FOLDERS", original)
