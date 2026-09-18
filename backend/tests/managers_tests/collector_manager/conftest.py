# @file backend/tests/managers_tests/collector_manager/conftest.py
# @brief 采集管理器测试的 DATA_DIR 隔离（避免监听配置持久化污染真实目录）
# @create 2026-09-18

import pytest

from core import setting_manager


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setitem(setting_manager.config, "DATA_DIR", str(tmp_path))
    yield
