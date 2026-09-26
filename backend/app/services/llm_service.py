"""
LLM 服务封装

支持 OpenAI / Anthropic / 本地模型 / Mock，通过 LLM_PROVIDER 切换
"""
import json
import logging

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.config import settings

logger = logging.getLogger(__name__)

_llm_client = None


class MockLLM:
    """
    本地假 LLM（LLM_PROVIDER=mock 时使用），不发起任何网络请求。

    通过提示词中的系统角色标识识别调用节点，返回与真实输出同构的假数据：
    - 选题节点：JSON 数组（title / description / category / tags）
    - 撰稿节点：Markdown 正文（首行为 "# 标题"）
    - 视觉节点：JSON 数组（point / detail / image_prompt）

    假数据会提取提示词中的方向/选题/标题字段，与实际输入保持关联。
    """

    # 各节点提示词中的唯一角色标识
    _MARKER_TOPICS = "资深的 AI 技术自媒体运营专家"
    _MARKER_DRAFT = "专业的 AI 技术内容创作者"
    _MARKER_VISUAL = "小红书视觉内容设计师"

    async def ainvoke(self, prompt, *args, **kwargs) -> AIMessage:
        return AIMessage(content=self._build_content(str(prompt)))

    def invoke(self, prompt, *args, **kwargs) -> AIMessage:
        return AIMessage(content=self._build_content(str(prompt)))

    def _build_content(self, prompt: str) -> str:
        if self._MARKER_TOPICS in prompt:
            return self._build_topics(prompt)
        if self._MARKER_DRAFT in prompt:
            return self._build_draft(prompt)
        if self._MARKER_VISUAL in prompt:
            return self._build_visual_points(prompt)
        logger.warning("MockLLM 未识别提示词类型，返回占位文本")
        return "【MockLLM】未识别的提示词类型，请检查提示词模板"

    def _build_topics(self, prompt: str) -> str:
        """选题节点：返回 5 个角度不同的选题 JSON"""
        direction = self._extract_line(prompt, "**内容方向**：") or "AI 技术"
        topics = [
            {
                "title": f"{direction}，从 0 到 1 的实战入门指南",
                "description": f"围绕「{direction}」梳理核心概念与学习路径，结合真实案例拆解上手步骤，新手照着做就能跑通第一个 Demo。",
                "category": "AI 工具",
                "tags": ["AI实战", "新手入门"],
            },
            {
                "title": f"搞懂{direction}，这 5 个高频踩坑点一定要避开",
                "description": f"总结实践「{direction}」时最常见的 5 类问题，分析原因并给出可直接复用的解决方案，帮你少走弯路。",
                "category": "Agent 实战",
                "tags": ["避坑指南", "实战经验"],
            },
            {
                "title": f"{direction}效率翻倍：3 个拿来即用的 Prompt 模板",
                "description": f"分享基于「{direction}」沉淀的提示词模板，覆盖需求分析、代码生成与结果校验，附使用场景和调优思路。",
                "category": "Prompt 工程",
                "tags": ["Prompt模板", "效率工具"],
            },
            {
                "title": f"用{direction}做一个真实小项目，完整流程全拆解",
                "description": f"以一个端到端小项目为例，演示「{direction}」从需求拆解、方案设计到落地验证的全过程，代码可直接参考。",
                "category": "Agent 实战",
                "tags": ["项目实战", "全流程"],
            },
            {
                "title": f"{direction}为什么突然火了？一文看懂能力边界",
                "description": f"结合最新技术动态讲清「{direction}」的适用场景、能力边界与发展趋势，帮助读者理性判断要不要投入学习。",
                "category": "行业动态",
                "tags": ["行业解读", "技术趋势"],
            },
        ]
        return json.dumps(topics, ensure_ascii=False)

    def _build_draft(self, prompt: str) -> str:
        """撰稿节点：返回 Markdown 文章，首行必须是 # 标题格式"""
        topic = self._extract_line(prompt, "**选题**：") or "AI 实战技巧"
        revision_note = (
            "> 本版已根据上一轮修改意见逐条调整。\n\n"
            if "上一版的修改意见" in prompt
            else ""
        )
        return f"""# {topic}，看这一篇就够了

{revision_note}## 开头：为什么你一定要了解{topic}

很多人第一次接触 **{topic}** 时都会卡在同一个地方：概念看了一堆，真要动手就懵。
这篇文章不讲空话，直接带你走一遍可落地的完整流程，建议先收藏再看。

## 一、先搞懂核心概念

{topic}的本质，可以理解为「把复杂任务拆解成模型能执行的小步骤」。
抓住下面三个关键点就够了：

- **目标清晰**：先定义想要什么结果，再决定怎么做
- **小步验证**：每一步都能独立测试，出问题马上定位
- **持续迭代**：先跑通，再优化，不要一上来追求完美

## 二、动手实战：3 步跑通第一个 Demo

**第 1 步：准备环境**
安装好依赖，确认 API Key 和基础配置可用。

**第 2 步：最小闭环**
先用最简单的输入验证整条链路，确认能拿到预期输出。

**第 3 步：逐步加复杂度**
在最小闭环上叠加业务逻辑，每次只改一个变量。

```python
# 核心逻辑其实只有几行
result = await client.ainvoke(prompt)
print(result.content)
```

## 三、新手最容易踩的 3 个坑

1. **只看不动手**：技术是练出来的，看完立刻自己跑一遍
2. **提示词太模糊**：给模型的指令要具体、可衡量
3. **忽略异常处理**：网络抖动和格式错误都要提前兜底

## 写在最后

{topic}没有想象中难，关键是**边学边练、用项目驱动学习**。
今天就动手搭一个属于你自己的 Demo，遇到问题欢迎在评论区交流。
如果觉得有用，记得点赞收藏关注。"""

    def _build_visual_points(self, prompt: str) -> str:
        """视觉节点：返回 5 个卡片知识点 JSON（image_prompt 为英文绘图提示词）"""
        title = self._extract_line(prompt, "**文章标题**：") or "技术要点"
        points = [
            {
                "point": "三步跑通 Demo",
                "detail": f"「{title}」的上手路径可拆为准备环境、最小闭环、逐步加复杂度三步。",
                "image_prompt": "flat vector illustration of a developer building a numbered step-by-step roadmap, clean tech style, blue and orange palette, vertical composition",
            },
            {
                "point": "核心概念一句话",
                "detail": "本质是把复杂任务拆成模型能执行的小步骤，目标清晰、小步验证。",
                "image_prompt": "flat vector illustration of puzzle pieces fitting together into a workflow, minimal tech background, soft gradients, clean composition",
            },
            {
                "point": "提示词要具体",
                "detail": "给模型的指令需要具体、可衡量，避免模糊描述导致结果不可控。",
                "image_prompt": "flat vector illustration of a chat prompt window transforming into a structured checklist, modern flat style, pastel colors",
            },
            {
                "point": "异常提前兜底",
                "detail": "网络抖动和输出格式错误都要提前处理，保证流程不被单次失败阻断。",
                "image_prompt": "flat vector illustration of a safety net catching error warning signs, shield and checklist, tech flat design, calm colors",
            },
            {
                "point": "项目驱动学习",
                "detail": "边学边练、用真实项目驱动，比只看教程的掌握效果好得多。",
                "image_prompt": "flat vector illustration of a person climbing stacked books toward a launching rocket, motivational tech style, clean shapes",
            },
        ]
        return json.dumps(points, ensure_ascii=False)

    @staticmethod
    def _extract_line(prompt: str, marker: str) -> str:
        """提取提示词中 'marker：值' 所在行的值，让假数据与用户输入挂钩"""
        for line in prompt.splitlines():
            if marker in line:
                return line.split(marker, 1)[1].strip()
        return ""


def get_llm_client():
    """获取 LLM 客户端（单例）"""
    global _llm_client
    if _llm_client is not None:
        return _llm_client

    provider = settings.LLM_PROVIDER.lower()

    if provider == "mock":
        logger.info("LLM 使用 MockLLM：不请求真实 API，返回内置假数据")
        _llm_client = MockLLM()
        return _llm_client

    api_key = settings.LLM_API_KEY.strip()

    if not api_key:
        raise ValueError(
            "LLM_API_KEY 未配置，请在 backend/.env 文件中设置有效的 API Key。"
            "可参考 .env.example 文件。"
        )

    if provider == "anthropic":
        _llm_client = ChatAnthropic(
            model=settings.LLM_MODEL,
            anthropic_api_key=api_key,
            max_tokens=4096,
            temperature=0.7,
        )
    else:
        # 默认使用 OpenAI 兼容接口（也适用于本地模型）
        client_kwargs = {
            "model": settings.LLM_MODEL,
            "openai_api_key": api_key,
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 120,  # LLM 生成可能较慢，给 120 秒
        }
        # 仅在配置了 Base URL 时传入，避免空字符串覆盖默认值
        api_base = settings.LLM_API_BASE.strip()
        if api_base:
            client_kwargs["openai_api_base"] = api_base
        _llm_client = ChatOpenAI(**client_kwargs)

    return _llm_client


def reset_llm_client():
    """重置 LLM 客户端（配置变更后调用）"""
    global _llm_client
    _llm_client = None
