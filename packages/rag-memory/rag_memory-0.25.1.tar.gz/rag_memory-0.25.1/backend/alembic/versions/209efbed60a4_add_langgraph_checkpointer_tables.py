"""add_langgraph_checkpointer_tables

Revision ID: 209efbed60a4
Revises: eb0488e04b85
Create Date: 2026-01-07 14:48:17.056063

DEPRECATED: LangGraph manages its own checkpoint tables via PostgresSaver.setup().
Tables are created automatically on backend startup in main.py.
This migration is kept as a no-op to preserve the migration chain.
"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '209efbed60a4'
down_revision: Union[str, None] = 'eb0488e04b85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NO-OP: LangGraph manages checkpoint tables via PostgresSaver.setup()
    # Called automatically on backend startup in app/main.py
    pass


def downgrade() -> None:
    # NO-OP: LangGraph tables are managed by LangGraph, not Alembic
    pass
