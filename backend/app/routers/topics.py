import json
import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.topic import Topic
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicResponse, TopicListResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("", response_model=ResponseModel[TopicListResponse])
def list_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取选题列表"""
    query = db.query(Topic)

    if status:
        query = query.filter(Topic.status == status)
    if keyword:
        query = query.filter(
            or_(
                Topic.title.ilike(f"%{keyword}%"),
                Topic.description.ilike(f"%{keyword}%"),
            )
        )
    if start_date:
        query = query.filter(Topic.created_at >= start_date)
    if end_date:
        query = query.filter(Topic.created_at <= end_date)

    total = query.count()
    items = (
        query.order_by(Topic.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for item in items:
        creator = db.query(User).filter(User.id == item.created_by).first()
        tags = json.loads(item.tags) if item.tags else None
        result.append(
            TopicResponse(
                id=item.id,
                title=item.title,
                description=item.description,
                status=item.status,
                category=item.category,
                tags=tags,
                content_count=item.content_count,
                created_by=item.created_by,
                created_by_name=creator.username if creator else None,
                created_at=item.created_at.isoformat(),
                approved_at=item.approved_at.isoformat() if item.approved_at else None,
            )
        )

    return ResponseModel(
        data=TopicListResponse(
            items=result,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )
    )


@router.get("/{topic_id}", response_model=ResponseModel[TopicResponse])
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取选题详情"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    creator = db.query(User).filter(User.id == topic.created_by).first()
    tags = json.loads(topic.tags) if topic.tags else None

    return ResponseModel(
        data=TopicResponse(
            id=topic.id,
            title=topic.title,
            description=topic.description,
            status=topic.status,
            category=topic.category,
            tags=tags,
            content_count=topic.content_count,
            created_by=topic.created_by,
            created_by_name=creator.username if creator else None,
            created_at=topic.created_at.isoformat(),
            approved_at=topic.approved_at.isoformat() if topic.approved_at else None,
        )
    )


@router.post("", response_model=ResponseModel[TopicResponse])
def create_topic(
    request: TopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建选题"""
    topic = Topic(
        title=request.title,
        description=request.description,
        status="draft",
        category=request.category,
        tags=json.dumps(request.tags or [], ensure_ascii=False),
        created_by=current_user.id,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)

    return ResponseModel(
        data=TopicResponse(
            id=topic.id,
            title=topic.title,
            description=topic.description,
            status=topic.status,
            category=topic.category,
            tags=request.tags,
            content_count=0,
            created_by=topic.created_by,
            created_by_name=current_user.username,
            created_at=topic.created_at.isoformat(),
        )
    )


@router.put("/{topic_id}", response_model=ResponseModel[TopicResponse])
def update_topic(
    topic_id: int,
    request: TopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新选题"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    update_data = request.model_dump(exclude_unset=True)

    if update_data.get("status") == "approved" and topic.status != "approved":
        topic.approved_at = datetime.now()

    for key, value in update_data.items():
        if key == "tags":
            topic.tags = json.dumps(value, ensure_ascii=False)
        else:
            setattr(topic, key, value)

    db.commit()
    db.refresh(topic)

    creator = db.query(User).filter(User.id == topic.created_by).first()
    tags = json.loads(topic.tags) if topic.tags else None

    return ResponseModel(
        data=TopicResponse(
            id=topic.id,
            title=topic.title,
            description=topic.description,
            status=topic.status,
            category=topic.category,
            tags=tags,
            content_count=topic.content_count,
            created_by=topic.created_by,
            created_by_name=creator.username if creator else None,
            created_at=topic.created_at.isoformat(),
            approved_at=topic.approved_at.isoformat() if topic.approved_at else None,
        )
    )


@router.delete("/{topic_id}", response_model=ResponseModel)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除选题"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    db.delete(topic)
    db.commit()
    return ResponseModel(message="删除成功")
