"""
选题生成 LangGraph 工作流

流程：分析需求 -> 生成选题 -> 格式化输出
"""
import json
from typing import Any

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from app.services.llm_service import get_llm_client
from app.workflows.prompts import TOPIC_GENERATION_PROMPT


class TopicState(TypedDict):
    keywords: list[str]
    category: str
    target_audience: str
    content_style: str
    count: int
    raw_output: str
    topics: list[dict[str, Any]]


async def analyze_requirements(state: TopicState) -> dict:
    """分析选题需求，确定方向"""
    # 这里可以对关键词进行扩展或分析，目前直接传递给下一步
    return {}


async def generate_topics(state: TopicState) -> dict:
    """调用 LLM 生成选题"""
    llm = get_llm_client()

    prompt = TOPIC_GENERATION_PROMPT.format(
        keywords="、".join(state["keywords"]) if state["keywords"] else "AI编程、AI应用开发、AI训练师",
        category=state["category"] or "AI技术培训",
        target_audience=state["target_audience"] or "对AI编程感兴趣的职场人和创业者",
        content_style=state["content_style"] or "专业但通俗易懂，结合实战案例",
        count=state["count"] or 5,
    )

    response = await llm.ainvoke(prompt)
    return {"raw_output": response.content}


async def format_topics(state: TopicState) -> dict:
    """解析 LLM 输出，格式化为结构化选题"""
    raw = state["raw_output"]

    # 尝试从 LLM 输出中提取 JSON
    try:
        # 尝试找到 JSON 块
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            topics = json.loads(raw[start:end])
        else:
            # 如果无法解析，返回原始文本作为单个选题
            topics = [
                {
                    "title": "AI生成的选题",
                    "description": raw,
                    "category": state.get("category", ""),
                    "tags": [],
                }
            ]
    except json.JSONDecodeError:
        topics = [
            {
                "title": "AI生成的选题",
                "description": raw,
                "category": state.get("category", ""),
                "tags": [],
            }
        ]

    return {"topics": topics}


def build_topic_graph() -> StateGraph:
    """构建选题生成工作流图"""
    graph = StateGraph(TopicState)

    graph.add_node("analyze_requirements", analyze_requirements)
    graph.add_node("generate_topics", generate_topics)
    graph.add_node("format_topics", format_topics)

    graph.add_edge(START, "analyze_requirements")
    graph.add_edge("analyze_requirements", "generate_topics")
    graph.add_edge("generate_topics", "format_topics")
    graph.add_edge("format_topics", END)

    return graph.compile()


topic_graph = build_topic_graph()


async def generate_topics_workflow(
    keywords: list[str] | None = None,
    category: str | None = None,
    target_audience: str | None = None,
    content_style: str | None = None,
    count: int = 5,
) -> list[dict[str, Any]]:
    """执行选题生成工作流"""
    initial_state: TopicState = {
        "keywords": keywords or [],
        "category": category or "",
        "target_audience": target_audience or "",
        "content_style": content_style or "",
        "count": count,
        "raw_output": "",
        "topics": [],
    }

    result = await topic_graph.ainvoke(initial_state)
    return result["topics"]
