from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.core.security import verify_password, hash_password, create_token
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, UserResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/login", response_model=ResponseModel[LoginResponse])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == request.username).first()
    print(f"[DEBUG] 登录尝试 - 用户名: {request.username}")
    print(f"[DEBUG] 数据库查询结果 - user: {user}")
    if user:
        print(f"[DEBUG] 用户详情 - ID: {user.id}, Username: {user.username}, Email: {user.email}")
        print(f"[DEBUG] 密码验证 - 传入密码: {request.password}, 哈希值: {user.hashed_password[:20]}...")
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token({"sub": user.id})

    return ResponseModel(
        data=LoginResponse(
            token=token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar=user.avatar,
                role=user.role,
                created_at=user.created_at.isoformat(),
            ),
        )
    )


@router.post("/logout", response_model=ResponseModel)
def logout(current_user: User = Depends(get_current_user)):
    """用户登出（客户端清除 token 即可）"""
    return ResponseModel(message="登出成功")


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return ResponseModel(
        data=UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            avatar=current_user.avatar,
            role=current_user.role,
            created_at=current_user.created_at.isoformat(),
        )
    )
