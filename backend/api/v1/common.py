# @file backend/api/v1/common.py
# @brief API 通用响应与错误辅助
# @create 2026-08-10

from fastapi import HTTPException


def ok(**data) -> dict:
    """成功响应：{"success": True, **data}"""
    return {"success": True, **data}


def not_found(detail: str) -> HTTPException:
    """404 异常辅助"""
    return HTTPException(404, detail=detail)


def bad_request(detail: str) -> HTTPException:
    """400 异常辅助"""
    return HTTPException(400, detail=detail)
