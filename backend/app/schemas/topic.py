from pydantic import BaseModel


class TopicGenerateRequest(BaseModel):
    keywords: list[str] | None = None
    category: str | None = None
    target_audience: str | None = None
    content_style: str | None = None
    count: int = 5


class TopicCreate(BaseModel):
    title: str
    description: str
    category: str | None = None
    tags: list[str] | None = None


class TopicUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class TopicResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    category: str | None = None
    tags: list[str] | None = None
    content_count: int = 0
    created_by: int
    created_by_name: str | None = None
    created_at: str
    approved_at: str | None = None


class TopicListResponse(BaseModel):
    items: list[TopicResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
