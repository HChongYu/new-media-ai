from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "editor"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar: str | None = None
    role: str
    created_at: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse
