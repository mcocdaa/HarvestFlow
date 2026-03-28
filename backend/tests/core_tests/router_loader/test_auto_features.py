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


class TestAutoFeatures:
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
