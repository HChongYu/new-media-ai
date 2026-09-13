import math
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.models.image import Image
from app.schemas.image import ImageResponse, ImageListResponse
from app.schemas.common import ResponseModel

router = APIRouter()

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=ResponseModel[ImageListResponse])
def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    content_id: int | None = None,
    image_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取图片列表"""
    query = db.query(Image)

    if content_id:
        query = query.filter(Image.content_id == content_id)
    if image_type:
        query = query.filter(Image.image_type == image_type)

    total = query.count()
    items = (
        query.order_by(Image.generated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = [
        ImageResponse(
            id=img.id,
            content_id=img.content_id,
            image_url=img.image_url,
            image_type=img.image_type,
            prompt=img.prompt,
            generated_at=img.generated_at.isoformat(),
            width=img.width,
            height=img.height,
            size=img.size,
        )
        for img in items
    ]

    return ResponseModel(
        data=ImageListResponse(
            items=result,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )
    )


@router.delete("/{image_id}", response_model=ResponseModel)
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除图片"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 删除物理文件
    if image.image_url:
        file_path = UPLOAD_DIR / Path(image.image_url).name
        if file_path.exists():
            file_path.unlink()

    db.delete(image)
    db.commit()
    return ResponseModel(message="删除成功")
