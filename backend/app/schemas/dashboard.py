from pydantic import BaseModel


class ActivityItem(BaseModel):
    """最近活动项"""
    type: str  # topic / content / image / publish
    ref_id: int
    title: str
    time: str  # ISO 8601


class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    total_topics: int
    total_contents: int
    total_images: int
    published_count: int
    recent_activities: list[ActivityItem]
