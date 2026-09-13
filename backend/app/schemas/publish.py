from pydantic import BaseModel


class PublishResponse(BaseModel):
    id: int
    content_id: int
    content_title: str | None = None
    platform: str
    post_url: str | None = None
    status: str
    published_at: str | None = None
    error_message: str | None = None
    created_at: str


class PublishListResponse(BaseModel):
    items: list[PublishResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
