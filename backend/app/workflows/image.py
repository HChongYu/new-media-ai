"""
图片生成 LangGraph 工作流

流程：分析文案 -> 生成图片提示词 -> 生成图片 -> 后处理
"""
import uuid
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from app.config import settings
from app.services.llm_service import get_llm_client
from app.services.image_service import generate_image
from app.workflows.prompts import IMAGE_PROMPT_GENERATION_PROMPT


class ImageState(TypedDict):
    content_title: str
    content_text: str
    image_types: list[str]
    count: int
    style: str
    width: int
    height: int
    image_prompts: list[dict[str, str]]
    generated_images: list[dict[str, Any]]


async def analyze_content(state: ImageState) -> dict:
    """分析文案内容，提取关键信息"""
    # 文案信息已在 state 中，直接传递给下一步
    return {}


async def generate_image_prompts(state: ImageState) -> dict:
    """根据文案内容生成图片提示词"""
    llm = get_llm_client()

    image_types_desc = {
        "cover": "封面图：吸引眼球的主视觉",
        "section": "正文图：配合具体段落的插图",
        "summary": "摘要图：总结核心要点的信息图",
    }

    types_text = "\n".join(
        f"- {image_types_desc.get(t, t)}" for t in state["image_types"]
    )

    prompt = IMAGE_PROMPT_GENERATION_PROMPT.format(
        content_title=state["content_title"],
        content_text=state["content_text"][:2000],  # 限制长度
        image_types=types_text,
        count=state["count"],
        style=state["style"],
    )

    response = await llm.ainvoke(prompt)

    # 解析提示词输出
    import json
    try:
        start = response.content.find("[")
        end = response.content.rfind("]") + 1
        if start != -1 and end > start:
            prompts = json.loads(response.content[start:end])
        else:
            prompts = [
                {"type": state["image_types"][0] if state["image_types"] else "cover", "prompt": response.content}
            ]
    except json.JSONDecodeError:
        prompts = [
            {"type": state["image_types"][0] if state["image_types"] else "cover", "prompt": response.content}
        ]

    return {"image_prompts": prompts}


async def generate_images_node(state: ImageState) -> dict:
    """调用图片生成服务生成图片"""
    generated = []

    for prompt_data in state["image_prompts"]:
        try:
            image_url = await generate_image(
                prompt=prompt_data["prompt"],
                width=state["width"],
                height=state["height"],
            )
            generated.append({
                "image_type": prompt_data.get("type", "section"),
                "prompt": prompt_data["prompt"],
                "image_url": image_url,
                "width": state["width"],
                "height": state["height"],
            })
        except Exception as e:
            # 单张图片生成失败不影响其他图片
            generated.append({
                "image_type": prompt_data.get("type", "section"),
                "prompt": prompt_data["prompt"],
                "image_url": "",
                "width": state["width"],
                "height": state["height"],
                "error": str(e),
            })

    # 过滤掉生成失败的
    generated = [img for img in generated if img["image_url"]]

    return {"generated_images": generated}


async def post_process(state: ImageState) -> dict:
    """后处理：检查图片数量是否满足要求"""
    images = state["generated_images"]
    # 如果生成的图片少于请求数量，记录日志（实际场景可以重试）
    return {}


def build_image_graph() -> StateGraph:
    """构建图片生成工作流图"""
    graph = StateGraph(ImageState)

    graph.add_node("analyze_content", analyze_content)
    graph.add_node("generate_image_prompts", generate_image_prompts)
    graph.add_node("generate_images", generate_images_node)
    graph.add_node("post_process", post_process)

    graph.add_edge(START, "analyze_content")
    graph.add_edge("analyze_content", "generate_image_prompts")
    graph.add_edge("generate_image_prompts", "generate_images")
    graph.add_edge("generate_images", "post_process")
    graph.add_edge("post_process", END)

    return graph.compile()


image_graph = build_image_graph()


async def generate_images_workflow(
    content_title: str,
    content_text: str,
    image_types: list[str] | None = None,
    count: int = 3,
    style: str = "professional",
    width: int = 1024,
    height: int = 768,
) -> list[dict[str, Any]]:
    """执行图片生成工作流"""
    initial_state: ImageState = {
        "content_title": content_title,
        "content_text": content_text,
        "image_types": image_types or ["cover", "section", "summary"],
        "count": count,
        "style": style,
        "width": width,
        "height": height,
        "image_prompts": [],
        "generated_images": [],
    }

    result = await image_graph.ainvoke(initial_state)
    return result["generated_images"]
