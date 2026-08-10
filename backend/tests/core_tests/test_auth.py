# @file backend/tests/core_tests/test_auth.py
# @brief 鉴权模块测试
# @create 2026-08-10

import asyncio
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


def _run_async(coro):
    """Helper to run an async coroutine synchronously (project has no pytest-asyncio)."""
    return asyncio.run(coro)


class TestRequireApiKey:
    """测试 require_api_key 依赖函数"""

    def test_auth_disabled_when_key_empty(self, monkeypatch):
        """API key 为空时鉴权被禁用，所有请求放行"""
        from core import setting_manager
        from core.auth import require_api_key

        monkeypatch.setitem(setting_manager.config, "HARVESTFLOW_API_KEY", "")

        result = _run_async(require_api_key(None))
        assert result is None  # auth disabled, passes through

    def test_auth_rejects_missing_token(self, monkeypatch):
        """设置了 API key 后，无 token 的请求应返回 401"""
        from core import setting_manager
        from core.auth import require_api_key

        monkeypatch.setitem(setting_manager.config, "HARVESTFLOW_API_KEY", "test-secret")

        with pytest.raises(HTTPException) as exc_info:
            _run_async(require_api_key(None))
        assert exc_info.value.status_code == 401
        assert "Invalid or missing API key" in exc_info.value.detail

    def test_auth_rejects_wrong_key(self, monkeypatch):
        """设置了 API key 后，错误的 key 应返回 401"""
        from core import setting_manager
        from core.auth import require_api_key

        monkeypatch.setitem(setting_manager.config, "HARVESTFLOW_API_KEY", "test-secret")

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-key")

        with pytest.raises(HTTPException) as exc_info:
            _run_async(require_api_key(creds))
        assert exc_info.value.status_code == 401

    def test_auth_accepts_correct_key(self, monkeypatch):
        """设置了 API key 后，正确的 key 应放行"""
        from core import setting_manager
        from core.auth import require_api_key

        monkeypatch.setitem(setting_manager.config, "HARVESTFLOW_API_KEY", "test-secret")

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-secret")

        result = _run_async(require_api_key(creds))
        assert result is None  # passes through
