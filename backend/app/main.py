from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.routers import auth, topics, contents, images, publish, settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)

    # 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    yield


app = FastAPI(
    title="AI 自媒体运营平台",
    description="基于 LangGraph 的 AI 自媒体内容生成与发布系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 调试中间件：打印所有请求头
@app.middleware("http")
async def log_requests(request, call_next):
    auth = request.headers.get("Authorization", "无")
    print(f"[DEBUG] {request.method} {request.url.path} - Authorization: {auth[:30] if auth != '无' else '无'}...")
    response = await call_next(request)
    return response

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（上传的文件）
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# 注册路由（前缀与前端 API 定义一致）
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(topics.router, prefix="/api/topics", tags=["选题"])
app.include_router(contents.router, prefix="/api/contents", tags=["内容"])
app.include_router(images.router, prefix="/api/images", tags=["图片"])
app.include_router(publish.router, prefix="/api/publish", tags=["发布"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["设置"])


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "message": "AI 自媒体运营平台运行中"}
