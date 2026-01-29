"""add_evaluation_system

Revision ID: 003_evaluation_system
Revises: 002_trust_system
Create Date: 2025-01-10

Replaces trust semantics with universal LLM evaluation:
- Removes trust_state from source_documents
- Removes trust_state_assigned, trust_assignment_reason from ingest_audit_log
- Keeps user_override in audit (valuable provenance)
- Adds reviewed_by_human boolean to source_documents
- Adds evaluation fields: quality_score, quality_summary, topic_relevance_*

Design principle: "Persist only primitive facts that are durable and hard to regret."
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_evaluation_system'
down_revision: Union[str, Sequence[str], None] = '002_trust_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove trust semantics, add evaluation fields."""

    # =========================================================================
    # 1. Remove trust_state from source_documents
    # =========================================================================

    # Drop the index first
    op.drop_index('source_documents_trust_state_idx', table_name='source_documents')

    # Drop the CHECK constraint
    op.execute("ALTER TABLE source_documents DROP CONSTRAINT IF EXISTS trust_state_valid")

    # Drop the column
    op.drop_column('source_documents', 'trust_state')

    # =========================================================================
    # 2. Clean up audit table (remove trust-assignment fields, keep provenance)
    # =========================================================================

    # Drop trust-related constraint
    op.execute("ALTER TABLE ingest_audit_log DROP CONSTRAINT IF EXISTS audit_trust_state_valid")

    # Drop trust_state_assigned column
    op.drop_column('ingest_audit_log', 'trust_state_assigned')

    # Drop trust_assignment_reason column
    op.drop_column('ingest_audit_log', 'trust_assignment_reason')

    # NOTE: user_override is KEPT - valuable provenance ("model said skip but user proceeded")

    # =========================================================================
    # 3. Add reviewed_by_human flag
    # =========================================================================

    op.add_column(
        'source_documents',
        sa.Column(
            'reviewed_by_human',
            sa.Boolean(),
            nullable=False,
            server_default='false'
        )
    )

    # Index for filtering by review status
    op.create_index(
        'source_documents_reviewed_idx',
        'source_documents',
        ['reviewed_by_human']
    )

    # =========================================================================
    # 4. Add LLM evaluation fields
    # =========================================================================

    # Quality assessment (always populated on every ingest)
    op.add_column(
        'source_documents',
        sa.Column(
            'quality_score',
            sa.Numeric(precision=4, scale=3),  # 0.000-1.000
            nullable=True  # Nullable for existing docs before migration
        )
    )

    op.add_column(
        'source_documents',
        sa.Column(
            'quality_summary',
            sa.Text(),
            nullable=True
        )
    )

    # Topic relevance (only populated when caller provides topic)
    op.add_column(
        'source_documents',
        sa.Column(
            'topic_relevance_score',
            sa.Numeric(precision=4, scale=3),  # 0.000-1.000
            nullable=True  # NULL if no topic provided
        )
    )

    op.add_column(
        'source_documents',
        sa.Column(
            'topic_relevance_summary',
            sa.Text(),
            nullable=True  # NULL if no topic provided
        )
    )

    op.add_column(
        'source_documents',
        sa.Column(
            'topic_used',
            sa.Text(),
            nullable=True  # Echo of provided topic, NULL if none
        )
    )

    # Evaluation metadata
    op.add_column(
        'source_documents',
        sa.Column(
            'eval_model',
            sa.String(length=100),
            nullable=True
        )
    )

    op.add_column(
        'source_documents',
        sa.Column(
            'eval_timestamp',
            sa.DateTime(),
            nullable=True
        )
    )

    # =========================================================================
    # 5. Create indexes for query filtering
    # =========================================================================

    op.create_index(
        'source_documents_quality_idx',
        'source_documents',
        ['quality_score']
    )

    op.create_index(
        'source_documents_topic_relevance_idx',
        'source_documents',
        ['topic_relevance_score']
    )


def downgrade() -> None:
    """Restore trust system, remove evaluation fields."""

    # =========================================================================
    # Remove evaluation indexes
    # =========================================================================
    op.drop_index('source_documents_topic_relevance_idx', table_name='source_documents')
    op.drop_index('source_documents_quality_idx', table_name='source_documents')
    op.drop_index('source_documents_reviewed_idx', table_name='source_documents')

    # =========================================================================
    # Remove evaluation columns
    # =========================================================================
    op.drop_column('source_documents', 'eval_timestamp')
    op.drop_column('source_documents', 'eval_model')
    op.drop_column('source_documents', 'topic_used')
    op.drop_column('source_documents', 'topic_relevance_summary')
    op.drop_column('source_documents', 'topic_relevance_score')
    op.drop_column('source_documents', 'quality_summary')
    op.drop_column('source_documents', 'quality_score')
    op.drop_column('source_documents', 'reviewed_by_human')

    # =========================================================================
    # Restore audit trust columns
    # =========================================================================
    op.add_column(
        'ingest_audit_log',
        sa.Column(
            'trust_assignment_reason',
            sa.Text(),
            nullable=False,
            server_default='Restored from downgrade'
        )
    )

    op.add_column(
        'ingest_audit_log',
        sa.Column(
            'trust_state_assigned',
            sa.String(length=20),
            nullable=False,
            server_default='needs_review'
        )
    )

    # Restore constraint
    op.execute("""
        ALTER TABLE ingest_audit_log
        ADD CONSTRAINT audit_trust_state_valid
        CHECK (trust_state_assigned IN ('trusted', 'needs_review'))
    """)

    # =========================================================================
    # Restore source_documents trust_state
    # =========================================================================
    op.add_column(
        'source_documents',
        sa.Column(
            'trust_state',
            sa.String(length=20),
            nullable=False,
            server_default='needs_review'
        )
    )

    op.execute("""
        ALTER TABLE source_documents
        ADD CONSTRAINT trust_state_valid
        CHECK (trust_state IN ('trusted', 'needs_review'))
    """)

    op.create_index(
        'source_documents_trust_state_idx',
        'source_documents',
        ['trust_state']
    )
