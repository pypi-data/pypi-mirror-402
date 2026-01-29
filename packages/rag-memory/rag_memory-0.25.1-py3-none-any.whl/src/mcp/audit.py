"""
Audit logging for ingestion operations.

Writes to ingest_audit_log table to track all ingestion activity with provenance.
"""

import logging
from datetime import datetime
from typing import Any

from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)


def _get_mcp_server_version() -> str:
    """Get MCP server version from package metadata."""
    try:
        from importlib.metadata import version
        return version("rag-memory")
    except Exception:
        return "unknown"


def create_audit_entry(
    db,
    source_document_id: int,
    actor_type: str,  # 'user', 'agent', 'api'
    ingest_method: str,  # 'text', 'file', 'directory', 'url'
    collection_name: str,
    actor_id: str = None,
    dry_run_performed: bool = False,
    dry_run_recommendation: str = None,  # 'ingest', 'review', 'skip'
    dry_run_score: float = None,
    dry_run_summary: str = None,
    user_override: bool = False,
    source_url: str = None,
    source_file_path: str = None,
    metadata: dict = None,
) -> int:
    """
    Create an audit log entry for an ingestion operation.

    Args:
        db: Database instance
        source_document_id: ID of the ingested document
        actor_type: Who initiated ('user', 'agent', 'api')
        ingest_method: How content was ingested ('text', 'file', 'directory', 'url')
        collection_name: Target collection
        actor_id: Optional identifier (e.g., 'claude-desktop', 'cursor')
        dry_run_performed: Whether dry run was done before ingesting
        dry_run_recommendation: Dry run result ('ingest', 'review', 'skip')
        dry_run_score: Relevance score from dry run (0.0-1.0)
        dry_run_summary: Summary from dry run
        user_override: True if user overrode a 'skip' or 'review' recommendation
        source_url: Original URL for URL ingests
        source_file_path: Original file path for file ingests
        metadata: Additional metadata (stored as JSONB)

    Returns:
        Audit log entry ID
    """
    conn = db.connect()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingest_audit_log (
                    source_document_id,
                    actor_type,
                    actor_id,
                    ingest_method,
                    collection_name,
                    dry_run_performed,
                    dry_run_recommendation,
                    dry_run_score,
                    dry_run_summary,
                    user_override,
                    mcp_server_version,
                    source_url,
                    source_file_path,
                    metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    source_document_id,
                    actor_type,
                    actor_id,
                    ingest_method,
                    collection_name,
                    dry_run_performed,
                    dry_run_recommendation,
                    dry_run_score,
                    dry_run_summary,
                    user_override,
                    _get_mcp_server_version(),
                    source_url,
                    source_file_path,
                    Jsonb(metadata) if metadata else None,
                )
            )
            audit_id = cur.fetchone()[0]
            conn.commit()

            logger.info(
                f"Audit log entry created: id={audit_id}, doc={source_document_id}, "
                f"method={ingest_method}, collection={collection_name}"
            )
            return audit_id

    except Exception as e:
        conn.rollback()
        # Audit logging should never break ingestion - log and continue
        logger.error(f"Failed to create audit log entry: {e}")
        return None


def get_audit_history(
    db,
    source_document_id: int = None,
    collection_name: str = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Retrieve audit log entries with optional filtering.

    Args:
        db: Database instance
        source_document_id: Filter by document ID
        collection_name: Filter by collection
        limit: Max entries to return
        offset: Pagination offset

    Returns:
        List of audit log entries
    """
    conn = db.connect()

    conditions = []
    params = []

    if source_document_id is not None:
        conditions.append("source_document_id = %s")
        params.append(source_document_id)

    if collection_name is not None:
        conditions.append("collection_name = %s")
        params.append(collection_name)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    params.extend([limit, offset])

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                id,
                source_document_id,
                created_at,
                actor_type,
                actor_id,
                ingest_method,
                collection_name,
                dry_run_performed,
                dry_run_recommendation,
                dry_run_score,
                dry_run_summary,
                user_override,
                mcp_server_version,
                source_url,
                source_file_path,
                metadata
            FROM ingest_audit_log
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            tuple(params)
        )
        rows = cur.fetchall()

    entries = []
    for row in rows:
        entries.append({
            "id": row[0],
            "source_document_id": row[1],
            "created_at": row[2].isoformat() if row[2] else None,
            "actor_type": row[3],
            "actor_id": row[4],
            "ingest_method": row[5],
            "collection_name": row[6],
            "dry_run_performed": row[7],
            "dry_run_recommendation": row[8],
            "dry_run_score": float(row[9]) if row[9] is not None else None,
            "dry_run_summary": row[10],
            "user_override": row[11],
            "mcp_server_version": row[12],
            "source_url": row[13],
            "source_file_path": row[14],
            "metadata": row[15],
        })

    return entries
