# @file backend/tests/managers_tests/collector_manager/test_watch_folders.py
# @brief CollectorManager 监视文件夹管理测试
# @create 2026-03-27

from managers.collector_manager import CollectorManager


class TestCollectorManagerWatchFolders:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_add_watch_folder_adds_new(self):
        self.manager.add_watch_folder("/test/path")
        assert "/test/path" in self.manager.watch_folders

    def test_add_watch_folder_prevents_duplicates(self):
        self.manager.add_watch_folder("/test/path")
        self.manager.add_watch_folder("/test/path")
        assert len(self.manager.watch_folders) == 1

    def test_remove_watch_folder_removes(self):
        self.manager.add_watch_folder("/test/path")
        assert "/test/path" in self.manager.watch_folders

        self.manager.remove_watch_folder("/test/path")
        assert "/test/path" not in self.manager.watch_folders

    def test_remove_watch_folder_ignores_not_present(self):
        self.manager.remove_watch_folder("/nonexistent")
        assert len(self.manager.watch_folders) == 0
