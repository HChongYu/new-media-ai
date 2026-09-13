from typing import Any
from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    preferred_topics: list[str] | None = None
    preferred_formats: list[str] | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    image_style: str | None = None
    platform_settings: dict[str, Any] | None = None


class SettingsResponse(BaseModel):
    id: int
    user_id: int
    preferred_topics: list[str]
    preferred_formats: list[str]
    llm_provider: str | None = None
    llm_model: str | None = None
    image_style: str | None = None
    platform_settings: dict[str, Any]
    created_at: str
    updated_at: str
