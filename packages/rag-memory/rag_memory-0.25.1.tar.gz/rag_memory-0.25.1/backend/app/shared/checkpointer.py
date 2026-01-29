"""AsyncPostgresSaver checkpointer singleton for LangGraph state persistence."""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from ..config import get_settings

settings = get_settings()

connection_pool: AsyncConnectionPool | None = None
checkpointer: AsyncPostgresSaver | None = None


async def get_or_create_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create AsyncPostgresSaver singleton.

    Returns an AsyncPostgresSaver instance that persists LangGraph state
    to PostgreSQL using thread IDs.

    Uses psycopg_pool.AsyncConnectionPool with autocommit=True for
    async checkpoint operations.
    """
    global connection_pool, checkpointer

    if checkpointer is None:
        # Convert from asyncpg format to psycopg format
        # postgresql+asyncpg://... -> postgresql://...
        database_url = settings.DATABASE_URL.replace("+asyncpg", "")

        # Create connection pool (don't open in constructor to avoid deprecation warning)
        connection_pool = AsyncConnectionPool(
            database_url,
            min_size=1,
            max_size=10,
            kwargs={"autocommit": True},
            open=False,  # Don't open in constructor
        )

        # Open pool explicitly
        await connection_pool.open()

        # Create AsyncPostgresSaver with the pool
        checkpointer = AsyncPostgresSaver(connection_pool)

        # NOTE: We do NOT call setup() here - schema is managed by Alembic migrations

    return checkpointer
