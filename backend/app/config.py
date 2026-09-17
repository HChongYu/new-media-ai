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
    IMAGE_PROVIDER: str = "mock"  # sensenova / openai / local / mock
    SD_WEBUI_URL: str = "http://127.0.0.1:7860"  # 本地 Stable Diffusion WebUI 地址

    # 商汤 SenseNova 文生图（provider=sensenova 时生效）
    IMAGE_MODEL: str = "sensenova-u1-fast"
    IMAGE_API_BASE: str = ""  # 留空则复用 LLM_API_BASE
    IMAGE_API_KEY: str = ""  # 留空则复用 LLM_API_KEY
    IMAGE_WATERMARK: bool = True  # 是否带官方水印（官方建议显式传参）

    # 文件上传
    UPLOAD_DIR: str = "uploads"

    # 内容发布
    PUBLISH_MODE: str = "simulate"  # simulate（开发模拟）/ live（对接真实平台 API）
    # 微信公众号（live 模式下必填，在公众号后台「设置与开发」中获取）
    WECHAT_APPID: str = ""
    WECHAT_APPSECRET: str = ""
    # IP 白名单不生效时可使用中控服务获取的稳定 access_token（可选）
    WECHAT_ACCESS_TOKEN_URL: str = ""

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
