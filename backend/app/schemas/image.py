from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: int
    content_id: int
    image_url: str
    image_type: str
    prompt: str
    generated_at: str
    width: int
    height: int
    size: int | None = None


class ImageListResponse(BaseModel):
    items: list[ImageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
