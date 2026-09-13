from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "AI自媒体运营平台"
    DEBUG: bool = True

    # 数据库
    # PostgreSQL: postgresql+psycopg://user:password@localhost:5432/op_ai
    # SQLite (开发用): sqlite:///./op_ai.db
    DATABASE_URL: str = "sqlite:///./op_ai.db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # LLM
    LLM_PROVIDER: str = "openai"  # openai / anthropic / local
    LLM_MODEL: str = "gpt-4"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = ""  # 本地模型或代理地址

    # 图片生成
    IMAGE_PROVIDER: str = "mock"  # openai / local / mock

    # 文件上传
    UPLOAD_DIR: str = "uploads"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
