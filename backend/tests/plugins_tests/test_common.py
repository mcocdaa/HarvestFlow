# @file backend/tests/plugins_tests/test_common.py
# @brief plugins.common.call_on_load 单元测试
# @create 2026-08-10

import logging
import sys
from pathlib import Path

# 项目根（plugins/ 与 backend/ 的父目录）加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from plugins.common import call_on_load  # noqa: E402


class TestCallOnLoad:
    def test_calls_on_load(self):
        called = []

        def on_load():
            called.append(True)

        call_on_load(on_load, "[Test]")
        assert called == [True]

    def test_error_logged_but_not_raised(self, caplog):
        def bad_on_load():
            raise RuntimeError("boom")

        with caplog.at_level(logging.ERROR, logger="plugins.common"):
            call_on_load(bad_on_load, "[Test]")

        assert any(
            "[Test] 调用 on_load 失败：boom" in record.getMessage()
            for record in caplog.records
        )

    def test_none_skipped_silently(self, caplog):
        with caplog.at_level(logging.ERROR, logger="plugins.common"):
            call_on_load(None, "[Test]")
        assert len(caplog.records) == 0
