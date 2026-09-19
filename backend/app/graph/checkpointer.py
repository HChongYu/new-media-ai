"""
Checkpointer 工厂与生命周期管理

按配置自动选择持久化后端：
- postgresql*  -> AsyncPostgresSaver（生产，需 langgraph-checkpoint-postgres + psycopg）
- sqlite / 其它 -> AsyncSqliteSaver（开发默认，独立文件 langgraph_checkpoints.db）
- 依赖缺失等异常 -> MemorySaver（仅内存，重启丢失，只能用于临时调试）

业务库（SQLAlchemy 同步引擎）与 Checkpoint 库在 SQLite 模式下使用不同文件，
避免同步连接与 aiosqlite 连接争抢同一个库文件。
"""
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# SQLite 开发环境下的 checkpointer 专用文件（CWD 为 backend/）
_SQLITE_CHECKPOINT_FILE = "langgraph_checkpoints.db"


def _resolve_backend() -> tuple[str, str]:
    """返回 (backend, conn_string)"""
    override = settings.LANGGRAPH_DB_URL.strip()

    if override:
        if override.startswith(("postgresql://", "postgresql+")):
            return "postgres", override
        if override.startswith("sqlite:///"):
            return "sqlite", override.removeprefix("sqlite:///")
        return "sqlite", override

    db_url = settings.DATABASE_URL.strip()
    if db_url.startswith(("postgresql://", "postgresql+")):
        # psycopg 的 conninfo 不接受 +psycopg 后缀
        return "postgres", db_url.replace("+psycopg", "", 1)

    # 开发环境（SQLite）：与业务库分文件
    return "sqlite", _SQLITE_CHECKPOINT_FILE


class CheckpointerLifecycle:
    """持有长连接与 checkpointer 实例，随 FastAPI lifespan 初始化 / 关闭"""

    def __init__(self) -> None:
        self.backend: str = ""
        self._saver = None
        self._conn = None  # aiosqlite / psycopg 原生连接

    @property
    def saver(self):
        return self._saver

    async def startup(self) -> None:
        backend, conn_string = _resolve_backend()
        self.backend = backend

        if backend == "postgres":
            self._saver = await self._start_postgres(conn_string)
        else:
            self._saver = await self._start_sqlite(conn_string)

    async def _start_sqlite(self, db_path: str):
        try:
            import aiosqlite
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        except ImportError:
            logger.warning(
                "未安装 langgraph-checkpoint-sqlite / aiosqlite，"
                "降级为 MemorySaver（重启后工作流状态会丢失）"
            )
            return self._memory_saver()

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(db_path)
        saver = AsyncSqliteSaver(self._conn)
        await saver.setup()  # 自动创建 checkpoints / writes 等表
        logger.info("LangGraph Checkpointer 使用 SQLite：%s", db_path)
        return saver

    async def _start_postgres(self, conn_string: str):
        try:
            import psycopg
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        except ImportError as exc:
            raise RuntimeError(
                "使用 PostgreSQL 作为 Checkpointer 需要安装依赖：\n"
                "  pip install langgraph-checkpoint-postgres 'psycopg[binary]'"
            ) from exc

        # kwargs 与 SQLAlchemy 配置保持一致，避免空闲连接被数据库断开
        self._conn = await psycopg.AsyncConnection.connect(
            conn_string,
            autocommit=True,
            prepare_threshold=0,
        )
        saver = AsyncPostgresSaver(self._conn)
        await saver.setup()  # 首次运行自动建表
        logger.info("LangGraph Checkpointer 使用 PostgreSQL")
        return saver

    @staticmethod
    def _memory_saver():
        from langgraph.checkpoint.memory import MemorySaver

        logger.warning("当前使用 MemorySaver，工作流状态仅保存在进程内存中")
        return MemorySaver()

    async def shutdown(self) -> None:
        if self._conn is not None:
            try:
                await self._conn.close()
            except Exception:  # noqa: BLE001 - 关闭阶段异常无需上抛
                logger.exception("关闭 Checkpointer 连接时出现异常")
        self._conn = None
        self._saver = None


# 全局单例（在 main.py lifespan 中初始化）
checkpointer_lifecycle = CheckpointerLifecycle()
