# @file backend/test/conftest.py
# @brief 测试配置和公共夹具
# @create 2026-03-18

import pytest
import os
import tempfile
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="function")
def temp_dir():
    temp_path = tempfile.mkdtemp()
    yield temp_path
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture(scope="function")
def test_db_path(temp_dir):
    return os.path.join(temp_dir, "test_harvestflow.db")


@pytest.fixture(scope="function")
def test_data_dir(temp_dir):
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_session():
    return {
        "session_id": "test_session_001",
        "file_path": "/tmp/test.json",
        "status": "raw",
        "agent_role": "backend_dev",
        "task_type": "code_generation",
        "tools_used": ["file_editor", "bash"],
        "tags": ["important", "bug_fix"],
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Write a hello world program"},
            {"role": "assistant", "content": "print('Hello, World!')", "tool_calls": None}
        ],
        "final_output": "print('Hello, World!')"
    }


@pytest.fixture
def sample_session_file(temp_dir, sample_session):
    import json
    session_file = os.path.join(temp_dir, "test_session.json")
    with open(session_file, 'w') as f:
        json.dump(sample_session, f)
    return session_file


@pytest.fixture(autouse=True)
def setup_test_env(test_db_path, test_data_dir):
    from core import database as db_module
    import config.settings as settings

    db_module._db_instance = None
    settings.DB_PATH = test_db_path
    settings.RAW_SESSIONS_DIR = os.path.join(test_data_dir, "raw_sessions")
    settings.AGENT_CURATED_DIR = os.path.join(test_data_dir, "agent_curated")
    settings.HUMAN_APPROVED_DIR = os.path.join(test_data_dir, "human_approved")
    settings.EXPORT_DIR = os.path.join(test_data_dir, "export")

    os.makedirs(settings.RAW_SESSIONS_DIR, exist_ok=True)
    os.makedirs(settings.AGENT_CURATED_DIR, exist_ok=True)
    os.makedirs(settings.HUMAN_APPROVED_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)

    yield

    db_module._db_instance = None
