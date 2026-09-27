import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.logging import setup_logging, bind_request_id, reset_context
from app.database import engine, Base
from app.routers import (
    auth,
    topics,
    contents,
    images,
    workflows,
    publish,
    settings as settings_router,
    dashboard,
    prompts,
)
from app.graph.workflow import init_workflow, shutdown_workflow

# 必须在创建 app 前完成日志初始化，使启动阶段日志也走统一配置
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    # Base.metadata.create_all(bind=engine)

    # 初始化 LangGraph Checkpointer 并编译统一工作流
    await init_workflow()

    # 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    yield

    # 释放 Checkpointer 连接
    await shutdown_workflow()


app = FastAPI(
    title="AI 自媒体运营平台",
    description="基于 LangGraph 的 AI 自媒体内容生成与发布系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 访问日志中间件：为每个请求生成 / 透传 request_id，记录方法、路径、状态码与耗时。
# 注意：刻意不记录 Authorization 等任何请求头，避免 token 等敏感信息写入日志。
@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    # 优先透传上游传入的 request_id，便于全链路排查；没有则生成
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    ctx_token = bind_request_id(request_id)

    start = time.perf_counter()
    status_code = 500
    response = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        logger.exception("请求处理异常: %s %s", request.method, request.url.path)
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        if response is not None:
            # 响应头回传，前端 / 调用方可凭此 id 定位日志
            response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )
        reset_context(request_token=ctx_token)

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
app.include_router(workflows.router, prefix="/api/workflows", tags=["统一工作流"])
app.include_router(publish.router, prefix="/api/publish", tags=["发布"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["设置"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["提示词管理"])


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "message": "AI 自媒体运营平台运行中"}
