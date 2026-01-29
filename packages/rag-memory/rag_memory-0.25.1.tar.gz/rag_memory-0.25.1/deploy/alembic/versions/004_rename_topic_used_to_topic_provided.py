"""rename_topic_used_to_topic_provided

Revision ID: 004_rename_topic
Revises: 003_evaluation_system
Create Date: 2025-01-11

Renames the topic_used column to topic_provided for clearer semantics.
The field name "topic_provided" better communicates that this is what
the caller provided for evaluation, not what the system "used".
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '004_rename_topic'
down_revision: Union[str, Sequence[str], None] = '003_evaluation_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename topic_used to topic_provided."""
    op.execute("ALTER TABLE source_documents RENAME COLUMN topic_used TO topic_provided")


def downgrade() -> None:
    """Rename topic_provided back to topic_used."""
    op.execute("ALTER TABLE source_documents RENAME COLUMN topic_provided TO topic_used")
