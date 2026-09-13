from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.settings import Settings
from app.schemas.settings import SettingsUpdate, SettingsResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("", response_model=ResponseModel[SettingsResponse | None])
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取系统设置"""
    settings = (
        db.query(Settings)
        .filter(Settings.user_id == current_user.id)
        .first()
    )

    if not settings:
        return ResponseModel(data=None)

    return ResponseModel(
        data=SettingsResponse(
            id=settings.id,
            user_id=settings.user_id,
            preferred_topics=settings.preferred_topics or [],
            preferred_formats=settings.preferred_formats or [],
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            image_style=settings.image_style,
            platform_settings=settings.platform_settings or {},
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat(),
        )
    )


@router.put("", response_model=ResponseModel[SettingsResponse])
def update_settings(
    request: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新系统设置"""
    settings = (
        db.query(Settings)
        .filter(Settings.user_id == current_user.id)
        .first()
    )

    if not settings:
        # 首次创建设置
        settings = Settings(user_id=current_user.id)
        db.add(settings)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    return ResponseModel(
        data=SettingsResponse(
            id=settings.id,
            user_id=settings.user_id,
            preferred_topics=settings.preferred_topics or [],
            preferred_formats=settings.preferred_formats or [],
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            image_style=settings.image_style,
            platform_settings=settings.platform_settings or {},
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat(),
        )
    )
