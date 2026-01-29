"""add_trust_system

Revision ID: 002_trust_system
Revises: 001_baseline
Create Date: 2025-01-10

Adds trust-aware memory system:
- trust_state column on source_documents (trusted/needs_review)
- ingest_audit_log table for tracking ingestion provenance

Schema changes:
- source_documents.trust_state: VARCHAR(20) with CHECK constraint
- ingest_audit_log: append-only audit trail for all ingestion operations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '002_trust_system'
down_revision: Union[str, Sequence[str], None] = '001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trust_state column and ingest_audit_log table."""

    # Add trust_state column to source_documents
    op.add_column(
        'source_documents',
        sa.Column(
            'trust_state',
            sa.String(length=20),
            nullable=False,
            server_default='needs_review'
        )
    )

    # Add CHECK constraint for valid trust states
    op.execute("""
        ALTER TABLE source_documents
        ADD CONSTRAINT trust_state_valid
        CHECK (trust_state IN ('trusted', 'needs_review'))
    """)

    # Add index for efficient trust state filtering
    op.create_index(
        'source_documents_trust_state_idx',
        'source_documents',
        ['trust_state']
    )

    # Create ingest_audit_log table (append-only audit trail)
    op.create_table(
        'ingest_audit_log',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False),

        # Document reference (nullable - document may be deleted, audit preserved)
        sa.Column('source_document_id', sa.Integer(), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),

        # Actor identification
        sa.Column('actor_type', sa.String(length=50), nullable=False),  # 'user', 'agent', 'api'
        sa.Column('actor_id', sa.String(length=255), nullable=True),    # e.g., 'claude-desktop', 'slack-agent'

        # Ingestion details
        sa.Column('ingest_method', sa.String(length=50), nullable=False),  # 'text', 'file', 'directory', 'url'
        sa.Column('collection_name', sa.String(length=255), nullable=False),

        # Dry run tracking
        sa.Column('dry_run_performed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dry_run_recommendation', sa.String(length=20), nullable=True),  # 'ingest', 'review', 'skip'
        sa.Column('dry_run_score', sa.Numeric(precision=3, scale=2), nullable=True),  # 0.00-1.00
        sa.Column('dry_run_summary', sa.Text(), nullable=True),

        # Override tracking
        sa.Column('user_override', sa.Boolean(), nullable=False, server_default='false'),

        # Trust assignment
        sa.Column('trust_state_assigned', sa.String(length=20), nullable=False),
        sa.Column('trust_assignment_reason', sa.Text(), nullable=False),

        # Provenance
        sa.Column('mcp_server_version', sa.String(length=50), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),       # For URL ingests
        sa.Column('source_file_path', sa.Text(), nullable=True), # For file ingests

        # Extensible metadata
        sa.Column('metadata', JSONB(), nullable=True, server_default='{}'),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['source_document_id'],
            ['source_documents.id'],
            ondelete='SET NULL'  # Preserve audit even if document deleted
        ),
    )

    # Add CHECK constraint for valid trust states in audit log
    op.execute("""
        ALTER TABLE ingest_audit_log
        ADD CONSTRAINT audit_trust_state_valid
        CHECK (trust_state_assigned IN ('trusted', 'needs_review'))
    """)

    # Add CHECK constraint for valid actor types
    op.execute("""
        ALTER TABLE ingest_audit_log
        ADD CONSTRAINT audit_actor_type_valid
        CHECK (actor_type IN ('user', 'agent', 'api'))
    """)

    # Add CHECK constraint for valid ingest methods
    op.execute("""
        ALTER TABLE ingest_audit_log
        ADD CONSTRAINT audit_ingest_method_valid
        CHECK (ingest_method IN ('text', 'file', 'directory', 'url'))
    """)

    # Add CHECK constraint for valid dry run recommendations
    op.execute("""
        ALTER TABLE ingest_audit_log
        ADD CONSTRAINT audit_dry_run_recommendation_valid
        CHECK (dry_run_recommendation IS NULL OR dry_run_recommendation IN ('ingest', 'review', 'skip'))
    """)

    # Create indexes for common query patterns
    op.create_index(
        'ingest_audit_log_doc_idx',
        'ingest_audit_log',
        ['source_document_id']
    )
    op.create_index(
        'ingest_audit_log_collection_idx',
        'ingest_audit_log',
        ['collection_name']
    )
    op.create_index(
        'ingest_audit_log_created_idx',
        'ingest_audit_log',
        ['created_at'],
        postgresql_ops={'created_at': 'DESC'}
    )


def downgrade() -> None:
    """Remove trust system - drop audit table and trust_state column."""

    # Drop ingest_audit_log table
    op.drop_table('ingest_audit_log')

    # Drop trust_state index
    op.drop_index('source_documents_trust_state_idx', table_name='source_documents')

    # Drop CHECK constraint
    op.execute("ALTER TABLE source_documents DROP CONSTRAINT IF EXISTS trust_state_valid")

    # Drop trust_state column
    op.drop_column('source_documents', 'trust_state')
