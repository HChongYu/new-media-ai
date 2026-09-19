"""
工作流运行器：对 FastAPI 层暴露极简的 start / resume / snapshot 语义

- start_workflow：创建 thread 并跑到第一次 interrupt（选题完成，暂停）
- resume_workflow：携带人工输入恢复执行，跑到下一次 interrupt 或结束
- get_snapshot：读取当前状态（不驱动执行）
"""
from dataclasses import dataclass, field
from typing import Any

from langgraph.types import Command

from app.graph.state import (
    STATUS_PLANNING,
    INTERRUPT_SELECT,
    INTERRUPT_REVIEW,
)
from app.graph.workflow import get_workflow


@dataclass
class WorkflowSnapshot:
    """给接入层使用的标准化快照"""

    thread_id: str
    next_step: str | None  # human_select / human_review / None（已结束）
    interrupt: dict[str, Any] | None  # 当前中断点的 payload
    values: dict[str, Any] = field(default_factory=dict)
    found: bool = True

    @property
    def completed(self) -> bool:
        return self.found and self.next_step is None


def _thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


async def get_snapshot(thread_id: str) -> WorkflowSnapshot:
    """读取线程当前状态；线程不存在时返回 found=False"""
    graph = get_workflow()
    snap = await graph.aget_state(_thread_config(thread_id))

    # 不存在的线程：values 为空且没有待执行节点
    if not snap.values and not snap.next:
        return WorkflowSnapshot(
            thread_id=thread_id, next_step=None, interrupt=None, found=False
        )

    interrupt_payload = None
    for task in snap.tasks:
        if task.interrupts:
            payload = task.interrupts[0].value
            if isinstance(payload, dict):
                interrupt_payload = payload
                break

    # next_step 优先取 interrupt payload 中的业务类型
    next_step = (
        interrupt_payload.get("type")
        if interrupt_payload
        else (snap.next[0] if snap.next else None)
    )

    return WorkflowSnapshot(
        thread_id=thread_id,
        next_step=next_step,
        interrupt=interrupt_payload,
        values=dict(snap.values),
    )


async def start_workflow(
    thread_id: str, topic_direction: str, platform: str = "xiaohongshu"
) -> WorkflowSnapshot:
    """启动工作流：运行 plan_topics 后停在 human_select"""
    graph = get_workflow()

    initial_state = {
        "topic_direction": topic_direction,
        "platform": platform,
        "proposed_topics": [],
        "selected_topic": "",
        "draft_title": "",
        "draft_content": "",
        "human_feedback": "",
        "review_decision": "",
        "final_content": "",
        "visual_points": [],
        "image_prompts": [],
        "image_urls": [],
        "revision_count": 0,
        "current_status": STATUS_PLANNING,
        "messages": [],
    }

    await graph.ainvoke(initial_state, _thread_config(thread_id))
    return await get_snapshot(thread_id)


async def resume_workflow(thread_id: str, resume_value: Any) -> WorkflowSnapshot:
    """
    恢复工作流。

    resume_value 契约：
    - human_select：直接传选中的选题字符串
    - human_review：传 {"status": "approve"/"reject", "feedback": "..."}
    """
    graph = get_workflow()
    await graph.ainvoke(
        Command(resume=resume_value),
        _thread_config(thread_id),
    )
    return await get_snapshot(thread_id)


def expected_action(next_step: str | None) -> str | None:
    """根据当前中断点，返回期望的 resume action"""
    if next_step == INTERRUPT_SELECT:
        return "select_topic"
    if next_step == INTERRUPT_REVIEW:
        return "review"
    return None
