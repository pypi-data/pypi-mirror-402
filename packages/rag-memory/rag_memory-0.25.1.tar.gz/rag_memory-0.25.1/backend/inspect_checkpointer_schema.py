"""Inspect checkpointer table schemas."""

import asyncio
from app.shared.checkpointer import get_or_create_checkpointer
from psycopg_pool import AsyncConnectionPool


async def inspect():
    """Inspect checkpointer table schemas."""
    checkpointer = await get_or_create_checkpointer()

    async with checkpointer.conn.connection() as conn:
        # Get checkpoints table schema
        print("=== CHECKPOINTS TABLE ===")
        result = await conn.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'checkpoints'
            ORDER BY ordinal_position
        """)
        rows = await result.fetchall()
        for row in rows:
            print(f"{row[0]:20} {row[1]:20} {row[3]}")

        print("\n=== CHECKPOINT_WRITES TABLE ===")
        result = await conn.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'checkpoint_writes'
            ORDER BY ordinal_position
        """)
        rows = await result.fetchall()
        for row in rows:
            print(f"{row[0]:20} {row[1]:20} {row[3]}")

        # Get indexes
        print("\n=== INDEXES ===")
        result = await conn.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename IN ('checkpoints', 'checkpoint_writes')
        """)
        rows = await result.fetchall()
        for row in rows:
            print(f"{row[0]}: {row[1]}")


if __name__ == "__main__":
    asyncio.run(inspect())
