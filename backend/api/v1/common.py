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


def raise_from_result(result: dict, not_found_detail: str = "Resource not found") -> dict:
    """统一结果校验：空结果抛 404，含 error 抛 400，否则原样返回

    Args:
        result: Manager 层返回的结果字典
        not_found_detail: 结果为空时的 404 文案

    Returns:
        原样透传的 result
    """
    if not result:
        raise not_found(not_found_detail)
    if "error" in result:
        raise bad_request(result["error"])
    return result
