"""
提示词运行时加载服务

三层保障，让提示词真正可运营：
1. DB 优先：节点执行时从 prompt_templates 表读取当前生效版本，
   管理端发布新版本 / 回滚 / A-B 调整后无需重启即生效；
2. A/B 分桶：同一 key 存在多条 active 时，按 thread_id（回退到用户输入）
   做 MD5 哈希确定性分桶，同一个工作流始终命中同一变体；
3. 代码兜底：DB 不可用、无生效版本或模板占位符损坏时，
   回退到 app.graph.prompts.PROMPT_REGISTRY 中的内置模板，流程不中断。

另外用短 TTL 缓存降低 DB 压力，管理端变更后会主动 invalidate。
"""
import asyncio
import hashlib
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

from app.database import SessionLocal
from app.graph.prompts import PROMPT_REGISTRY
from app.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 30


@dataclass(frozen=True)
class ActivePrompt:
    """active 行的轻量快照（避免 SQLAlchemy 会话关闭后的 DetachedInstanceError）"""

    version: int
    variant: str
    traffic_percent: int | None
    content: str


# key -> (过期时间戳, active 快照列表)
_cache: dict[str, tuple[float, list[ActivePrompt]]] = {}


def invalidate_cache(key: str | None = None) -> None:
    """管理端变更后主动清缓存；key=None 清空全部"""
    if key is None:
        _cache.clear()
    else:
        _cache.pop(key, None)


def _load_active_rows(key: str) -> list[ActivePrompt]:
    """读取某 key 的全部 active 版本（带 TTL 缓存），DB 异常时回退内置"""
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        db = SessionLocal()
        try:
            rows = (
                db.query(PromptTemplate)
                .filter(
                    PromptTemplate.key == key,
                    PromptTemplate.status == "active",
                )
                .order_by(PromptTemplate.version.asc())
                .all()
            )
            snapshots = [
                ActivePrompt(
                    version=row.version,
                    variant=row.variant,
                    traffic_percent=row.traffic_percent,
                    content=row.content,
                )
                for row in rows
            ]
        finally:
            db.close()
    except Exception as exc:  # DB 不可用时走代码兜底，不阻断工作流
        logger.warning("提示词 %s 读取 DB 失败，使用内置模板：%s", key, exc)
        _cache.pop(key, None)
        return []

    _cache[key] = (now + _CACHE_TTL_SECONDS, snapshots)
    return snapshots


def _bucket_index(key: str, bucket_id: str | None) -> int:
    """0-99 的确定性分桶值；无分桶键时随机（并告警，实验配置应保证传入）"""
    if not bucket_id:
        bucket = random.randint(0, 99)
        logger.warning("提示词 %s 的 A/B 实验缺少分桶键，本次随机分桶=%d", key, bucket)
        return bucket
    digest = hashlib.md5(f"{key}:{bucket_id}".encode("utf-8")).hexdigest()
    return int(digest, 16) % 100


def _pick_variant(key: str, rows: list[ActivePrompt], bucket_id: str | None) -> ActivePrompt:
    """按流量占比选择变体；无实验变体时直接返回主干"""
    variants = [row for row in rows if row.variant != "main"]
    main_rows = [row for row in rows if row.variant == "main"]
    main = main_rows[0] if main_rows else rows[-1]

    if not variants:
        return main

    bucket = _bucket_index(key, bucket_id)
    cumulative = 0
    for row in sorted(variants, key=lambda r: r.version):
        cumulative += row.traffic_percent or 0
        if bucket < cumulative:
            logger.info(
                "提示词 %s A/B 命中实验变体 v%s(%s)，bucket=%d",
                key, row.version, row.variant, bucket,
            )
            return row
    return main


def _format(template: str, variables: dict[str, Any]) -> str | None:
    try:
        return template.format(**variables)
    except (KeyError, IndexError, ValueError) as exc:
        logger.warning("提示词模板格式化失败（占位符与变量不匹配）：%s", exc)
        return None


async def render_prompt(
    key: str,
    *,
    bucket_id: str | None = None,
    **variables: Any,
) -> str:
    """
    渲染提示词。

    :param key: PROMPT_REGISTRY 中的逻辑标识
    :param bucket_id: A/B 分桶键（工作流传 thread_id），同一键命中结果稳定
    :param variables: 模板占位符变量
    :return: 渲染后的提示词字符串；任何异常都回退内置模板
    """
    if key not in PROMPT_REGISTRY:
        raise ValueError(f"未知的提示词 key：{key}")

    default_template = PROMPT_REGISTRY[key]["template"]
    rows = await asyncio.to_thread(_load_active_rows, key)

    if not rows:
        rendered = _format(default_template, variables)
        if rendered is None:
            # 内置模板理论上不会失败；失败说明调用方变量传错，直接暴露问题
            return default_template.format(**variables)
        logger.info("提示词 %s 使用代码内置模板（DB 无生效版本）", key)
        return rendered

    chosen = _pick_variant(key, rows, bucket_id)
    rendered = _format(chosen.content, variables)
    if rendered is None:
        # DB 中的运营模板占位符被改坏：回退内置模板，避免线上流程中断
        logger.warning(
            "提示词 %s 的 DB 版本 v%s(%s) 格式化失败，回退内置模板",
            key, chosen.version, chosen.variant,
        )
        return default_template.format(**variables)

    logger.info("提示词 %s 使用 DB 版本 v%s(%s)", key, chosen.version, chosen.variant)
    return rendered
