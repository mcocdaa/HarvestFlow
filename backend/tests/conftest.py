# @file backend/tests/conftest.py
# @brief pytest fixtures
# @create 2026-03-22

import os
import sys
import tempfile
import argparse
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def args_with_db_path(temp_db_path):
    namespace = argparse.Namespace(
        db_path=temp_db_path,
        host="127.0.0.1",
        port=3000,
        data_dir="./data",
        log_level="DEBUG",
        cors_origins="*",
        plugins_dir="./plugins",
    )
    return namespace


@pytest.fixture
def args_minimal():
    namespace = argparse.Namespace(
        host="127.0.0.1",
        port=3000,
        data_dir="./data",
        db_path="./data/test.db",
        log_level="DEBUG",
        cors_origins="*",
        plugins_dir="./plugins",
        secrets_yaml="",
        cache_ttl=300,
    )
    return namespace


@pytest.fixture
def temp_plugins_dir(tmp_path):
    yield tmp_path


@pytest.fixture
def plugin_yaml_content():
    return """
name: "Test Plugin"
type: "collector"
version: "1.0.0"
description: "Test plugin for unit testing"
secrets:
  - name: "TEST_API_KEY"
    description: "Test API Key"
    level: "optional"
    default: "test-key-123"
backend_entry: "main.py"
"""
