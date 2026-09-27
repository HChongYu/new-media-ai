import logging
from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.logging import bind_user_id, reset_context
from app.core.security import decode_token
from app.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Generator[User, None, None]:
    """获取当前登录用户，并将 user_id 绑定到本次请求的日志上下文"""
    payload = decode_token(credentials.credentials)
    if payload is None:
        logger.warning("认证失败：token 无效或已过期")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )
    sub = payload.get("sub")
    if sub is None:
        logger.warning("认证失败：token 中缺少 sub 字段")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )
    user_id: int = int(sub)
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning("认证失败：用户不存在 user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    user_token = bind_user_id(user.id)
    try:
        yield user
    finally:
        reset_context(user_token=user_token)
