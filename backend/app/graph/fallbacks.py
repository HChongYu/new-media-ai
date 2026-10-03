"""
节点级兜底模板

当 LLM 主备模型全部失败 / 熔断（ResilientLLM 抛异常）时启用，
保证工作流仍然产出结构完整的结果、不被整体中断（API 层不再转 502）。

与 graph/nodes 内已有的「输出解析失败降级」互补：
- 解析失败降级：LLM 有返回，但 JSON 解析不动 → 截取原始文本；
- 本模块：LLM 根本没调通（网络故障 / 认证失败 / 熔断打开）→ 模板生成。

兜底内容只依赖 state 中的用户输入，字段结构与正常节点返回保持一致，
后续节点（人工选择、审核、配图）无需感知差异。
"""
from typing import Any

# 兜底内容统一标注，运营 / 审核人员一眼可辨（也便于后续检索替换）
FALLBACK_NOTE = "（AI 服务暂不可用，本内容为系统兜底生成，恢复后可重新生成）"

# 视觉兜底用的通用英文绘图提示词（扁平科技风，与 prompts.py 风格一致）
_FALLBACK_IMAGE_PROMPT = (
    "flat vector illustration of a modern technology knowledge card, "
    "clean minimalist tech style, blue and orange palette, "
    "vertical composition for social media"
)


def fallback_topics(topic_direction: str) -> list[dict[str, Any]]:
    """选题节点兜底：基于用户输入方向构造 1 条可选择的选题"""
    direction = (topic_direction or "AI 技术").strip()[:30]
    return [
        {
            "title": f"{direction}实战入门：核心要点全梳理",
            "description": (
                f"围绕「{direction}」梳理核心概念、典型应用场景与上手步骤，"
                f"帮助读者快速建立整体认知。{FALLBACK_NOTE}"
            ),
            "category": "AI 工具",
            "tags": ["入门指南"],
        }
    ]


def fallback_draft(selected_topic: str) -> tuple[str, str]:
    """
    撰稿节点兜底：返回 (标题, Markdown 正文)。

    直接返回分离后的结构，节点无需再按「# 标题」首行解析；
    正文结构完整（引言 / 核心内容 / 小结），可直接进入人工审核环节。
    """
    topic = (selected_topic or "AI 实战要点").strip()
    content = f"""> {FALLBACK_NOTE}

## 引言

本文围绕「{topic}」展开，帮你快速了解它的核心概念、适用场景与上手路径。

## 一、它是什么

一句话讲清「{topic}」的定义，以及它主要解决什么问题。

## 二、适用场景

- **场景一：日常提效**——把重复性工作交给 AI，把时间留给判断与决策
- **场景二：项目实战**——在真实需求中验证效果，沉淀可复用的经验
- **场景三：问题排查**——借助 AI 快速定位报错原因与修复方向

## 三、上手三步

1. **明确目标**：定义清楚想要的结果，准备好必要的环境与账号
2. **最小闭环**：用最简单的输入跑通整条链路，确认能拿到预期输出
3. **持续迭代**：在最小闭环上逐步叠加复杂度，每次只改一个变量

## 小结

学习「{topic}」的关键是动手实践。建议收藏本文，结合实际项目边做边学，
AI 服务恢复后可重新生成完整版本。
"""
    return f"{topic}（兜底版）", content


def fallback_visual_points(draft_title: str) -> list[dict[str, str]]:
    """视觉节点兜底：基于文章标题生成 1 个可配图的知识点卡片"""
    title = (draft_title or "技术要点").strip()
    return [
        {
            "point": title[:15],
            "detail": f"「{title}」核心要点速览。{FALLBACK_NOTE}",
            "image_prompt": _FALLBACK_IMAGE_PROMPT,
        }
    ]
