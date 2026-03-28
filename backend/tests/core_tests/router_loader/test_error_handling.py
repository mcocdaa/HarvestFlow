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


class TestErrorHandling:
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
