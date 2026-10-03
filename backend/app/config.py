from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "AI自媒体运营平台"
    DEBUG: bool = True

    # 日志
    LOG_LEVEL: str = "INFO"  # DEBUG / INFO / WARNING / ERROR
    LOG_JSON_FORMAT: bool = False  # 生产环境建议 true，输出 JSON 结构化日志

    # 数据库
    # PostgreSQL: postgresql+psycopg://user:password@localhost:5432/op_ai
    # SQLite (开发用): sqlite:///./op_ai.db
    DATABASE_URL: str = "sqlite:///./op_ai.db"

    # LangGraph Checkpointer 连接（留空时自动跟随 DATABASE_URL）
    # - PostgreSQL：直接使用 postgresql://user:password@host:5432/db
    # - SQLite 开发环境：默认使用独立文件 langgraph_checkpoints.db
    #   也可显式指定文件路径或 sqlite:///./xxx.db
    LANGGRAPH_DB_URL: str = ""

    # Checkpointer 后端开关：
    # auto   -> 跟随 LANGGRAPH_DB_URL / DATABASE_URL 自动选择（默认）
    # memory -> 纯内存 mock，不依赖任何数据库，重启后状态丢失（仅本地开发/测试）
    CHECKPOINTER_BACKEND: str = "auto"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # LLM
    LLM_PROVIDER: str = "openai"  # openai / anthropic / local / mock
    LLM_MODEL: str = "gpt-4"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = ""  # 本地模型或代理地址

    # LLM 容错：主备 fallback 链 + 熔断器
    # 备用模型名（逗号分隔，按顺序尝试），复用同一 provider / API Key / Base URL；
    # 留空则只有主模型。示例："sensenova-6.8-flash,sensenova-5"
    LLM_FALLBACK_MODELS: str = ""
    LLM_CIRCUIT_FAILURE_THRESHOLD: int = 5  # 单模型连续失败次数达到后跳闸
    LLM_CIRCUIT_RECOVERY_SECONDS: int = 30  # 熔断打开后的冷却时间，到期后半开试探

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
