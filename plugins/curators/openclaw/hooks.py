# @file plugins/curators/openclaw/hooks.py
# @brief OpenClaw 审核器插件 hooks - 短路接管自动审核评分
# @create 2026-08-11

import logging

from core import database_manager
from core.constants import SessionStatus
from core.hook_manager import hook_manager
from managers.session_manager import session_manager
from plugins.curators.openclaw.backend import get_curator, HIGH_VALUE_SCORE_THRESHOLD

logger = logging.getLogger(__name__)


@hook_manager.hook("curator_manager_evaluate_before")
def openclaw_curator_evaluate_before(self, session_id):
    """OpenClaw 审核器短路钩子：接管自动审核评分

    前置校验与错误文案与内置 CuratorManager.evaluate_session 逐字一致
    （api/v1/curator.py 依赖这些文案返回 404/409）。
    评分异常时返回 None 不短路，自动回退内置评分。

    Args:
        self: CuratorManager 实例
        session_id: 会话 ID

    Returns:
        评分结果 dict（短路），或 None（回退内置）
    """
    if not self.enabled:
        return {"session_id": session_id, "error": "curator disabled"}

    session = session_manager.get_session(session_id)
    if not session:
        return {"session_id": session_id, "error": "session not found"}

    if session.get("status") != SessionStatus.RAW.value:
        return {"session_id": session_id, "error": "session is not in raw status"}

    content = session.get("content")
    if not content:
        return {"session_id": session_id, "error": "content not found"}

    try:
        result = get_curator().evaluate(content)
    except Exception as e:
        logger.error(f"[OpenClawCurator] 评分失败: {e}", exc_info=True)
        return None

    session_manager.update_session(session_id, {
        "quality_auto_score": result["score"],
        "tags": result["tags"],
        "tools_used": content.get("tools_used", []),
        "status": SessionStatus.CURATED.value,
    })

    auto_approved = False
    if result["is_high_value"]:
        database_manager.session_review_apply(
            session_id, SessionStatus.APPROVED.value, result["score"],
            "auto_approve",
            f"score {result['score']} >= threshold {HIGH_VALUE_SCORE_THRESHOLD}"
        )
        auto_approved = True

    return {
        "session_id": session_id,
        "score": result["score"],
        "is_high_value": result["is_high_value"],
        "tags": result["tags"],
        "tools_used": content.get("tools_used", []),
        "auto_approved": auto_approved,
        "score_reasons": result.get("score_reasons", []),
    }
