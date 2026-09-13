import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.content import Content
from app.models.publish_record import PublishRecord
from app.schemas.publish import PublishResponse, PublishListResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/history", response_model=ResponseModel[PublishListResponse])
def get_publish_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    platform: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取发布记录列表"""
    query = db.query(PublishRecord)

    if platform:
        query = query.filter(PublishRecord.platform == platform)
    if status:
        query = query.filter(PublishRecord.status == status)

    total = query.count()
    items = (
        query.order_by(PublishRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for item in items:
        content = db.query(Content).filter(Content.id == item.content_id).first()
        result.append(
            PublishResponse(
                id=item.id,
                content_id=item.content_id,
                content_title=content.title if content else None,
                platform=item.platform,
                post_url=item.post_url,
                status=item.status,
                published_at=item.published_at.isoformat() if item.published_at else None,
                error_message=item.error_message,
                created_at=item.created_at.isoformat(),
            )
        )

    return ResponseModel(
        data=PublishListResponse(
            items=result,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )
    )


@router.delete("/{record_id}", response_model=ResponseModel)
def delete_publish_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除发布记录"""
    record = db.query(PublishRecord).filter(PublishRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="发布记录不存在")

    db.delete(record)
    db.commit()
    return ResponseModel(message="删除成功")
