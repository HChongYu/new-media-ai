"""
LLM 服务封装

支持 OpenAI / Anthropic / 本地模型，通过配置切换
"""
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.config import settings

_llm_client = None


def get_llm_client():
    """获取 LLM 客户端（单例）"""
    global _llm_client
    if _llm_client is not None:
        return _llm_client

    provider = settings.LLM_PROVIDER.lower()

    if provider == "anthropic":
        _llm_client = ChatAnthropic(
            model=settings.LLM_MODEL,
            anthropic_api_key=settings.LLM_API_KEY,
            max_tokens=4096,
            temperature=0.7,
        )
    else:
        # 默认使用 OpenAI 兼容接口（也适用于本地模型）
        _llm_client = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.LLM_API_KEY,
            openai_api_base=settings.LLM_API_BASE,
            temperature=0.7,
            max_tokens=4096,
        )

    return _llm_client


def reset_llm_client():
    """重置 LLM 客户端（配置变更后调用）"""
    global _llm_client
    _llm_client = None
