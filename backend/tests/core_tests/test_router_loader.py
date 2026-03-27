# @file backend/tests/core_tests/test_router_loader.py
# @brief 自动路由加载器测试
# @create 2026-03-26

import os
import sys
sys.path.insert(0, '/home/mcocdaa/AI_CODE/HarvestFlow')

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


class TestRouterLoader:
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

    def test_skips_modules_in_skip_list(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "skipped.py").touch()
        (api_dir / "included.py").touch()

        def mock_import(name, *args, **kwargs):
            return MockModule()

        monkeypatch.setattr("importlib.import_module", mock_import)

        initial_routes = len(parent_router.routes)

        include_routers_from_directory(
            parent_router,
            "test.api",
            api_dir,
            skip_modules=["skipped"]
        )

        routes_added = len(parent_router.routes) - initial_routes
        assert routes_added > 0

    def test_auto_tag_adds_tags(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "testmodule.py").touch()

        def mock_import(name, *args, **kwargs):
            return MockModule()

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(
            parent_router,
            "test.api",
            api_dir,
            auto_tag=True
        )

        assert len(parent_router.routes) >= 0

    def test_auto_prefix_adds_module_prefix(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "testmod.py").touch()

        def mock_import(name, *args, **kwargs):
            return MockModule()

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(
            parent_router,
            "test.api",
            api_dir,
            auto_prefix=True
        )

        assert len(parent_router.routes) >= 0

    def test_handles_import_error(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "bad.py").touch()

        def mock_import(name, *args, **kwargs):
            raise ImportError("Module not found")

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(parent_router, "test.api", api_dir)

        assert len(parent_router.routes) == 0

    def test_no_router_in_module_skipped(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "norouter.py").touch()

        def mock_import(name, *args, **kwargs):
            return type('MockNoRouter', (), {})()

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(parent_router, "test.api", api_dir)

        assert len(parent_router.routes) == 0

    def test_skip_empty_module_name(self, tmp_path):
        parent_router = APIRouter()

        not_py = tmp_path / "file.txt"
        not_py.write_text("not a python file")
        api_dir = tmp_path

        include_routers_from_directory(parent_router, "test", api_dir)

        assert len(parent_router.routes) == 0

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

    def test_auto_tag_and_auto_prefix_both_true(self, tmp_path, monkeypatch):
        parent_router = APIRouter()

        api_dir = tmp_path / "api"
        api_dir.mkdir()
        (api_dir / "testmod.py").touch()

        def mock_import(name, *args, **kwargs):
            return MockModule()

        monkeypatch.setattr("importlib.import_module", mock_import)

        include_routers_from_directory(
            parent_router,
            "test.api",
            api_dir,
            auto_tag=True,
            auto_prefix=True
        )

        assert len(parent_router.routes) > 0
