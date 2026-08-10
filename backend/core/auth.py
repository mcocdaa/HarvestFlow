# @file backend/core/auth.py
# @brief API 鉴权 - Bearer token 验证
# @create 2026-08-10

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core import setting_manager

bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    """校验 API key（未配置 key 时默认放行）"""
    expected = setting_manager.get("HARVESTFLOW_API_KEY")
    if not expected:
        return  # auth disabled
    if credentials is None or credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
