# @file backend/tests/managers_tests/test_exporter_manager.py
# @brief ExporterManager 测试
# @create 2026-03-26

import argparse

import pytest

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

    def test_default_output_dir_property(self, args_minimal):
        self.manager.init(args_minimal)
        assert self.manager.default_output_dir is not None
