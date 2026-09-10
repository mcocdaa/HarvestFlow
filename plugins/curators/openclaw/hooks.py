# @file plugins/curators/openclaw/hooks.py
# @brief OpenClaw 审核器插件 hooks - 经窄钩子接管自动审核评分
# @create 2026-03-18

import logging

from core.hook_manager import hook_manager
from plugins.curators.openclaw.backend import get_curator

logger = logging.getLogger(__name__)


@hook_manager.hook("curator_manager_score_before")
def openclaw_curator_score(self, content):
    """OpenClaw 评分窄钩子：只接管评分步骤，校验与回写由 CuratorManager 模板负责

    返回 dict（含 score 键）即短路内置评分；评分异常时返回 None，
    自动回退内置评分，不阻断评估流程。

    Args:
        self: CuratorManager 实例
        content: 会话内容字典

    Returns:
        {"score", "is_high_value", "tags", "score_reasons"} 或 None（回退内置）
    """
    try:
        result = get_curator().evaluate(content)
    except Exception as e:
        logger.error(f"[OpenClawCurator] 评分失败: {e}", exc_info=True)
        return None
    logger.debug(f"[OpenClawCurator] 评分完成: {result.get('score')}")
    return result
