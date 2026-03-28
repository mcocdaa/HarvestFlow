import os
import sys
from importlib.util import spec_from_file_location
from fastapi import APIRouter
from pathlib import Path
import tempfile
import pytest

from core.router_loader import include_routers_from_directory


class MockModule:
    def __init__(self):
        self.router = APIRouter()
        @self.router.get("/test")
        def test():
            return {"hello": "world"}


class TestBasicScanning:
    def test_include_routers_from_directory_files(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()

        (api_dir / "module1.py").touch()
        (api_dir / "module2.py").touch()
        (api_dir / "norouter.py").touch()

        def mock_import(name, *args, **kwargs):
            mock = MockModule()
            if "norouter" in name:
                delattr(mock, "router")
            return mock

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(parent_router, "test.api", api_dir)

        assert len(parent_router.routes) > 0

    def test_include_routers_from_directory_subpackages(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "v1").mkdir()
        (api_dir / "v2").mkdir()
        (api_dir / "v1" / "__init__.py").touch()
        (api_dir / "v2" / "__init__.py").touch()

        def mock_import(name, *args, **kwargs):
            return MockModule()

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(parent_router, "test.api", api_dir)

        assert len(parent_router.routes) > 0

    def test_skips_init_py(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "__init__.py").touch()
        (api_dir / "test.py").touch()

        def mock_import(name, *args, **kwargs):
            if name.endswith(".__init__"):
                return type('MockEmpty', (), {})()
            return MockModule()

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(parent_router, "test.api", api_dir)

        assert len(parent_router.routes) > 0

    def test_skips_directory_without_init_py(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        subdir = api_dir / "noplugin"
        subdir.mkdir()

        (api_dir / "hasinit").mkdir()
        (api_dir / "hasinit" / "__init__.py").touch()

        def mock_import(name, *args, **kwargs):
            return MockModule()

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(parent_router, "test.api", api_dir)

        assert len(parent_router.routes) == 1

    def test_skip_empty_module_name(self, tmp_path):
        parent_router = APIRouter()

        not_py = tmp_path / "file.txt"
        not_py.write_text("not a python file")
        api_dir = tmp_path

        include_routers_from_directory(parent_router, "test", api_dir)

        assert len(parent_router.routes) == 0
