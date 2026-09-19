"""
业务表 content_projects：工作流运行元数据（用于前端列表与历史归档）

与 LangGraph checkpoints 的分工：
- checkpoints（langgraph_checkpoints.db / PostgreSQL 自动建表）：
  保存完整图状态，支撑中断 / 恢复；
- content_projects：保存面向业务展示的快照字段，通过 thread_id 关联。
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid_hex() -> str:
    return uuid.uuid4().hex


class ContentProject(Base):
    __tablename__ = "content_projects"

    # 设计上使用 UUID（36 位 hex 字符串，SQLite/PostgreSQL 均可移植）
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    # 关联 LangGraph thread_id，恢复工作流的关键
    thread_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=_uuid_hex)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    topic_direction: Mapped[str] = mapped_column(String(500), default="")
    topic: Mapped[str] = mapped_column(String(300), default="")  # 最终确定的选题
    platform: Mapped[str] = mapped_column(String(20), default="xiaohongshu")

    # awaiting_select 选题中 / writing 撰稿中 / reviewing 审核中 /
    # generating_images 生成图片中 / completed 已完成
    status: Mapped[str] = mapped_column(String(30), default="awaiting_select")

    # 最终文案与图片资产（JSON 快照，完成时写入）
    article_content: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    image_assets: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)

    revision_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
