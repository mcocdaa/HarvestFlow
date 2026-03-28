# @file backend/tests/core_tests/secrets_manager/test_file_loading.py
# @brief SecretsManager 文件加载测试
# @create 2026-03-27

import os
import tempfile
import argparse

from core.secrets_manager import SecretsManager


class TestSecretsManagerFileLoading:
    def setup_method(self):
        self.manager = SecretsManager()

    def test_load_from_secrets_yaml(self, args_minimal):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
secrets:
  - name: CORE_KEY1
    description: Core Key 1
    level: required
  - name: CORE_KEY2
    description: Core Key 2
    level: optional
    default: default_value
""")
            temp_path = f.name

        try:
            args_minimal.secrets_yaml = temp_path
            self.manager.init(args_minimal, [])
            result = self.manager._collect_secret_defs([])

            assert len(result) == 2
            assert any(d["name"] == "CORE_KEY1" for d in result)
            assert any(d["name"] == "CORE_KEY2" for d in result)
            assert any(d["source"] == "core" for d in result)
        finally:
            os.unlink(temp_path)

    def test_skips_nonexistent_yaml(self, args_minimal):
        args_minimal.secrets_yaml = "/nonexistent/path/secrets.yaml"
        self.manager.init(args_minimal, [])
        result = self.manager._collect_secret_defs([])
        assert len(result) == 0

    def test_handles_invalid_yaml(self, args_minimal):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("this is not valid yaml: : :")
            temp_path = f.name

        try:
            args_minimal.secrets_yaml = temp_path
            self.manager.init(args_minimal, [])
            result = self.manager._collect_secret_defs([])

            assert len(result) == 0
        finally:
            os.unlink(temp_path)

    def test_skips_duplicate_secrets(self, args_minimal):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
secrets:
  - name: DUPLICATE_KEY
    description: From file
    level: optional
""")
            temp_path = f.name

        try:
            args_minimal.secrets_yaml = temp_path
            self.manager.init(args_minimal, [
                {"name": "DUPLICATE_KEY", "level": "optional", "source": "plugin"},
                {"name": "UNIQUE_KEY", "level": "required", "source": "plugin"},
            ])
            result = self.manager.list_secrets()

            assert "DUPLICATE_KEY" in result
            assert "UNIQUE_KEY" in result
            assert len(result) == 2
        finally:
            os.unlink(temp_path)

    def test_file_path_exists_but_not_file(self, args_minimal):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "secrets.yaml")
            open(temp_path, 'w').close()
            args_minimal.secrets_yaml = temp_path
            self.manager.init(args_minimal, [])
            result = self.manager._collect_secret_defs([])
            assert len(result) == 0
