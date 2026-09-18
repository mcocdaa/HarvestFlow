# @file backend/tests/managers_tests/test_exporter_manager.py
# @brief ExporterManager 测试
# @create 2026-03-26

import argparse
import io
import zipfile

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

    def test_resolve_export_file_ok(self, tmp_path):
        self.manager.output_dir = str(tmp_path)
        target = tmp_path / "sharegpt_1.jsonl"
        target.write_text("{}\n", encoding="utf-8")

        assert self.manager.resolve_export_file("sharegpt_1.jsonl") == str(target)

    def test_resolve_export_file_rejects_invalid_names(self, tmp_path):
        """路径穿越、子目录、空名、非导出后缀均拒绝"""
        self.manager.output_dir = str(tmp_path)
        for name in ["../secret.jsonl", "sub/a.jsonl", "", "note.txt", "..\\secret.jsonl"]:
            with pytest.raises((ValueError, FileNotFoundError)):
                self.manager.resolve_export_file(name)

    def test_resolve_export_file_missing(self, tmp_path):
        self.manager.output_dir = str(tmp_path)
        with pytest.raises(FileNotFoundError):
            self.manager.resolve_export_file("missing.jsonl")

    def test_build_export_zip(self, tmp_path):
        self.manager.output_dir = str(tmp_path)
        (tmp_path / "a.jsonl").write_text("a\n", encoding="utf-8")
        (tmp_path / "b.jsonl").write_text("b\n", encoding="utf-8")

        data = self.manager.build_export_zip(["a.jsonl", "b.jsonl", "a.jsonl"])
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            assert sorted(archive.namelist()) == ["a.jsonl", "b.jsonl"]
            assert archive.read("a.jsonl") == b"a\n"

    def test_build_export_zip_empty(self):
        with pytest.raises(ValueError):
            self.manager.build_export_zip([])

    def test_build_export_zip_missing_file(self, tmp_path):
        self.manager.output_dir = str(tmp_path)
        with pytest.raises(FileNotFoundError):
            self.manager.build_export_zip(["missing.jsonl"])
