import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.topic import Topic
from app.models.content import Content
from app.models.image import Image
from app.schemas.content import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ContentReviewRequest,
    ContentListResponse,
)
from app.schemas.image import ImageResponse, ImageGenerateRequest
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("", response_model=ResponseModel[ContentListResponse])
def list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    topic_id: int | None = None,
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取内容列表"""
    query = db.query(Content)

    if status:
        query = query.filter(Content.status == status)
    if topic_id:
        query = query.filter(Content.topic_id == topic_id)
    if keyword:
        query = query.filter(
            or_(
                Content.title.ilike(f"%{keyword}%"),
                Content.content_text.ilike(f"%{keyword}%"),
            )
        )
    if start_date:
        query = query.filter(Content.created_at >= start_date)
    if end_date:
        query = query.filter(Content.created_at <= end_date)

    total = query.count()
    items = (
        query.order_by(Content.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for item in items:
        topic = db.query(Topic).filter(Topic.id == item.topic_id).first()
        creator = db.query(User).filter(User.id == item.created_by).first()
        reviewer = db.query(User).filter(User.id == item.reviewed_by).first() if item.reviewed_by else None
        result.append(
            ContentResponse(
                id=item.id,
                topic_id=item.topic_id,
                topic_title=topic.title if topic else None,
                title=item.title,
                content_text=item.content_text,
                content_type=item.content_type,
                word_count=item.word_count,
                status=item.status,
                created_by=item.created_by,
                created_by_name=creator.username if creator else None,
                reviewed_by=item.reviewed_by,
                reviewed_by_name=reviewer.username if reviewer else None,
                created_at=item.created_at.isoformat(),
                reviewed_at=item.reviewed_at.isoformat() if item.reviewed_at else None,
                published_at=item.published_at.isoformat() if item.published_at else None,
            )
        )

    return ResponseModel(
        data=ContentListResponse(
            items=result,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )
    )


@router.get("/{content_id}", response_model=ResponseModel[ContentResponse])
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取内容详情"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
    creator = db.query(User).filter(User.id == content.created_by).first()
    reviewer = db.query(User).filter(User.id == content.reviewed_by).first() if content.reviewed_by else None

    return ResponseModel(
        data=ContentResponse(
            id=content.id,
            topic_id=content.topic_id,
            topic_title=topic.title if topic else None,
            title=content.title,
            content_text=content.content_text,
            content_type=content.content_type,
            word_count=content.word_count,
            status=content.status,
            created_by=content.created_by,
            created_by_name=creator.username if creator else None,
            reviewed_by=content.reviewed_by,
            reviewed_by_name=reviewer.username if reviewer else None,
            created_at=content.created_at.isoformat(),
            reviewed_at=content.reviewed_at.isoformat() if content.reviewed_at else None,
            published_at=content.published_at.isoformat() if content.published_at else None,
        )
    )


@router.post("", response_model=ResponseModel[ContentResponse])
def create_content(
    request: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建内容"""
    topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    content = Content(
        topic_id=request.topic_id,
        title=request.title,
        content_text=request.content_text,
        content_type=request.content_type,
        word_count=len(request.content_text),
        status=request.status,
        created_by=current_user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)

    return ResponseModel(
        data=ContentResponse(
            id=content.id,
            topic_id=content.topic_id,
            topic_title=topic.title,
            title=content.title,
            content_text=content.content_text,
            content_type=content.content_type,
            word_count=content.word_count,
            status=content.status,
            created_by=content.created_by,
            created_by_name=current_user.username,
            created_at=content.created_at.isoformat(),
        )
    )


@router.put("/{content_id}", response_model=ResponseModel[ContentResponse])
def update_content(
    content_id: int,
    request: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新内容"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(content, key, value)

    if "content_text" in update_data:
        content.word_count = len(content.content_text)

    db.commit()
    db.refresh(content)

    topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
    creator = db.query(User).filter(User.id == content.created_by).first()

    return ResponseModel(
        data=ContentResponse(
            id=content.id,
            topic_id=content.topic_id,
            topic_title=topic.title if topic else None,
            title=content.title,
            content_text=content.content_text,
            content_type=content.content_type,
            word_count=content.word_count,
            status=content.status,
            created_by=content.created_by,
            created_by_name=creator.username if creator else None,
            created_at=content.created_at.isoformat(),
            reviewed_at=content.reviewed_at.isoformat() if content.reviewed_at else None,
            published_at=content.published_at.isoformat() if content.published_at else None,
        )
    )


@router.post("/{content_id}/review", response_model=ResponseModel[ContentResponse])
def review_content(
    content_id: int,
    request: ContentReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审核内容"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    content.status = request.status
    content.reviewed_by = current_user.id
    content.reviewed_at = datetime.now()
    content.review_note = request.review_note

    db.commit()
    db.refresh(content)

    topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
    creator = db.query(User).filter(User.id == content.created_by).first()
    reviewer = db.query(User).filter(User.id == content.reviewed_by).first()

    return ResponseModel(
        data=ContentResponse(
            id=content.id,
            topic_id=content.topic_id,
            topic_title=topic.title if topic else None,
            title=content.title,
            content_text=content.content_text,
            content_type=content.content_type,
            word_count=content.word_count,
            status=content.status,
            created_by=content.created_by,
            created_by_name=creator.username if creator else None,
            reviewed_by=content.reviewed_by,
            reviewed_by_name=reviewer.username if reviewer else None,
            created_at=content.created_at.isoformat(),
            reviewed_at=content.reviewed_at.isoformat() if content.reviewed_at else None,
            published_at=content.published_at.isoformat() if content.published_at else None,
        )
    )


@router.delete("/{content_id}", response_model=ResponseModel)
def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除内容"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    db.delete(content)
    db.commit()
    return ResponseModel(message="删除成功")


# ============================================================
# 内容关联的图片接口（前端: /contents/{contentId}/images）
# ============================================================

@router.get("/{content_id}/images", response_model=ResponseModel[list[ImageResponse]])
def get_content_images(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取某内容关联的图片"""
    images = (
        db.query(Image)
        .filter(Image.content_id == content_id)
        .order_by(Image.generated_at.desc())
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
        for img in images
    ]

    return ResponseModel(data=result)


@router.post("/{content_id}/images/generate", response_model=ResponseModel[list[ImageResponse]])
async def generate_content_images(
    content_id: int,
    request: ImageGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 为内容生成配图"""
    from app.workflows.image import generate_images_workflow

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    results = await generate_images_workflow(
        content_title=content.title,
        content_text=content.content_text,
        image_types=request.image_type or ["cover", "section", "summary"],
        count=request.count or 3,
        style=request.style or "professional",
        width=request.width or 1024,
        height=request.height or 768,
    )

    saved_images = []
    for img_data in results:
        image = Image(
            content_id=content_id,
            image_url=img_data["image_url"],
            image_type=img_data["image_type"],
            prompt=img_data["prompt"],
            width=img_data.get("width", request.width or 1024),
            height=img_data.get("height", request.height or 768),
        )
        db.add(image)
        db.flush()
        saved_images.append(
            ImageResponse(
                id=image.id,
                content_id=image.content_id,
                image_url=image.image_url,
                image_type=image.image_type,
                prompt=image.prompt,
                generated_at=image.generated_at.isoformat(),
                width=image.width,
                height=image.height,
            )
        )

    db.commit()
    return ResponseModel(data=saved_images)


# ============================================================
# 内容发布接口（前端: /contents/{contentId}/publish/{platform}）
# ============================================================

@router.post("/{content_id}/publish/{platform}", response_model=ResponseModel)
async def publish_content(
    content_id: int,
    platform: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布内容到指定平台"""
    from app.models.publish_record import PublishRecord
    from app.schemas.publish import PublishResponse

    if platform not in ("xiaohongshu", "wechat"):
        raise HTTPException(status_code=400, detail="不支持的平台")

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if content.status != "approved":
        raise HTTPException(status_code=400, detail="内容未通过审核，无法发布")

    record = PublishRecord(
        content_id=content_id,
        platform=platform,
        status="pending",
    )
    db.add(record)
    db.flush()

    try:
        # TODO: 对接小红书/微信公众号 API
        record.status = "published"
        record.published_at = datetime.now()
        record.post_url = f"https://{'www.xiaohongshu.com' if platform == 'xiaohongshu' else 'mp.weixin.qq.com'}/post/{record.id}"

        content.status = "published"
        content.published_at = datetime.now()

        db.commit()
        db.refresh(record)

        return ResponseModel(
            data=PublishResponse(
                id=record.id,
                content_id=record.content_id,
                content_title=content.title,
                platform=record.platform,
                post_url=record.post_url,
                status=record.status,
                published_at=record.published_at.isoformat(),
                created_at=record.created_at.isoformat(),
            )
        )
    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            data=PublishResponse(
                id=record.id,
                content_id=record.content_id,
                content_title=content.title,
                platform=record.platform,
                status="failed",
                error_message=str(e),
                created_at=record.created_at.isoformat(),
            ),
            code=500,
            message="发布失败",
        )
