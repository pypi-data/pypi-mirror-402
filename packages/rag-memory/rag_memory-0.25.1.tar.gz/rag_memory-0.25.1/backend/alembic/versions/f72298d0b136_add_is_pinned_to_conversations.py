"""add_is_pinned_to_conversations

Revision ID: f72298d0b136
Revises: 209efbed60a4
Create Date: 2026-01-07 15:51:06.438313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f72298d0b136'
down_revision: Union[str, None] = '209efbed60a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_pinned column with default False
    op.add_column('conversations', sa.Column('is_pinned', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    # Remove is_pinned column
    op.drop_column('conversations', 'is_pinned')
