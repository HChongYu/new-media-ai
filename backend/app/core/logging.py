"""
统一日志配置

- 基于标准库 logging，无需 structlog / loguru 等额外依赖
- 通过 contextvars 在同一请求 / 工作流执行链路内自动注入
  request_id / thread_id / user_id，实现日志关联
- 开发环境输出易读文本格式；LOG_JSON_FORMAT=true 时输出 JSON（便于日志平台采集）

使用方式：
    # 应用启动时（main.py 导入阶段）调用一次
    from app.core.logging import setup_logging
    setup_logging()

    # 业务代码中按常规方式取 logger 即可，上下文字段自动注入
    import logging
    logger = logging.getLogger(__name__)
    logger.info("工作流启动")
"""
import contextvars
import json
import logging
import logging.config
import sys
from datetime import datetime
from types import TracebackType
from typing import Any

from app.config import settings

# 链路上下文字段：每个请求一个独立的 asyncio Task，ContextVar 在 Task 间隔离，
# 不会出现请求间串值的问题
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
thread_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "thread_id", default=None
)
user_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "user_id", default=None
)

# JSON / 文本格式中统一使用的占位值
_EMPTY = "-"

# 文本日志格式：时间 | 级别 | logger 名 | 链路标识 | 消息
_TEXT_FORMAT = (
    "%(asctime)s | %(levelname)-7s | %(name)s | "
    "req=%(request_id)s thread=%(thread_id)s user=%(user_id)s | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ContextFilter(logging.Filter):
    """为每条日志记录补充链路上下文字段"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or _EMPTY
        record.thread_id = thread_id_var.get() or _EMPTY
        record.user_id = user_id_var.get() or _EMPTY
        return True


class JsonFormatter(logging.Formatter):
    """JSON 结构化日志格式（生产 / 日志平台采集场景）"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", _EMPTY),
            "thread_id": getattr(record, "thread_id", _EMPTY),
            "user_id": getattr(record, "user_id", _EMPTY),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # 其它通过 extra= 传入的结构化字段也一并保留
        standard_attrs = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__)
        for key, value in record.__dict__.items():
            if key not in standard_attrs and key not in payload:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def bind_request_id(request_id: str) -> contextvars.Token[str | None]:
    """绑定当前请求的 request_id，返回 token 用于事后 reset"""
    return request_id_var.set(request_id)


def bind_thread_id(thread_id: str) -> contextvars.Token[str | None]:
    """绑定当前执行中的工作流 thread_id"""
    return thread_id_var.set(thread_id)


def bind_user_id(user_id: int) -> contextvars.Token[int | None]:
    """绑定当前登录用户 id"""
    return user_id_var.set(user_id)


def reset_context(
    request_token: contextvars.Token[str | None] | None = None,
    thread_token: contextvars.Token[str | None] | None = None,
    user_token: contextvars.Token[int | None] | None = None,
) -> None:
    """按 token 还原上下文（参数为 None 的字段跳过）"""
    if request_token is not None:
        request_id_var.reset(request_token)
    if thread_token is not None:
        thread_id_var.reset(thread_token)
    if user_token is not None:
        user_id_var.reset(user_token)


class log_context:  # noqa: N801 - 作为上下文管理器使用，保留小写风格
    """
    临时绑定链路字段的上下文管理器。

    示例：
        with log_context(thread_id="abc-123"):
            logger.info("节点执行中")  # 自动带上 thread_id
    """

    def __init__(
        self,
        *,
        request_id: str | None = None,
        thread_id: str | None = None,
        user_id: int | None = None,
    ) -> None:
        self._request_id = request_id
        self._thread_id = thread_id
        self._user_id = user_id
        self._tokens: list[contextvars.Token[Any]] = []

    def __enter__(self) -> "log_context":
        if self._request_id is not None:
            self._tokens.append(request_id_var.set(self._request_id))
        if self._thread_id is not None:
            self._tokens.append(thread_id_var.set(self._thread_id))
        if self._user_id is not None:
            self._tokens.append(user_id_var.set(self._user_id))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # 按 set 的逆序 reset
        for token in reversed(self._tokens):
            token.var.reset(token)


def setup_logging() -> None:
    """
    初始化全局日志配置，应用启动时调用一次即可。

    - 所有日志统一输出到 stdout（容器环境由外部采集）
    - uvicorn.access 被关闭，HTTP 访问日志由 main.py 中的中间件统一输出
      （含 request_id 与耗时，避免重复记录）
    """
    log_level = settings.LOG_LEVEL.upper()
    formatter_name = "json" if settings.LOG_JSON_FORMAT else "text"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "context": {
                "()": ContextFilter,
            }
        },
        "formatters": {
            "text": {
                "format": _TEXT_FORMAT,
                "datefmt": _DATE_FORMAT,
            },
            "json": {
                "()": JsonFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": formatter_name,
                "filters": ["context"],
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            # 应用代码可通过 LOG_LEVEL 单独控制
            "app": {"level": log_level},
            # uvicorn 自身日志交给 root handler，保持格式统一
            "uvicorn": {"level": "INFO", "handlers": [], "propagate": True},
            "uvicorn.error": {"level": "INFO", "handlers": [], "propagate": True},
            # 访问日志由业务中间件输出（带 request_id / 耗时），关闭默认 access logger
            "uvicorn.access": {"handlers": [], "propagate": False},
        },
    }
    logging.config.dictConfig(config)
