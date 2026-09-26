"""plan_topics：根据 topic_direction 调用 LLM 生成备选选题"""
import logging

from app.services.llm_service import get_llm_client
from app.services.prompt_service import render_prompt
from app.graph.prompts import PLATFORM_DESC
from app.graph.state import ArticleState, STATUS_PLANNING
from app.graph.utils import parse_json_array

logger = logging.getLogger(__name__)

TOPIC_COUNT = 5


async def plan_topics(state: ArticleState) -> dict:
    """生成 3-5 个技术干货选题，写入 proposed_topics"""
    llm = get_llm_client()

    platform = state.get("platform") or "xiaohongshu"
    prompt = await render_prompt(
        "topic_plan",
        bucket_id=state.get("thread_id"),
        topic_direction=state["topic_direction"],
        count=TOPIC_COUNT,
        platform_desc=PLATFORM_DESC.get(platform, "小红书 / 微信公众号"),
    )

    response = await llm.ainvoke(prompt)
    raw = response.content

    topics = parse_json_array(raw)
    if topics is None:
        # JSON 解析失败时降级：把原始输出作为单个选题，避免流程中断
        logger.warning("选题 LLM 输出无法解析为 JSON，降级为单条文本选题")
        topics = [
            {
                "title": state["topic_direction"][:30] or "AI 生成选题",
                "description": raw[:500],
                "category": "",
                "tags": [],
            }
        ]

    # 规整字段，保证结构一致
    normalized = [
        {
            "title": str(item.get("title", "")).strip() or "未命名选题",
            "description": str(item.get("description", "")).strip(),
            "category": str(item.get("category", "")).strip(),
            "tags": item.get("tags", []) if isinstance(item.get("tags"), list) else [],
        }
        for item in topics
        if isinstance(item, dict)
    ]

    return {
        "proposed_topics": normalized[:TOPIC_COUNT],
        "current_status": STATUS_PLANNING,
    }
