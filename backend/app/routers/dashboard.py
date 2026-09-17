import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.topic import Topic
from app.models.content import Content
from app.models.image import Image
from app.models.publish_record import PublishRecord
from app.schemas.common import ResponseModel
from app.schemas.dashboard import DashboardStats, ActivityItem

router = APIRouter()
logger = logging.getLogger(__name__)

# 最近活动返回条数；每张表最多取该数量（数据库侧 LIMIT，不拉全量）
RECENT_LIMIT = 8

PLATFORM_NAMES = {
    "xiaohongshu": "小红书",
    "wechat": "公众号",
}


@router.get("/stats", response_model=ResponseModel[DashboardStats])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """仪表盘统计数据（总量统计 + 全局最近活动）"""
    # ---- 总量统计（统计口径：对应表全量计数）----
    total_topics = db.query(Topic).count()
    total_contents = db.query(Content).count()
    total_images = db.query(Image).count()
    # 已发布内容：内容状态为 published
    published_count = (
        db.query(Content).filter(Content.status == "published").count()
    )

    # ---- 各表最近记录（按各自时间字段倒序，数据库侧 LIMIT）----
    recent_topics = (
        db.query(Topic).order_by(Topic.created_at.desc())
        .limit(RECENT_LIMIT).all()
    )
    recent_contents = (
        db.query(Content).order_by(Content.created_at.desc())
        .limit(RECENT_LIMIT).all()
    )
    recent_images = (
        db.query(Image).order_by(Image.generated_at.desc())
        .limit(RECENT_LIMIT).all()
    )
    recent_publishes = (
        db.query(PublishRecord).order_by(PublishRecord.created_at.desc())
        .limit(RECENT_LIMIT).all()
    )

    # 批量补齐图片 / 发布记录关联的内容标题（一次 IN 查询，避免 N+1）
    content_ids = {item.content_id for item in recent_images}
    content_ids.update(item.content_id for item in recent_publishes)
    content_title_map: dict[int, str] = {}
    if content_ids:
        rows = (
            db.query(Content.id, Content.title)
            .filter(Content.id.in_(content_ids))
            .all()
        )
        content_title_map = {row.id: row.title for row in rows}

    # ---- 聚合为统一活动流，内部携带 datetime 用于排序 ----
    activities: list[tuple[datetime, ActivityItem]] = []

    for topic in recent_topics:
        activities.append((
            topic.created_at,
            ActivityItem(
                type="topic",
                ref_id=topic.id,
                title=f"新建选题：{topic.title}",
                time=topic.created_at.isoformat(),
            ),
        ))

    for content in recent_contents:
        activities.append((
            content.created_at,
            ActivityItem(
                type="content",
                ref_id=content.id,
                title=f"创建内容：{content.title}",
                time=content.created_at.isoformat(),
            ),
        ))

    for image in recent_images:
        content_title = content_title_map.get(image.content_id)
        title = f"为《{content_title}》生成配图" if content_title else "生成配图"
        activities.append((
            image.generated_at,
            ActivityItem(
                type="image",
                ref_id=image.id,
                title=title,
                time=image.generated_at.isoformat(),
            ),
        ))

    for record in recent_publishes:
        platform_name = PLATFORM_NAMES.get(record.platform, record.platform)
        content_title = content_title_map.get(record.content_id)
        title = (
            f"发布到{platform_name}：{content_title}"
            if content_title
            else f"发布到{platform_name}"
        )
        activities.append((
            record.created_at,
            ActivityItem(
                type="publish",
                ref_id=record.id,
                title=title,
                time=record.created_at.isoformat(),
            ),
        ))

    # 全局按时间倒序取前 N 条
    activities.sort(key=lambda pair: pair[0], reverse=True)
    recent_activities = [item for _, item in activities[:RECENT_LIMIT]]

    return ResponseModel(
        data=DashboardStats(
            total_topics=total_topics,
            total_contents=total_contents,
            total_images=total_images,
            published_count=published_count,
            recent_activities=recent_activities,
        )
    )
