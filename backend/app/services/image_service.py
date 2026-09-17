"""
图片生成服务

支持多种图片生成后端：商汤 SenseNova / OpenAI DALL-E / 本地 Stable Diffusion WebUI / 模拟模式
"""
import base64
import math
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

    通过 IMAGE_PROVIDER 切换后端：sensenova / openai / local / mock
    """
    provider = settings.IMAGE_PROVIDER.lower()

    if provider == "sensenova":
        return await _generate_with_sensenova(prompt, width, height)
    elif provider == "openai":
        return await _generate_with_openai(prompt, width, height)
    elif provider == "local":
        return await _generate_with_local(prompt, width, height)
    else:
        # 默认使用模拟模式（开发环境）
        return await _generate_mock(prompt, width, height)


# SenseNova U1 Fast 仅支持以下 11 种固定尺寸（宽, 高）
_SENSENOVA_SIZES = [
    (1664, 2496),   # 2:3 竖版
    (2496, 1664),   # 3:2 横版
    (1760, 2368),   # 3:4 竖版
    (2368, 1760),   # 4:3 横版
    (1824, 2272),   # 4:5 竖版
    (2272, 1824),   # 5:4 横版
    (2048, 2048),   # 1:1
    (2752, 1536),   # 16:9 横版
    (1536, 2752),   # 9:16 竖版
    (3072, 1376),   # 21:9 超宽横版
    (1344, 3136),   # 9:21 超长竖版
]


def _pick_sensenova_size(width: int, height: int) -> str:
    """从 SenseNova 支持的固定尺寸中，选择与目标宽高比最接近的一个"""
    target_ratio = width / height
    best_w, best_h = min(
        _SENSENOVA_SIZES,
        # 用对数比值衡量宽高比差异，横竖方向判断对称
        key=lambda s: abs(math.log((s[0] / s[1]) / target_ratio)),
    )
    return f"{best_w}x{best_h}"


async def _download_to_local(image_url: str) -> str:
    """下载远程图片到本地上传目录，返回可访问的相对 URL"""
    filename = f"{uuid.uuid4().hex}.png"
    file_path = UPLOAD_DIR / filename

    async with httpx.AsyncClient(timeout=120.0) as http_client:
        img_response = await http_client.get(image_url)
        img_response.raise_for_status()
        file_path.write_bytes(img_response.content)

    return f"/uploads/images/{filename}"


async def _generate_with_sensenova(
    prompt: str, width: int, height: int
) -> str:
    """
    使用商汤 SenseNova 文生图（默认模型 sensenova-u1-fast）

    接口文档：{IMAGE_API_BASE}/images/generations（OpenAI 兼容）
    注意：返回的图片 URL 为临时链接（有效期 1 小时），必须立即下载转存本地。
    """
    base_url = (settings.IMAGE_API_BASE or settings.LLM_API_BASE).strip().rstrip("/")
    api_key = (settings.IMAGE_API_KEY or settings.LLM_API_KEY).strip()
    if not base_url or not api_key:
        raise ValueError(
            "SenseNova 生图缺少 API Base / Key，请在 backend/.env 中配置 "
            "LLM_API_BASE 与 LLM_API_KEY（或 IMAGE_API_BASE / IMAGE_API_KEY）"
        )

    payload = {
        "model": settings.IMAGE_MODEL,
        "prompt": prompt,
        "size": _pick_sensenova_size(width, height),
        "n": 1,
        "watermark": settings.IMAGE_WATERMARK,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=180.0) as http_client:
        try:
            response = await http_client.post(
                f"{base_url}/images/generations",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                "SenseNova 生图接口返回错误 "
                f"{e.response.status_code}: {e.response.text[:300]}"
            ) from e
        except httpx.HTTPError as e:
            raise RuntimeError(
                f"无法连接 SenseNova 生图服务（{base_url}）：{e}"
            ) from e

    try:
        image_url = data["data"][0]["url"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"SenseNova 响应中未找到图片地址：{str(data)[:300]}"
        ) from e

    # 临时 URL 仅 1 小时有效，立即下载落盘
    try:
        return await _download_to_local(image_url)
    except httpx.HTTPError as e:
        raise RuntimeError(f"生成图片下载失败：{e}") from e


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
    """
    使用本地 Stable Diffusion WebUI 生成图片

    依赖 AUTOMATIC1111 stable-diffusion-webui 并开启 --api 参数，
    接口文档：{SD_WEBUI_URL}/docs（/sdapi/v1/txt2img）
    """
    # SD 要求宽高为 8 的倍数，向下对齐，最小 64
    width = max(64, (width // 8) * 8)
    height = max(64, (height // 8) * 8)

    payload = {
        "prompt": prompt,
        "negative_prompt": "lowres, bad anatomy, worst quality, low quality",
        "steps": 20,
        "width": width,
        "height": height,
        "batch_size": 1,
        "n_iter": 1,
        "sampler_name": "DPM++ 2M Karras",
    }

    base_url = settings.SD_WEBUI_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=180.0) as http_client:
            response = await http_client.post(
                f"{base_url}/sdapi/v1/txt2img",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise RuntimeError(
            f"无法连接本地 Stable Diffusion 服务（{base_url}），"
            "请确认 WebUI 已启动并添加 --api 参数"
        ) from e

    images = data.get("images")
    if not images:
        raise RuntimeError("Stable Diffusion 未返回图片数据")

    # WebUI 返回 base64 编码图片，可能带 data:image/png;base64, 前缀
    image_b64 = images[0].split(",", 1)[-1]
    image_bytes = base64.b64decode(image_b64)

    filename = f"{uuid.uuid4().hex}.png"
    file_path = UPLOAD_DIR / filename
    file_path.write_bytes(image_bytes)

    return f"/uploads/images/{filename}"


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
