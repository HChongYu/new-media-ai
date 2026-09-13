from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    preferred_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 数组
    preferred_formats: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 数组
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    platform_settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 对象
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
