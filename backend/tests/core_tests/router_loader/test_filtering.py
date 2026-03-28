import os
import sys
from fastapi import APIRouter
from pathlib import Path
import pytest

from core.router_loader import include_routers_from_directory


class MockModule:
    def __init__(self):
        self.router = APIRouter()
        @self.router.get("/test")
        def test():
            return {"hello": "world"}


class TestFiltering:
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
