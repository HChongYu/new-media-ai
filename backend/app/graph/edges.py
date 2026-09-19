"""条件路由：人工审核后决定前进到视觉阶段还是回退重写"""
from app.graph.state import ArticleState, DECISION_APPROVE, DECISION_REJECT


def route_after_review(state: ArticleState) -> str:
    """
    human_review 之后的条件边：

    - approve -> extract_visual_points（进入图片阶段）
    - reject  -> generate_draft（带着修改意见回环重写）
    """
    decision = state.get("review_decision", "")
    if decision == DECISION_APPROVE:
        return DECISION_APPROVE
    # 任何异常状态下默认退回重写，避免流程卡死在审核点
    return DECISION_REJECT
