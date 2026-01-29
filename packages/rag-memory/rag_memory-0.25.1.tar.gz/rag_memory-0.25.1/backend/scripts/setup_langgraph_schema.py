"""
Script to set up PostgreSQL schema for LangGraph checkpointing.

This script creates the required database tables for LangGraph's AsyncPostgresSaver.
It is idempotent - safe to run multiple times.

Tables created:
- checkpoints: Stores conversation state snapshots
- checkpoint_writes: Stores pending writes/updates
- checkpoint_blobs: Stores large binary data
- checkpoint_migrations: Tracks schema version

Usage:
    python scripts/setup_langgraph_schema.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

# Set up basic logging for this script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

settings = get_settings()


async def setup_langgraph_tables():
    """Set up LangGraph checkpoint tables in the database.

    Uses the application's config system to get the database URL.
    """
    try:
        # Get database URL from settings
        # Convert from asyncpg format to psycopg format
        # asyncpg: postgresql+asyncpg://...
        # psycopg: postgresql://...
        database_url = settings.DATABASE_URL.replace("+asyncpg", "")

        logger.info("Initializing LangGraph PostgreSQL tables...")

        # Create connection pool
        async with AsyncConnectionPool(
            database_url,
            min_size=1,
            max_size=10,
            kwargs={"autocommit": True},
        ) as pool:
            # Create AsyncPostgresSaver
            checkpointer = AsyncPostgresSaver(pool)

            # Run setup to create tables (idempotent - safe to run multiple times)
            await checkpointer.setup()

        logger.info("Successfully created LangGraph checkpoint tables in PostgreSQL")
        return True
    except Exception as e:
        logger.error(f"Failed to create LangGraph tables: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_langgraph_tables())
