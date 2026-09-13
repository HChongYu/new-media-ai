"""
内容生成 LangGraph 工作流

流程：分析选题 -> 生成大纲 -> 撰写内容 -> 质量检查
"""
from typing import Any

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from app.services.llm_service import get_llm_client
from app.workflows.prompts import (
    CONTENT_OUTLINE_PROMPT,
    CONTENT_WRITING_PROMPT,
    CONTENT_QUALITY_CHECK_PROMPT,
)


class ContentState(TypedDict):
    topic_title: str
    topic_description: str
    platform: str
    tone: str
    length: str
    outline: str
    content: str
    title: str
    quality_passed: bool
    quality_feedback: str
    revision_count: int


async def analyze_topic(state: ContentState) -> dict:
    """分析选题，确定内容方向"""
    # 选题信息已在 state 中，直接传递给下一步
    return {}


async def generate_outline(state: ContentState) -> dict:
    """生成内容大纲"""
    llm = get_llm_client()

    length_guide = {
        "short": "500字以内",
        "medium": "500-1500字",
        "long": "1500字以上",
    }.get(state["length"], "500-1500字")

    prompt = CONTENT_OUTLINE_PROMPT.format(
        topic_title=state["topic_title"],
        topic_description=state["topic_description"],
        platform="小红书" if state["platform"] == "xiaohongshu" else "微信公众号",
        tone=state["tone"],
        length_guide=length_guide,
    )

    response = await llm.ainvoke(prompt)
    return {"outline": response.content}


async def write_content(state: ContentState) -> dict:
    """根据大纲撰写内容"""
    llm = get_llm_client()

    # 如果有质量反馈，加入提示中
    feedback_section = ""
    if state.get("quality_feedback"):
        feedback_section = f"\n\n上一版的问题（请针对性改进）：\n{state['quality_feedback']}"

    prompt = CONTENT_WRITING_PROMPT.format(
        topic_title=state["topic_title"],
        outline=state["outline"],
        platform="小红书" if state["platform"] == "xiaohongshu" else "微信公众号",
        tone=state["tone"],
        feedback=feedback_section,
    )

    response = await llm.ainvoke(prompt)

    # 从输出中提取标题和正文
    content_text = response.content
    title = state["topic_title"]

    # 尝试提取 Markdown 标题
    lines = content_text.strip().split("\n")
    if lines and lines[0].startswith("# "):
        title = lines[0].lstrip("# ").strip()
        content_text = "\n".join(lines[1:]).strip()

    return {"content": content_text, "title": title}


async def check_quality(state: ContentState) -> dict:
    """质量检查"""
    llm = get_llm_client()

    prompt = CONTENT_QUALITY_CHECK_PROMPT.format(
        topic_title=state["topic_title"],
        content=state["content"],
        platform="小红书" if state["platform"] == "xiaohongshu" else "微信公众号",
    )

    response = await llm.ainvoke(prompt)
    result = response.content.strip().upper()

    # 简单判断：如果包含 PASS 或 通过，则认为质量合格
    passed = "PASS" in result or "通过" in result

    # 如果已经修订过2次，强制通过
    if state.get("revision_count", 0) >= 2:
        passed = True

    return {
        "quality_passed": passed,
        "quality_feedback": "" if passed else response.content,
        "revision_count": state.get("revision_count", 0) + (0 if passed else 1),
    }


def should_revise(state: ContentState) -> str:
    """决定是否需要根据质量检查结果进行修改"""
    if state["quality_passed"]:
        return "end"
    return "revise"


def build_content_graph() -> StateGraph:
    """构建内容生成工作流图"""
    graph = StateGraph(ContentState)

    graph.add_node("analyze_topic", analyze_topic)
    graph.add_node("generate_outline", generate_outline)
    graph.add_node("write_content", write_content)
    graph.add_node("check_quality", check_quality)

    graph.add_edge(START, "analyze_topic")
    graph.add_edge("analyze_topic", "generate_outline")
    graph.add_edge("generate_outline", "write_content")
    graph.add_edge("write_content", "check_quality")

    # 质量检查后根据结果决定是结束还是重新修改
    graph.add_conditional_edges(
        "check_quality",
        should_revise,
        {
            "revise": "write_content",
            "end": END,
        },
    )

    return graph.compile()


content_graph = build_content_graph()


async def generate_content_workflow(
    topic_title: str,
    topic_description: str,
    platform: str = "xiaohongshu",
    tone: str = "professional",
    length: str = "medium",
) -> dict[str, Any]:
    """执行内容生成工作流"""
    initial_state: ContentState = {
        "topic_title": topic_title,
        "topic_description": topic_description,
        "platform": platform,
        "tone": tone,
        "length": length,
        "outline": "",
        "content": "",
        "title": topic_title,
        "quality_passed": False,
        "quality_feedback": "",
        "revision_count": 0,
    }

    result = await content_graph.ainvoke(initial_state)
    return {
        "title": result["title"],
        "content": result["content"],
    }
