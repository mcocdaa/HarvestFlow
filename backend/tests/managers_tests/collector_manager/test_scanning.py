# @file backend/tests/managers_tests/collector_manager/test_scanning.py
# @brief CollectorManager 扫描文件夹测试
# @create 2026-03-27

from managers.collector_manager import CollectorManager


class TestCollectorManagerScanning:
    def setup_method(self):
        self.manager = CollectorManager()

    def test_scan_folder_returns_json_files(self, tmp_path):
        (tmp_path / "file1.json").write_text("{}")
        (tmp_path / "file2.json").write_text("{}")
        (tmp_path / "file.txt").write_text("text")

        result = self.manager.scan_folder(str(tmp_path))

        assert len(result) == 2
        assert any("file1.json" in f for f in result)
        assert any("file2.json" in f for f in result)

    def test_scan_folder_resursive(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file.json").write_text("{}")

        result = self.manager.scan_folder(str(tmp_path))

        assert len(result) == 1
        assert "subdir" in result[0]

    def test_scan_folder_none_when_no_folder_provided(self):
        self.manager.watch_folders = []
        result = self.manager.scan_folder(None)
        assert result == []

    def test_scan_folder_folder_not_exists(self):
        result = self.manager.scan_folder("/nonexistent/path")
        assert result == []

    def test_scan_folder_uses_first_watch_folder(self):
        self.manager.watch_folders = ["/tmp"]
        result = self.manager.scan_folder(None)
        assert isinstance(result, list)
