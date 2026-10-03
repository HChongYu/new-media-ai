"""generate_draft：根据 selected_topic 撰写技术长文；驳回后带反馈重写"""
import logging

from app.services.llm_service import get_llm_client
from app.services.prompt_service import render_prompt
from app.graph.fallbacks import fallback_draft
from app.graph.prompts import PLATFORM_DESC, PLATFORM_STYLE
from app.graph.state import ArticleState, STATUS_WRITING

logger = logging.getLogger(__name__)


async def generate_draft(state: ArticleState) -> dict:
    """
    撰写（或基于 human_feedback 重写）文章草稿。

    重入语义：被人工驳回后，条件边会回到本节点；
    此时 state.human_feedback 中有修改意见，revision_count 加 1。
    """
    llm = get_llm_client()

    platform = state.get("platform") or "xiaohongshu"
    feedback = state.get("human_feedback", "").strip()
    feedback_section = ""
    if feedback:
        feedback_section = (
            "\n**上一版的修改意见（请逐条针对性改进，不要复述意见本身）**：\n"
            f"{feedback}\n"
        )

    prompt = await render_prompt(
        "draft_writing",
        bucket_id=state.get("thread_id"),
        selected_topic=state["selected_topic"],
        platform_desc=PLATFORM_DESC.get(platform, "小红书"),
        platform_style=PLATFORM_STYLE.get(platform, PLATFORM_STYLE["xiaohongshu"]),
        feedback_section=feedback_section,
    )

    revision_count = state.get("revision_count", 0)
    if feedback:
        revision_count += 1

    try:
        response = await llm.ainvoke(prompt)
        content_text = response.content
    except Exception as exc:
        # 主备模型全部失败 / 熔断：兜底模板文章，流程继续到人工审核
        logger.error("撰稿节点 LLM 调用失败，启用兜底文章模板：%s", exc)
        title, content_text = fallback_draft(state["selected_topic"])
        return {
            "draft_title": title,
            "draft_content": content_text,
            "revision_count": revision_count,
            "current_status": STATUS_WRITING,
        }

    # 提取 Markdown 首行标题（与旧版内容工作流保持一致的约定）
    title = state["selected_topic"]
    lines = content_text.strip().split("\n")
    if lines and lines[0].startswith("# "):
        title = lines[0].lstrip("# ").strip()
        content_text = "\n".join(lines[1:]).strip()

    return {
        "draft_title": title,
        "draft_content": content_text,
        "revision_count": revision_count,
        "current_status": STATUS_WRITING,
    }
