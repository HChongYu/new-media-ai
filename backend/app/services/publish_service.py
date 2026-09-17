"""
内容发布服务

通过 settings.PUBLISH_MODE 切换发布方式：
- simulate（默认）：开发/演示环境，模拟发布流程，不调用外部平台、不伪造文章链接
- live：对接真实平台开放接口
    - 微信公众号：access_token → 新建草稿(draft/add) → 发布(freepublish/submit)
    - 小红书：官方暂无面向个人开发者的公开笔记发布接口，需企业/服务商资质授权
"""
import asyncio
import html

import httpx

from app.config import settings

SUPPORTED_PLATFORMS = ("xiaohongshu", "wechat")

WECHAT_API_BASE = "https://api.weixin.qq.com"


class PublishError(Exception):
    """发布失败异常，message 可直接展示给用户"""


async def publish_to_platform(platform: str, title: str, content: str) -> str | None:
    """
    发布内容到指定平台。

    Returns:
        平台文章链接；平台未直接下发链接时（模拟模式 / 微信异步发布）返回 None。

    Raises:
        PublishError: 平台不支持、凭证缺失或平台接口返回错误。
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise PublishError(f"不支持的平台: {platform}")

    if settings.PUBLISH_MODE.lower() == "live":
        if platform == "wechat":
            return await _publish_to_wechat(title, content)
        return await _publish_to_xiaohongshu(title, content)

    return await _simulate_publish(platform)


async def _simulate_publish(platform: str) -> None:
    """模拟发布：仅模拟网络耗时，不产生虚假的平台链接"""
    await asyncio.sleep(0.1)
    return None


async def _publish_to_wechat(title: str, content: str) -> str | None:
    """
    发布到微信公众号（订阅号/服务号官方接口）

    流程：获取 access_token → 新建图文草稿 → 提交发布。
    发布为平台侧异步审核，接口不直接返回文章链接，因此返回 None，
    可在公众号后台或通过 freepublish/batchget 查询发布结果。
    """
    appid = settings.WECHAT_APPID.strip()
    appsecret = settings.WECHAT_APPSECRET.strip()
    if not appid or not appsecret:
        raise PublishError(
            "微信公众号 AppID/AppSecret 未配置，无法真实发布；"
            "请在 backend/.env 中配置或将 PUBLISH_MODE 设为 simulate"
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            access_token = await _get_wechat_access_token(client, appid, appsecret)

            # 1. 新建图文草稿
            draft_resp = await client.post(
                f"{WECHAT_API_BASE}/cgi-bin/draft/add",
                params={"access_token": access_token},
                json={
                    "articles": [
                        {
                            "title": title,
                            "content": _plain_text_to_html(content),
                            "content_source_url": "",
                            "need_open_comment": 0,
                            "only_fans_can_comment": 0,
                        }
                    ]
                },
            )
            draft_data = draft_resp.json()
            media_id = draft_data.get("media_id")
            if not media_id:
                raise PublishError(
                    f"创建微信公众号草稿失败: "
                    f"[{draft_data.get('errcode')}] {draft_data.get('errmsg', '未知错误')}"
                )

            # 2. 提交发布（异步审核）
            submit_resp = await client.post(
                f"{WECHAT_API_BASE}/cgi-bin/freepublish/submit",
                params={"access_token": access_token},
                json={"media_id": media_id},
            )
            submit_data = submit_resp.json()
            if submit_data.get("errcode") != 0:
                raise PublishError(
                    f"微信公众号发布失败: "
                    f"[{submit_data.get('errcode')}] {submit_data.get('errmsg', '未知错误')}"
                )
    except httpx.HTTPError as e:
        raise PublishError(f"调用微信公众号接口失败: {e}") from e

    return None


async def _get_wechat_access_token(
    client: httpx.AsyncClient, appid: str, appsecret: str
) -> str:
    """
    获取微信公众号 access_token。

    优先使用中控服务地址（WECHAT_ACCESS_TOKEN_URL，适合多实例共享、
    规避 IP 白名单问题）；否则使用官方 client_credential 方式。
    """
    token_url = settings.WECHAT_ACCESS_TOKEN_URL.strip()
    if token_url:
        resp = await client.get(token_url)
        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise PublishError(
                f"中控服务未返回 access_token: {data.get('errmsg', '未知错误')}"
            )
        return token

    resp = await client.get(
        f"{WECHAT_API_BASE}/cgi-bin/token",
        params={
            "grant_type": "client_credential",
            "appid": appid,
            "secret": appsecret,
        },
    )
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise PublishError(
            f"获取微信 access_token 失败: "
            f"[{data.get('errcode')}] {data.get('errmsg', '未知错误')}；"
            "请检查 AppID/AppSecret 及服务器 IP 白名单配置"
        )
    return token


async def _publish_to_xiaohongshu(title: str, content: str) -> str:
    """
    发布到小红书。

    小红书开放平台的笔记发布接口仅面向已入驻的品牌商家/服务商，
    需通过 OAuth 授权获取商户访问凭证，无通用的服务端密钥发布方式，
    因此此处不提供未经验证的调用实现。
    """
    raise PublishError(
        "小红书暂不支持服务端直接发布：需在小红书开放平台申请企业/服务商权限"
        "并完成 OAuth 授权；开发阶段可将 PUBLISH_MODE 设为 simulate 使用模拟发布"
    )


def _plain_text_to_html(text: str) -> str:
    """将纯文本内容转为公众号草稿所需的简单 HTML（先转义再按段落包裹）"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    return "".join(
        f"<p>{html.escape(p).replace(chr(10), '<br/>')}</p>" for p in paragraphs
    )
