"""
图片生成服务

支持多种图片生成后端：OpenAI DALL-E / Stability AI / 本地模型
"""
import uuid
from pathlib import Path

import httpx

from app.config import settings


UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 768,
) -> str:
    """
    生成图片，返回图片 URL

    当前实现：调用 OpenAI DALL-E API
    可扩展：替换为 Stability AI 或其他图片生成服务
    """
    provider = settings.IMAGE_PROVIDER.lower()

    if provider == "openai":
        return await _generate_with_openai(prompt, width, height)
    elif provider == "local":
        return await _generate_with_local(prompt, width, height)
    else:
        # 默认使用模拟模式（开发环境）
        return await _generate_mock(prompt, width, height)


async def _generate_with_openai(
    prompt: str, width: int, height: int
) -> str:
    """使用 OpenAI DALL-E 生成图片"""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.LLM_API_KEY)

    # DALL-E 3 只支持特定尺寸
    size = "1024x1024"
    if width > height:
        size = "1792x1024"
    elif height > width:
        size = "1024x1792"

    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url

    # 下载图片保存到本地
    filename = f"{uuid.uuid4().hex}.png"
    file_path = UPLOAD_DIR / filename

    async with httpx.AsyncClient() as http_client:
        img_response = await http_client.get(image_url)
        file_path.write_bytes(img_response.content)

    return f"/uploads/images/{filename}"


async def _generate_with_local(
    prompt: str, width: int, height: int
) -> str:
    """使用本地模型生成图片（预留接口）"""
    # TODO: 对接本地 Stable Diffusion 等模型
    raise NotImplementedError("本地图片生成模型尚未实现")


async def _generate_mock(
    prompt: str, width: int, height: int
) -> str:
    """模拟图片生成（开发环境使用）"""
    # 生成一个占位图片 URL
    filename = f"{uuid.uuid4().hex}.png"

    # 创建一个简单的占位图
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (width, height), color=(66, 133, 244))
        draw = ImageDraw.Draw(img)

        # 在图片上绘制提示词摘要
        text = prompt[:100] + "..." if len(prompt) > 100 else prompt
        # 简单居中绘制文字
        draw.text(
            (width // 2 - 100, height // 2 - 20),
            text[:50],
            fill=(255, 255, 255),
        )

        file_path = UPLOAD_DIR / filename
        img.save(str(file_path))
    except ImportError:
        # 如果没有 PIL，创建一个空文件
        file_path = UPLOAD_DIR / filename
        file_path.write_bytes(b"")

    return f"/uploads/images/{filename}"
