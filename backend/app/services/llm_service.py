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
