# @file backend/tests/managers_tests/test_exporter_manager.py
# @brief ExporterManager 测试
# @create 2026-03-26

import argparse


from managers.exporter_manager import ExporterManager


class TestExporterManager:
    def setup_method(self):
        self.manager = ExporterManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_init_sets_default_format(self, args_minimal):
        self.manager.init(args_minimal)
        assert self.manager.default_format == "sharegpt"

    def test_init_uses_arguments(self, args_minimal):
        args_minimal.export_default_format = "alpaca"
        args_minimal.export_output_dir = "/custom/export"
        self.manager.init(args_minimal)

        assert self.manager.default_format == "alpaca"
        assert self.manager.output_dir == "/custom/export"

    def test_convert_sharegpt_skips_null_content(self):
        """P1.5: _convert_to_sharegpt skips sessions with null/empty content."""
        sessions = [
            {"session_id": "1", "content": None},
            {"session_id": "2", "content": {}},
            {"session_id": "3", "content": {"messages": [{"role": "user", "content": "hello"}]}},
        ]
        result = self.manager._convert_to_sharegpt(sessions)
        assert len(result) == 1

    def test_convert_alpaca_skips_null_content(self):
        """P1.5: _convert_to_alpaca skips sessions with null/empty content."""
        sessions = [
            {"session_id": "1", "content": None},
            {"session_id": "2", "content": {}},
            {"session_id": "3", "content": {"messages": [{"role": "assistant", "content": "output"}]}},
        ]
        result = self.manager._convert_to_alpaca(sessions)
        assert len(result) == 1
