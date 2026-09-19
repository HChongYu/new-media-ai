"""
全局状态 ArticleState

在工作流的所有节点之间传递。字段语义分两类：
- 覆盖型（单值快照）：如 selected_topic / review_decision，直接赋值覆盖；
- 追加型（Annotated + operator.add）：image_urls / messages，
  用于并行扇出汇总与对话历史累积。
"""
import operator
from typing import Annotated, Any

from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class ArticleState(TypedDict, total=False):
    # ----------------------------------------------------------
    # 输入信息
    # ----------------------------------------------------------
    topic_direction: str  # 用户输入的初始方向，如 "LangChain 新特性"
    platform: str  # xiaohongshu / wechat

    # ----------------------------------------------------------
    # 选题阶段
    # ----------------------------------------------------------
    # [{"title", "description", "category", "tags"}]
    proposed_topics: list[dict[str, Any]]
    selected_topic: str  # 人工最终选择的标题

    # ----------------------------------------------------------
    # 写作阶段
    # ----------------------------------------------------------
    draft_title: str
    draft_content: str
    human_feedback: str  # 人工审核的修改意见
    review_decision: str  # approve / reject
    final_content: str  # 通过审核后的最终文案

    # ----------------------------------------------------------
    # 图片生成阶段
    # ----------------------------------------------------------
    # [{"point": 知识点短文案, "detail": 讲解, "image_prompt": 英文绘图提示词}]
    visual_points: list[dict[str, str]]
    image_prompts: Annotated[list[str], operator.add]
    image_urls: Annotated[list[str], operator.add]  # 并行绘图结果汇总

    # ----------------------------------------------------------
    # 流程控制
    # ----------------------------------------------------------
    revision_count: int
    current_status: str  # planning / writing / reviewing / completed
    messages: Annotated[list[BaseMessage], operator.add]


# 状态机对外暴露的状态取值
STATUS_PLANNING = "planning"
STATUS_WRITING = "writing"
STATUS_REVIEWING = "reviewing"
STATUS_COMPLETED = "completed"

# 两次人工中断的类型标识（放在 interrupt payload 里，前端据此渲染）
INTERRUPT_SELECT = "human_select"
INTERRUPT_REVIEW = "human_review"

# 审核决策
DECISION_APPROVE = "approve"
DECISION_REJECT = "reject"
