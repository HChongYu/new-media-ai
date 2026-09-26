"""
视觉阶段节点：
- extract_visual_points：把最终长文提炼为 3-5 个卡片知识点（含英文绘图提示词）
- generate_images：并行调用绘图模型生成配图
"""
import asyncio
import logging

from app.services.llm_service import get_llm_client
from app.services.image_service import generate_image
from app.services.prompt_service import render_prompt
from app.graph.state import ArticleState, STATUS_COMPLETED
from app.graph.utils import parse_json_array

logger = logging.getLogger(__name__)

VISUAL_POINT_COUNT = 5

# 不同平台的配图尺寸倾向（image_service 内部会再对齐具体模型支持的尺寸）
_IMAGE_SIZE = {
    "xiaohongshu": (1024, 1365),  # 竖版 3:4
    "wechat": (1024, 768),        # 横版 4:3
}


async def extract_visual_points(state: ArticleState) -> dict:
    """将 final_content 提炼为知识点，并为每个知识点生成英文绘图提示词"""
    llm = get_llm_client()

    prompt = await render_prompt(
        "visual_points",
        bucket_id=state.get("thread_id"),
        draft_title=state.get("draft_title", state.get("selected_topic", "")),
        final_content=state.get("final_content", "")[:3000],
        count=VISUAL_POINT_COUNT,
    )

    response = await llm.ainvoke(prompt)
    points = parse_json_array(response.content)

    if points is None:
        # 降级：无法解析时不阻断流程，用文章标题生成一个通用提示词
        logger.warning("视觉知识点 LLM 输出无法解析为 JSON，降级为单卡片")
        points = [
            {
                "point": state.get("draft_title", "技术要点"),
                "detail": "",
                "image_prompt": response.content[:500],
            }
        ]

    visual_points = [
        {
            "point": str(item.get("point", "")).strip(),
            "detail": str(item.get("detail", "")).strip(),
            "image_prompt": str(item.get("image_prompt", "")).strip(),
        }
        for item in points
        if isinstance(item, dict) and item.get("image_prompt")
    ][:VISUAL_POINT_COUNT]

    image_prompts = [item["image_prompt"] for item in visual_points]

    return {
        "visual_points": visual_points,
        "image_prompts": image_prompts,
    }


async def generate_images(state: ArticleState) -> dict:
    """
    并行生成配图。

    单张失败不影响其它图片（返回结果中过滤掉失败项）。
    """
    platform = state.get("platform") or "xiaohongshu"
    width, height = _IMAGE_SIZE.get(platform, _IMAGE_SIZE["xiaohongshu"])
    prompts = state.get("image_prompts", [])

    async def _safe_generate(index: int, prompt: str) -> str:
        try:
            return await generate_image(prompt=prompt, width=width, height=height)
        except Exception as exc:  # 单张失败降级为空串，后续过滤
            logger.warning("第 %d 张配图生成失败：%s", index + 1, exc)
            return ""

    results = await asyncio.gather(
        *[_safe_generate(i, prompt) for i, prompt in enumerate(prompts)]
    )
    image_urls = [url for url in results if url]

    return {
        "image_urls": image_urls,
        "current_status": STATUS_COMPLETED,
    }
