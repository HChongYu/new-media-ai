from pydantic import BaseModel


class ContentGenerateRequest(BaseModel):
    platform: str | None = None  # xiaohongshu / wechat
    tone: str | None = None  # professional / casual / enthusiastic
    length: str | None = None  # short / medium / long


class ContentCreate(BaseModel):
    topic_id: int
    title: str
    content_text: str
    content_type: str = "article"
    status: str = "draft"


class ContentUpdate(BaseModel):
    title: str | None = None
    content_text: str | None = None
    content_type: str | None = None
    status: str | None = None


class ContentReviewRequest(BaseModel):
    status: str  # approved / rejected
    review_note: str | None = None


class ContentResponse(BaseModel):
    id: int
    topic_id: int
    topic_title: str | None = None
    title: str
    content_text: str
    content_type: str
    word_count: int
    status: str
    created_by: int
    created_by_name: str | None = None
    reviewed_by: int | None = None
    reviewed_by_name: str | None = None
    created_at: str
    reviewed_at: str | None = None
    published_at: str | None = None


class ContentListResponse(BaseModel):
    items: list[ContentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
