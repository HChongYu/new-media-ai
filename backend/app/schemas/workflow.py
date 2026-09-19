"""统一图文工作流的请求 / 响应 Schema"""
from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowStartRequest(BaseModel):
    topic_direction: str = Field(..., min_length=1, max_length=500, description="内容方向")
    platform: Literal["xiaohongshu", "wechat"] = "xiaohongshu"


class WorkflowResumeRequest(BaseModel):
    # select_topic：人工选题；review：人工审稿
    action: Literal["select_topic", "review"]
    # action=select_topic 时：选中的标题
    data: str | None = None
    # action=review 时：approve / reject
    status: Literal["approve", "reject"] | None = None
    # action=review 且 reject 时的修改意见
    feedback: str | None = None


class WorkflowProjectResponse(BaseModel):
    """content_projects 业务表视图"""

    id: str
    thread_id: str
    topic_direction: str
    topic: str
    platform: str
    status: str
    revision_count: int
    article_content: dict[str, Any] | None = None
    image_assets: list[Any] | None = None
    created_at: str
    updated_at: str


class WorkflowRunResponse(BaseModel):
    """工作流运行状态（业务表 + 图状态快照）"""

    project: WorkflowProjectResponse
    # human_select / human_review / None（已完成）
    next_step: str | None = None
    # 当前中断点返回给前端的载荷（备选选题 / 待审草稿）
    interrupt: dict[str, Any] | None = None
    completed: bool = False

    # 图状态中的关键数据（便于前端直接渲染）
    proposed_topics: list[dict[str, Any]] = []
    selected_topic: str = ""
    draft_title: str = ""
    draft_content: str = ""
    final_content: str = ""
    visual_points: list[dict[str, Any]] = []
    image_urls: list[str] = []
    revision_count: int = 0
