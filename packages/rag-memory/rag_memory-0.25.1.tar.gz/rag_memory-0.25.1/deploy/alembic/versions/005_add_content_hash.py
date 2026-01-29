"""add_content_hash

Revision ID: 005_content_hash
Revises: 004_rename_topic
Create Date: 2025-01-11

Adds content_hash column to source_documents for reliable duplicate detection.
SHA256 hash of document content enables detecting duplicates regardless of
filename or path - same content = same hash.

Also includes optional backfill to compute hashes for existing documents.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_content_hash'
down_revision: Union[str, Sequence[str], None] = '004_rename_topic'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add content_hash column and index."""
    # Add nullable column first (allows backfill)
    op.add_column(
        'source_documents',
        sa.Column('content_hash', sa.String(64), nullable=True)
    )

    # Create index for fast duplicate lookups
    op.create_index(
        'idx_source_documents_content_hash',
        'source_documents',
        ['content_hash']
    )

    # Backfill existing documents with computed hashes
    # SHA256 produces 64 hex characters
    op.execute("""
        UPDATE source_documents
        SET content_hash = encode(sha256(content::bytea), 'hex')
        WHERE content_hash IS NULL
    """)


def downgrade() -> None:
    """Remove content_hash column and index."""
    op.drop_index('idx_source_documents_content_hash', 'source_documents')
    op.drop_column('source_documents', 'content_hash')
