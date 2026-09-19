"""
人工介入节点（虚拟节点，仅承载 interrupt）

关键约束（LangGraph interrupt 语义）：
- interrupt() 会让当前节点暂停；用 Command(resume=value) 恢复时，
  当前节点会从头重新执行，interrupt() 的返回值即 resume 传入的数据。
- 因此这类节点必须保持“无副作用、幂等”，只负责把人工输入写回 state，
  不要在这里调用 LLM 或写数据库。
"""
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from app.graph.state import (
    ArticleState,
    INTERRUPT_SELECT,
    INTERRUPT_REVIEW,
    STATUS_WRITING,
)


async def human_select(state: ArticleState) -> dict:
    """第一次中断：暂停在选题之后，等待人工选择 selected_topic"""
    selected_topic = interrupt(
        {
            "type": INTERRUPT_SELECT,
            "message": "请从备选选题中选择一个",
            "topics": state.get("proposed_topics", []),
        }
    )

    return {
        "selected_topic": selected_topic,
        "current_status": STATUS_WRITING,
        "messages": [HumanMessage(content=f"人工选择选题：{selected_topic}")],
    }


async def human_review(state: ArticleState) -> dict:
    """
    第二次中断：草稿生成后暂停，等待人工审核。

    resume 数据契约：
        {"status": "approve" | "reject", "feedback": "修改意见（驳回时必填）"}
    """
    review = interrupt(
        {
            "type": INTERRUPT_REVIEW,
            "message": "请审核文章草稿：approve 通过，reject 退回重写",
            "draft_title": state.get("draft_title", ""),
            "draft_content": state.get("draft_content", ""),
            "revision_count": state.get("revision_count", 0),
        }
    )

    # 容错：允许直接传字符串
    if isinstance(review, str):
        status = review
        feedback = ""
    else:
        status = (review or {}).get("status", "").lower()
        feedback = (review or {}).get("feedback", "")

    if status == "approve":
        return {
            "review_decision": "approve",
            "human_feedback": "",
            "final_content": state.get("draft_content", ""),
        }

    # reject / 其它值一律视为退回重写
    return {
        "review_decision": "reject",
        "human_feedback": feedback,
        "final_content": "",
        "messages": [HumanMessage(content=f"人工驳回并要求修改：{feedback}")],
    }
