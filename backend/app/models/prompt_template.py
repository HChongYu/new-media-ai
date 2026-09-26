from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PromptTemplate(Base):
    """提示词模板版本表

    每个逻辑提示词（key，如 topic_plan）可以拥有多个 version：
    - status: draft 草稿 / active 生效中 / archived 已归档
    - 正常情况下同一 key 只有一条 active（variant='main'，主干版本）
    - A/B 实验时同一 key 可同时存在多条 active：
      variant='main' 为主干（吃剩余流量），其余为实验变体，
      traffic_percent 标记 0-100 的流量占比，按 thread_id 哈希确定性分桶
    """

    __tablename__ = "prompt_templates"
    __table_args__ = (
        UniqueConstraint("key", "version", name="uq_prompt_key_version"),
        Index("ix_prompt_key_status", "key", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50))  # 逻辑标识：topic_plan / draft_writing / visual_points
    version: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))  # 展示名称
    content: Mapped[str] = mapped_column(Text)
    change_note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    variant: Mapped[str] = mapped_column(String(50), default="main")
    traffic_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
