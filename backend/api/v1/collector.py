# @file backend/api/v1/collector.py
# @brief Collector API 路由
# @create 2026-03-22

from fastapi import APIRouter, Request
from typing import Optional
from pydantic import BaseModel
from managers.collector_manager import collector_manager
from api.v1.common import ok, bad_request


class ContentImportRequest(BaseModel):
    content: str
    filename: Optional[str] = "upload.json"


router = APIRouter()


@router.post("/collector/upload")
async def upload_dataset(request: Request) -> dict:
    """接收外部通用格式数据集 (OpenAI Messages, ShareGPT, Alpaca, HarvestFlow) 流式导入"""
    body = await request.body()
    content_str = body.decode("utf-8", errors="ignore")
    filename = request.headers.get("x-filename", "upload.json")
    result = collector_manager.import_from_text(content_str, filename=filename)
    return ok(**result)


@router.post("/collector/import-content")
def import_content(request: ContentImportRequest) -> dict:
    """通过 JSON 请求体直接导入会话文本"""
    result = collector_manager.import_from_text(request.content, filename=request.filename or "upload.json")
    return ok(**result)


@router.get("/collector/scan")
def scan_folder(folder_path: Optional[str] = None) -> dict:
    files = collector_manager.scan_folder(folder_path)
    return {"folder_path": folder_path, "files_found": len(files), "files": files}


@router.post("/collector/import")
def import_session(file_path: str) -> dict:
    session_id = collector_manager.import_session(file_path)
    if not session_id:
        raise bad_request("Failed to import session")
    return ok(session_id=session_id)


@router.post("/collector/import-all")
def import_all(folder_path: Optional[str] = None) -> dict:
    result = collector_manager.import_all(folder_path)
    return result


@router.post("/collector/watch-folder")
def add_watch_folder(folder_path: str) -> dict:
    collector_manager.add_watch_folder(folder_path)
    return ok(watch_folders=collector_manager.watch_folders)


@router.delete("/collector/watch-folder")
def remove_watch_folder(folder_path: str) -> dict:
    collector_manager.remove_watch_folder(folder_path)
    return ok(watch_folders=collector_manager.watch_folders)


@router.get("/collector/watch-folders")
def get_watch_folders() -> dict:
    return {"watch_folders": collector_manager.watch_folders}


@router.get("/collector/watch-state")
def get_watch_state() -> dict:
    """监听状态：开关、运行中、间隔、目录与各目录最近一次导入结果"""
    return collector_manager.get_watch_state()


@router.post("/collector/watch-start")
def start_watching() -> dict:
    return collector_manager.set_watch_enabled(True)


@router.post("/collector/watch-stop")
def stop_watching() -> dict:
    return collector_manager.set_watch_enabled(False)


@router.post("/collector/watch-run")
def watch_run_now() -> dict:
    """立即对所有监听目录执行一次导入"""
    return {"results": collector_manager.watch_run_once()}
