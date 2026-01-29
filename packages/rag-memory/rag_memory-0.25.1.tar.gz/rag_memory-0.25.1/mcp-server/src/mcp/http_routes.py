"""
HTTP REST API routes for RAG Memory MCP server.

This module provides HTTP endpoints for operations that don't fit the MCP protocol:
- Browser-based file uploads via multipart/form-data
- Admin dashboard endpoints for analytics and system metrics

These endpoints:
- Process files in-memory (no temp files)
- Use the same business logic as MCP tools (UnifiedIngestionMediator)
- Support standard browser file uploads
- Handle PDF files via pymupdf4llm text extraction
- Provide aggregate statistics for admin dashboard (human operators, not AI agents)

Usage:
    These routes are registered in server.py using @mcp.custom_route() decorator.
    They coexist with MCP tools - MCP for AI agents, HTTP for web frontends.
"""

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse

from src.core.database import Database
from src.ingestion.document_store import DocumentStore
from src.unified.graph_store import GraphStore
from src.unified.mediator import UnifiedIngestionMediator

# Audit logging
from src.mcp.audit import create_audit_entry

# Reuse validation helpers from MCP tools (SOURCE OF TRUTH for file validation)
from src.mcp.tools import (
    validate_mode,
    validate_collection_exists,
    ensure_databases_healthy,
    delete_document_for_reingest,
    # File validation (shared across all layers)
    validate_file_for_ingestion,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    BLOCKED_EXTENSIONS,
    PDF_EXTENSION,
    SUPPORTED_FILES_DESCRIPTION,
    # Content hash functions for duplicate detection
    compute_content_hash,
    check_duplicate_by_hash_global,
    update_document_metadata_only,
    # Manage collection link (link/unlink)
    manage_collection_link_impl,
)

# PDF extraction (lazy import to avoid load time if not used)
_pymupdf4llm = None

def _get_pdf_extractor():
    """Lazy import of pymupdf4llm for PDF text extraction."""
    global _pymupdf4llm
    if _pymupdf4llm is None:
        try:
            import pymupdf4llm
            _pymupdf4llm = pymupdf4llm
        except ImportError:
            raise ImportError(
                "PDF support requires pymupdf4llm. Install with: pip install pymupdf4llm"
            )
    return _pymupdf4llm

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from a PDF file using pymupdf4llm.

    Returns markdown-formatted text that preserves document structure,
    which works well with the existing hierarchical chunker.

    Args:
        file_bytes: Raw PDF file bytes
        filename: Original filename (for error messages)

    Returns:
        Extracted text as markdown string

    Raises:
        ValueError: If PDF extraction fails
    """
    pymupdf4llm = _get_pdf_extractor()

    try:
        # pymupdf4llm.to_markdown() expects a file path or PyMuPDF document
        # We need to use pymupdf (fitz) to open from bytes
        import pymupdf  # PyMuPDF

        # Open PDF from bytes
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")

        # Extract as markdown (preserves structure for better chunking)
        markdown_text = pymupdf4llm.to_markdown(doc)

        # Close the document
        doc.close()

        if not markdown_text or not markdown_text.strip():
            raise ValueError("PDF appears to be empty or contains no extractable text")

        logger.info(f"Extracted {len(markdown_text)} chars of text from PDF '{filename}'")
        return markdown_text

    except ImportError as e:
        raise ValueError(f"PDF extraction requires pymupdf4llm: {e}")
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF '{filename}': {e}")


async def upload_file_endpoint(
    request: Request,
    unified_mediator: UnifiedIngestionMediator,
    doc_store: DocumentStore,
    db: Database,
    graph_store: Optional[GraphStore],
) -> JSONResponse:
    """
    Handle multipart/form-data file upload (in-memory, no temp files).

    This endpoint:
    - Parses form data directly in memory
    - Validates file type and size
    - Checks for duplicates
    - Calls UnifiedIngestionMediator (same business logic as MCP tools)

    Args:
        request: Starlette request with multipart form data
        unified_mediator: For calling business logic
        doc_store: For collection validation
        db: For duplicate checking
        graph_store: For health checks and reingest deletion

    Returns:
        JSONResponse with ingestion result or error
    """
    try:
        # Health check: both PostgreSQL and Neo4j must be reachable
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return JSONResponse(
                {
                    "error": "database_unavailable",
                    "message": health_error.get("message", "Database health check failed"),
                    "details": health_error.get("details"),
                },
                status_code=503,
            )

        # Parse multipart form data (in-memory)
        form = await request.form()

        # Extract file
        if "file" not in form:
            return JSONResponse(
                {"error": "missing_file", "message": "No file provided in request"},
                status_code=400,
            )

        uploaded_file = form["file"]

        # Validate it's actually a file (not just a string field)
        if not hasattr(uploaded_file, "read"):
            return JSONResponse(
                {"error": "invalid_file", "message": "Expected file upload, got text field"},
                status_code=400,
            )

        # Extract parameters
        collection_name = form.get("collection_name")
        metadata_str = form.get("metadata")
        mode = form.get("mode", "ingest")

        # Evaluation parameters
        topic = form.get("topic")  # Optional topic for relevance scoring
        reviewed_by_human_str = form.get("reviewed_by_human", "false")
        reviewed_by_human = reviewed_by_human_str.lower() in ("true", "1", "yes")

        # Audit parameters (default to "api" for HTTP uploads)
        actor_type = form.get("actor_type", "api")

        # Validate required parameters
        if not collection_name:
            return JSONResponse(
                {"error": "missing_collection", "message": "collection_name is required"},
                status_code=400,
            )

        # Validate mode
        try:
            validate_mode(mode)
        except ValueError as e:
            return JSONResponse(
                {"error": "invalid_mode", "message": str(e)},
                status_code=400,
            )

        # Validate collection exists
        try:
            validate_collection_exists(doc_store, collection_name)
        except ValueError as e:
            return JSONResponse(
                {"error": "collection_not_found", "message": str(e)},
                status_code=400,
            )

        # Get filename
        filename = uploaded_file.filename
        if not filename:
            return JSONResponse(
                {"error": "missing_filename", "message": "File must have a filename"},
                status_code=400,
            )

        # Read file bytes (in-memory) - need size for validation
        file_bytes = await uploaded_file.read()
        file_ext = Path(filename).suffix.lower()

        # Validate file using shared validation (SOURCE OF TRUTH from MCP tools)
        validation = validate_file_for_ingestion(
            file_path=Path(filename),  # Just need the extension
            file_size=len(file_bytes),
            allow_pdf=True,
        )

        if not validation["valid"]:
            # Map category to appropriate HTTP error code
            status_code = 413 if validation["category"] == "too_large" else 400
            error_type = validation["category"] or "unsupported_file_type"

            return JSONResponse(
                {
                    "error": error_type,
                    "message": f"Cannot upload '{filename}': {validation['reason']}. {SUPPORTED_FILES_DESCRIPTION}",
                },
                status_code=status_code,
            )

        # Handle PDF files separately using pymupdf4llm
        is_pdf = file_ext == PDF_EXTENSION

        if is_pdf:
            # Extract text from PDF using pymupdf4llm
            try:
                content = extract_text_from_pdf(file_bytes, filename)
            except ValueError as e:
                return JSONResponse(
                    {"error": "pdf_extraction_failed", "message": str(e)},
                    status_code=400,
                )
        else:
            # Text file: decode bytes to string (UTF-8 with error ignoring)
            try:
                content = file_bytes.decode("utf-8", errors="ignore")
            except Exception as e:
                return JSONResponse(
                    {"error": "decode_failed", "message": f"Could not decode file as text: {e}"},
                    status_code=400,
                )

            # Check for binary file (content is mostly non-printable)
            # Skip this check for PDFs since they're already handled
            non_printable_ratio = sum(1 for c in content[:1000] if not c.isprintable() and c not in '\n\r\t') / max(len(content[:1000]), 1)
            if non_printable_ratio > 0.3:
                return JSONResponse(
                    {
                        "error": "binary_file",
                        "message": "File appears to be binary. Only text files are supported.",
                    },
                    status_code=400,
                )

        # Prepare file metadata
        file_type = file_ext.lstrip(".").lower() if file_ext else "text"
        file_metadata = {
            "file_type": file_type,
            "file_size": len(file_bytes),
            "upload_source": "http",  # Mark as HTTP upload
        }

        # Parse and merge user metadata if provided
        if metadata_str:
            try:
                user_metadata = json.loads(metadata_str)
                if isinstance(user_metadata, dict):
                    file_metadata.update(user_metadata)
            except json.JSONDecodeError:
                return JSONResponse(
                    {"error": "invalid_metadata", "message": "Metadata must be valid JSON"},
                    status_code=400,
                )

        # Compute content hash for duplicate detection
        content_hash = compute_content_hash(content)
        logger.info(f"Computed content hash: {content_hash[:16]}...")

        # Check for existing document with same content hash in ANY collection (global check)
        existing = check_duplicate_by_hash_global(db, content_hash)

        # Get collection description for evaluation (once, before any case)
        collection = doc_store.collection_mgr.get_collection(collection_name)
        collection_description = collection.get("description", "") if collection else ""

        # Import evaluation function
        from src.mcp.evaluation import evaluate_content

        # =================================================================
        # CASE 0: Content exists in DIFFERENT collection + mode=ingest = Error
        # (mode=reingest will delete and re-ingest in CASE 2 below)
        # =================================================================
        if mode == "ingest" and existing and collection_name not in existing.get("collections", []):
            existing_collection = existing["collections"][0] if existing["collections"] else "unknown"
            logger.warning(
                f"Content exists in different collection '{existing_collection}' "
                f"(doc_id={existing['doc_id']}), target was '{collection_name}'"
            )
            return JSONResponse({
                "error": "content_exists_in_other_collection",
                "status": "error",
                "message": (
                    f"This content already exists in collection '{existing_collection}' "
                    f"(document_id: {existing['doc_id']}, title: '{existing['filename']}'). "
                    f"Use manage_collection_link to add it to '{collection_name}', "
                    f"or mode='reingest' to move it."
                ),
                "existing_document_id": existing["doc_id"],
                "existing_collection": existing_collection,
                "existing_collections": existing["collections"],
                "target_collection": collection_name,
                "options": {
                    "link": f"manage_collection_link(document_id={existing['doc_id']}, collection_name='{collection_name}')",
                    "move": f"Use mode='reingest' to delete from '{existing_collection}' and ingest fresh to '{collection_name}'"
                }
            }, status_code=409)

        # =================================================================
        # CASE 1: mode=ingest + hash matches in SAME collection = Smart Update
        # =================================================================
        if existing and mode == "ingest" and collection_name in existing.get("collections", []):
            logger.info(f"Content hash matches existing doc ID={existing['doc_id']}")
            logger.info("Smart update: Updating metadata only (no re-embed, no re-graph)")

            # Determine if we need to re-run LLM evaluation
            needs_eval = (topic != existing.get("topic_provided"))

            eval_result = None
            if needs_eval:
                logger.info(f"Topic changed, re-running evaluation")
                eval_result = await evaluate_content(
                    content=content,
                    collection_name=collection_name,
                    collection_description=collection_description,
                    topic=topic,
                )

            # Smart update - update metadata, timestamps, and eval fields if needed
            # Note: filename intentionally NOT updated to preserve existing LLM-generated title
            # MERGE existing metadata with new file_metadata (new values take precedence)
            merged_metadata = {**(existing.get("metadata") or {}), **file_metadata}
            update_result = update_document_metadata_only(
                db=db,
                doc_id=existing["doc_id"],
                metadata=merged_metadata,  # MERGE with existing, not replace
                reviewed_by_human=reviewed_by_human if reviewed_by_human else None,
                # Eval fields - only update if we re-ran eval
                topic_provided=topic if needs_eval else None,
                quality_score=eval_result.quality_score if eval_result else None,
                quality_summary=eval_result.quality_summary if eval_result else None,
                topic_relevance_score=eval_result.topic_relevance_score if eval_result else None,
                topic_relevance_summary=eval_result.topic_relevance_summary if eval_result else None,
                eval_model=eval_result.model if eval_result else None,
                eval_timestamp=eval_result.timestamp if eval_result else None,
            )

            # Build evaluation for response
            evaluation = {
                "quality_score": eval_result.quality_score if eval_result else existing.get("quality_score"),
                "quality_summary": eval_result.quality_summary if eval_result else existing.get("quality_summary"),
            }
            if topic:
                evaluation["topic_relevance_score"] = eval_result.topic_relevance_score if eval_result else existing.get("topic_relevance_score")
                evaluation["topic_relevance_summary"] = eval_result.topic_relevance_summary if eval_result else existing.get("topic_relevance_summary")
                evaluation["topic_provided"] = topic

            return JSONResponse({
                "status": "updated",
                "source_document_id": existing["doc_id"],
                "content_changed": False,
                "updated_fields": update_result["updated_fields"],
                "filename": filename,
                "file_type": file_type,
                "file_size": len(file_bytes),
                "collection_name": collection_name,
                "evaluation": evaluation,
                "message": "Content unchanged. Metadata and timestamps updated.",
            })

        # =================================================================
        # CASE 2: mode=reingest + hash matches = Full Delete + Fresh Ingest
        # =================================================================
        if existing and mode == "reingest":
            logger.info(f"Reingest mode: Full delete + fresh ingest for doc ID={existing['doc_id']}")

            await delete_document_for_reingest(
                doc_id=existing["doc_id"],
                doc_store=doc_store,
                graph_store=graph_store,
                filename=existing["filename"],
            )
            # Continue to full ingest below...

        # =================================================================
        # CASE 3: New content (or mode=reingest) = Full Ingest
        # =================================================================
        logger.info(f"Running content evaluation (topic={'provided' if topic else 'none'})")
        eval_result = await evaluate_content(
            content=content,
            collection_name=collection_name,
            collection_description=collection_description,
            topic=topic,
        )

        # Call unified mediator (CORE BUSINESS LOGIC)
        logger.info(f"HTTP upload: Ingesting file '{filename}' into collection '{collection_name}'")
        result = await unified_mediator.ingest_text(
            content=content,
            collection_name=collection_name,
            document_title=filename,
            metadata=file_metadata,
            # Pass evaluation fields
            reviewed_by_human=reviewed_by_human,
            quality_score=eval_result.quality_score,
            quality_summary=eval_result.quality_summary,
            topic_relevance_score=eval_result.topic_relevance_score,
            topic_relevance_summary=eval_result.topic_relevance_summary,
            topic_provided=eval_result.topic_provided,
            eval_model=eval_result.model,
            eval_timestamp=eval_result.timestamp,
            # Pass content hash for storage
            content_hash=content_hash,
        )

        # Build evaluation response
        evaluation = {
            "quality_score": eval_result.quality_score,
            "quality_summary": eval_result.quality_summary,
        }
        if topic:
            evaluation["topic_relevance_score"] = eval_result.topic_relevance_score
            evaluation["topic_relevance_summary"] = eval_result.topic_relevance_summary
            evaluation["topic_provided"] = eval_result.topic_provided

        # Audit logging
        create_audit_entry(
            db=db,
            source_document_id=result["source_document_id"],
            actor_type=actor_type,
            ingest_method="file",
            collection_name=collection_name,
            metadata={
                "filename": filename,
                "file_type": file_type,
                "file_size": len(file_bytes),
                "upload_source": "http",
                "evaluation": evaluation,
            },
        )

        # Format response
        return JSONResponse({
            "status": "reingested" if (existing and mode == "reingest") else "ingested",
            "source_document_id": result["source_document_id"],
            "num_chunks": result["num_chunks"],
            "entities_extracted": result.get("entities_extracted", 0),
            "filename": filename,
            "file_type": file_type,
            "file_size": len(file_bytes),
            "collection_name": collection_name,
            "evaluation": evaluation,
        })

    except Exception as e:
        logger.error(f"HTTP file upload failed: {e}", exc_info=True)
        return JSONResponse(
            {"error": "ingestion_failed", "message": str(e)},
            status_code=500,
        )


async def update_document_review_endpoint(
    request: Request,
    doc_store: DocumentStore,
    db: Database,
    graph_store: Optional[GraphStore],
) -> JSONResponse:
    """
    Update a document's reviewed_by_human status.

    This endpoint allows the frontend to toggle the human review status
    without requiring full document update (no re-chunking, no re-embedding).

    Args:
        request: Starlette request with JSON body containing document_id and reviewed_by_human
        doc_store: Document store for update
        db: Database connection
        graph_store: For health checks

    Returns:
        JSONResponse with update result or error
    """
    try:
        # Health check
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return JSONResponse(
                {
                    "error": "database_unavailable",
                    "message": health_error.get("message", "Database health check failed"),
                },
                status_code=503,
            )

        # Parse JSON body
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse(
                {"error": "invalid_json", "message": f"Invalid JSON body: {e}"},
                status_code=400,
            )

        document_id = body.get("document_id")
        reviewed_by_human = body.get("reviewed_by_human")

        if document_id is None:
            return JSONResponse(
                {"error": "missing_document_id", "message": "document_id is required"},
                status_code=400,
            )

        if reviewed_by_human is None:
            return JSONResponse(
                {"error": "missing_reviewed_by_human", "message": "reviewed_by_human is required"},
                status_code=400,
            )

        if not isinstance(reviewed_by_human, bool):
            return JSONResponse(
                {"error": "invalid_reviewed_by_human", "message": "reviewed_by_human must be a boolean"},
                status_code=400,
            )

        # Update the document
        logger.info(f"HTTP: Updating document {document_id} reviewed_by_human={reviewed_by_human}")
        result = await doc_store.update_document(
            document_id=document_id,
            reviewed_by_human=reviewed_by_human,
        )

        return JSONResponse({
            "document_id": result["document_id"],
            "updated_fields": result["updated_fields"],
            "reviewed_by_human": reviewed_by_human,
        })

    except ValueError as e:
        # Document not found or validation error
        return JSONResponse(
            {"error": "not_found", "message": str(e)},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"HTTP update document review failed: {e}", exc_info=True)
        return JSONResponse(
            {"error": "update_failed", "message": str(e)},
            status_code=500,
        )


async def manage_collection_link_endpoint(
    request: Request,
    doc_store: DocumentStore,
    db: Database,
    graph_store: Optional[GraphStore],
) -> JSONResponse:
    """
    Link or unlink a document to/from a collection.

    This endpoint manages document-collection relationships without
    re-embedding or re-graphing. It's an instant metadata operation.

    Args:
        request: Starlette request with form data containing:
            - document_id (required): Document ID
            - collection_name (required): Target collection
            - unlink (optional): "true" to unlink, defaults to link
        doc_store: Document store for operation
        db: Database connection
        graph_store: For health checks

    Returns:
        JSONResponse with link/unlink result or error
    """
    try:
        # Health check
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return JSONResponse(
                {
                    "error": "database_unavailable",
                    "message": health_error.get("message", "Database health check failed"),
                },
                status_code=503,
            )

        # Parse form data
        form = await request.form()

        document_id_str = form.get("document_id")
        collection_name = form.get("collection_name")
        unlink_str = form.get("unlink", "false")

        if not document_id_str:
            return JSONResponse(
                {"error": "missing_document_id", "message": "document_id is required"},
                status_code=400,
            )

        if not collection_name:
            return JSONResponse(
                {"error": "missing_collection_name", "message": "collection_name is required"},
                status_code=400,
            )

        try:
            document_id = int(document_id_str)
        except ValueError:
            return JSONResponse(
                {"error": "invalid_document_id", "message": "document_id must be an integer"},
                status_code=400,
            )

        # Parse unlink flag (form data comes as string)
        unlink = unlink_str.lower() in ("true", "1", "yes")

        # Call the implementation
        action = "Unlinking" if unlink else "Linking"
        logger.info(f"HTTP: {action} document {document_id} {'from' if unlink else 'to'} collection '{collection_name}'")
        result = manage_collection_link_impl(db, doc_store, document_id, collection_name, unlink)

        return JSONResponse(result)

    except ValueError as e:
        # Document not found, collection not found, already linked, not linked, or orphan protection
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return JSONResponse(
                {"error": "not_found", "message": error_msg},
                status_code=404,
            )
        elif "already" in error_msg.lower():
            return JSONResponse(
                {"error": "already_linked", "message": error_msg},
                status_code=409,
            )
        elif "is not in collection" in error_msg.lower():
            return JSONResponse(
                {"error": "not_linked", "message": error_msg},
                status_code=404,
            )
        elif "only collection" in error_msg.lower():
            return JSONResponse(
                {"error": "orphan_protection", "message": error_msg},
                status_code=400,
            )
        else:
            return JSONResponse(
                {"error": "validation_error", "message": error_msg},
                status_code=400,
            )
    except Exception as e:
        logger.error(f"HTTP manage collection link failed: {e}", exc_info=True)
        return JSONResponse(
            {"error": "operation_failed", "message": str(e)},
            status_code=500,
        )


# =============================================================================
# ADMIN DASHBOARD ENDPOINTS
# =============================================================================


async def get_admin_stats_endpoint(
    request: Request,
    db: Database,
) -> JSONResponse:
    """
    Get aggregate system statistics for the admin dashboard.

    Returns counts and distributions across all collections, documents, and chunks.
    This is a READ-ONLY endpoint for human administrators, not AI agents.

    Query params:
        collection: Optional collection name to filter by

    Args:
        request: Starlette request
        db: Database connection

    Returns:
        JSONResponse with system statistics
    """
    try:
        conn = db.connect()
        collection_name = request.query_params.get("collection")

        stats = {}

        # Total collections (always show all collections count)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM collections")
            stats["collections"] = {"total": cur.fetchone()[0]}

        # Build collection filter for document queries
        # Documents are linked to collections via: document_chunks -> chunk_collections -> collections
        if collection_name:
            doc_filter = """
                WHERE sd.id IN (
                    SELECT DISTINCT dch.source_document_id
                    FROM document_chunks dch
                    JOIN chunk_collections cc ON cc.chunk_id = dch.id
                    JOIN collections c ON c.id = cc.collection_id
                    WHERE c.name = %s
                )
            """
            doc_filter_params = (collection_name,)
            chunk_filter = """
                WHERE ch.id IN (
                    SELECT cc.chunk_id
                    FROM chunk_collections cc
                    JOIN collections c ON c.id = cc.collection_id
                    WHERE c.name = %s
                )
            """
            chunk_filter_params = (collection_name,)
        else:
            doc_filter = ""
            doc_filter_params = ()
            chunk_filter = ""
            chunk_filter_params = ()

        # Total documents with review status breakdown
        with conn.cursor() as cur:
            query = f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE sd.reviewed_by_human = true) as reviewed,
                    COUNT(*) FILTER (WHERE sd.reviewed_by_human = false OR sd.reviewed_by_human IS NULL) as unreviewed
                FROM source_documents sd
                {doc_filter}
            """
            cur.execute(query, doc_filter_params)
            row = cur.fetchone()
            stats["documents"] = {
                "total": row[0],
                "reviewed": row[1],
                "unreviewed": row[2],
            }

        # Total chunks
        with conn.cursor() as cur:
            query = f"""
                SELECT COUNT(*)
                FROM document_chunks ch
                {chunk_filter}
            """
            cur.execute(query, chunk_filter_params)
            stats["chunks"] = {"total": cur.fetchone()[0]}

        # Quality score statistics
        with conn.cursor() as cur:
            query = f"""
                SELECT
                    AVG(sd.quality_score) as avg,
                    MIN(sd.quality_score) as min,
                    MAX(sd.quality_score) as max,
                    COUNT(*) FILTER (WHERE sd.quality_score >= 0.7) as high,
                    COUNT(*) FILTER (WHERE sd.quality_score >= 0.4 AND sd.quality_score < 0.7) as medium,
                    COUNT(*) FILTER (WHERE sd.quality_score < 0.4) as low,
                    COUNT(*) FILTER (WHERE sd.quality_score IS NULL) as unscored
                FROM source_documents sd
                {doc_filter}
            """
            cur.execute(query, doc_filter_params)
            row = cur.fetchone()
            stats["quality"] = {
                "avg": round(float(row[0]), 3) if row[0] else None,
                "min": round(float(row[1]), 3) if row[1] else None,
                "max": round(float(row[2]), 3) if row[2] else None,
                "distribution": {
                    "high": row[3],
                    "medium": row[4],
                    "low": row[5],
                    "unscored": row[6],
                },
            }

        # Topic relevance breakdown
        with conn.cursor() as cur:
            query = f"""
                SELECT
                    COUNT(*) FILTER (WHERE sd.topic_provided IS NOT NULL) as with_topic,
                    COUNT(*) FILTER (WHERE sd.topic_provided IS NULL) as without_topic,
                    AVG(sd.topic_relevance_score) FILTER (WHERE sd.topic_relevance_score IS NOT NULL) as avg_relevance
                FROM source_documents sd
                {doc_filter}
            """
            cur.execute(query, doc_filter_params)
            row = cur.fetchone()
            stats["topic_relevance"] = {
                "with_topic": row[0],
                "without_topic": row[1],
                "avg_relevance": round(float(row[2]), 3) if row[2] else None,
            }

        # Add filter info if filtered
        if collection_name:
            stats["filtered_by"] = collection_name

        logger.info(f"Admin stats retrieved: {stats['documents']['total']} docs, {stats['chunks']['total']} chunks (collection={collection_name or 'all'})")
        return JSONResponse(stats)

    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}", exc_info=True)
        return JSONResponse(
            {"error": "stats_failed", "message": str(e)},
            status_code=500,
        )


async def get_quality_analytics_endpoint(
    request: Request,
    db: Database,
) -> JSONResponse:
    """
    Get detailed quality analytics for charts and visualizations.

    Returns histogram data suitable for Recharts bar charts and comparison data
    across collections. Optionally filtered by collection.

    Args:
        request: Starlette request with optional collection_name query param
        db: Database connection

    Returns:
        JSONResponse with quality distribution data for charts
    """
    try:
        conn = db.connect()
        collection_name = request.query_params.get("collection_name")

        analytics = {}

        # Build WHERE clause for collection filter
        if collection_name:
            # Filter by collection using the junction tables
            collection_filter = """
                WHERE sd.id IN (
                    SELECT DISTINCT dc.source_document_id
                    FROM document_chunks dc
                    JOIN chunk_collections cc ON cc.chunk_id = dc.id
                    JOIN collections c ON c.id = cc.collection_id
                    WHERE c.name = %s
                )
            """
            filter_params = [collection_name]
        else:
            collection_filter = ""
            filter_params = []

        # Quality score histogram (5 bins: 0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
        with conn.cursor() as cur:
            query = f"""
                SELECT
                    COUNT(*) FILTER (WHERE quality_score >= 0 AND quality_score < 0.2) as bin_0_20,
                    COUNT(*) FILTER (WHERE quality_score >= 0.2 AND quality_score < 0.4) as bin_20_40,
                    COUNT(*) FILTER (WHERE quality_score >= 0.4 AND quality_score < 0.6) as bin_40_60,
                    COUNT(*) FILTER (WHERE quality_score >= 0.6 AND quality_score < 0.8) as bin_60_80,
                    COUNT(*) FILTER (WHERE quality_score >= 0.8 AND quality_score <= 1.0) as bin_80_100
                FROM source_documents sd
                {collection_filter}
            """
            cur.execute(query, filter_params)
            row = cur.fetchone()
            analytics["quality_histogram"] = [
                {"range": "0-20%", "count": row[0]},
                {"range": "20-40%", "count": row[1]},
                {"range": "40-60%", "count": row[2]},
                {"range": "60-80%", "count": row[3]},
                {"range": "80-100%", "count": row[4]},
            ]

        # Topic relevance histogram (same bins)
        with conn.cursor() as cur:
            query = f"""
                SELECT
                    COUNT(*) FILTER (WHERE topic_relevance_score >= 0 AND topic_relevance_score < 0.2) as bin_0_20,
                    COUNT(*) FILTER (WHERE topic_relevance_score >= 0.2 AND topic_relevance_score < 0.4) as bin_20_40,
                    COUNT(*) FILTER (WHERE topic_relevance_score >= 0.4 AND topic_relevance_score < 0.6) as bin_40_60,
                    COUNT(*) FILTER (WHERE topic_relevance_score >= 0.6 AND topic_relevance_score < 0.8) as bin_60_80,
                    COUNT(*) FILTER (WHERE topic_relevance_score >= 0.8 AND topic_relevance_score <= 1.0) as bin_80_100
                FROM source_documents sd
                {collection_filter}
            """
            cur.execute(query, filter_params)
            row = cur.fetchone()
            analytics["topic_histogram"] = [
                {"range": "0-20%", "count": row[0]},
                {"range": "20-40%", "count": row[1]},
                {"range": "40-60%", "count": row[2]},
                {"range": "60-80%", "count": row[3]},
                {"range": "80-100%", "count": row[4]},
            ]

        # Review status breakdown
        with conn.cursor() as cur:
            query = f"""
                SELECT
                    COUNT(*) FILTER (WHERE reviewed_by_human = true) as reviewed,
                    COUNT(*) FILTER (WHERE reviewed_by_human = false OR reviewed_by_human IS NULL) as unreviewed
                FROM source_documents sd
                {collection_filter}
            """
            cur.execute(query, filter_params)
            row = cur.fetchone()
            analytics["review_breakdown"] = {
                "reviewed": row[0],
                "unreviewed": row[1],
            }

        # Quality by collection (only if not already filtered to a single collection)
        if not collection_name:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        c.name as collection,
                        AVG(sd.quality_score) as avg,
                        MIN(sd.quality_score) as min,
                        MAX(sd.quality_score) as max,
                        COUNT(DISTINCT sd.id) as doc_count
                    FROM collections c
                    JOIN chunk_collections cc ON cc.collection_id = c.id
                    JOIN document_chunks dc ON dc.id = cc.chunk_id
                    JOIN source_documents sd ON sd.id = dc.source_document_id
                    WHERE sd.quality_score IS NOT NULL
                    GROUP BY c.name
                    ORDER BY AVG(sd.quality_score) DESC
                """)
                rows = cur.fetchall()
                analytics["quality_by_collection"] = [
                    {
                        "collection": row[0],
                        "avg": round(float(row[1]), 3) if row[1] else None,
                        "min": round(float(row[2]), 3) if row[2] else None,
                        "max": round(float(row[3]), 3) if row[3] else None,
                        "doc_count": row[4],
                    }
                    for row in rows
                ]
        else:
            analytics["quality_by_collection"] = []
            analytics["filtered_by"] = collection_name

        logger.info(f"Quality analytics retrieved (collection={collection_name or 'all'})")
        return JSONResponse(analytics)

    except Exception as e:
        logger.error(f"Failed to get quality analytics: {e}", exc_info=True)
        return JSONResponse(
            {"error": "analytics_failed", "message": str(e)},
            status_code=500,
        )


def _format_bytes(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    if size_bytes is None:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


async def get_content_analytics_endpoint(
    request: Request,
    db: Database,
) -> JSONResponse:
    """
    Get content composition and ingestion pattern metrics.

    Query params:
        collection: Optional collection name to filter by

    Returns metrics about:
    - File type distribution (what kinds of content)
    - Ingest method breakdown (how content enters)
    - Actor type breakdown (who ingests)
    - Ingestion timeline (activity over time)
    - Crawl statistics (web crawl details)
    - Storage metrics (total size, avg per doc)
    - Chunk statistics (total, avg per doc)

    Args:
        request: Starlette request
        db: Database connection

    Returns:
        JSONResponse with content analytics data
    """
    try:
        # Get optional collection filter
        collection_name = request.query_params.get("collection")

        conn = db.connect()
        analytics = {}

        # Build collection filter clause for source_documents queries
        # Requires joining through document_chunks -> chunk_collections -> collections
        if collection_name:
            doc_filter = """
                INNER JOIN document_chunks dch ON dch.source_document_id = sd.id
                INNER JOIN chunk_collections cc ON cc.chunk_id = dch.id
                INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
            """
            doc_filter_params = (collection_name,)
        else:
            doc_filter = ""
            doc_filter_params = ()

        # =================================================================
        # FILE TYPE DISTRIBUTION
        # =================================================================
        with conn.cursor() as cur:
            # Prefer metadata->>'file_type' (correctly set) over file_type column (often hardcoded to 'text')
            if collection_name:
                cur.execute("""
                    SELECT
                        COALESCE(sd.metadata->>'file_type', sd.file_type, 'unknown') as type,
                        COUNT(DISTINCT sd.id) as count,
                        COALESCE(SUM(DISTINCT sd.file_size), 0) as size_bytes
                    FROM source_documents sd
                    INNER JOIN document_chunks dch ON dch.source_document_id = sd.id
                    INNER JOIN chunk_collections cc ON cc.chunk_id = dch.id
                    INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
                    GROUP BY COALESCE(sd.metadata->>'file_type', sd.file_type, 'unknown')
                    ORDER BY count DESC
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        COALESCE(metadata->>'file_type', file_type, 'unknown') as type,
                        COUNT(*) as count,
                        COALESCE(SUM(file_size), 0) as size_bytes
                    FROM source_documents
                    GROUP BY COALESCE(metadata->>'file_type', file_type, 'unknown')
                    ORDER BY count DESC
                """)
            rows = cur.fetchall()
            total_docs = sum(row[1] for row in rows)
            analytics["file_type_distribution"] = [
                {
                    "type": row[0] or "unknown",
                    "count": row[1],
                    "size_bytes": row[2] or 0,
                    "pct": round((row[1] / total_docs * 100), 1) if total_docs > 0 else 0,
                }
                for row in rows
            ]

        # =================================================================
        # INGEST METHOD BREAKDOWN (from audit log)
        # =================================================================
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT
                        ingest_method,
                        COUNT(*) as count
                    FROM ingest_audit_log
                    WHERE collection_name = %s
                    GROUP BY ingest_method
                    ORDER BY count DESC
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        ingest_method,
                        COUNT(*) as count
                    FROM ingest_audit_log
                    GROUP BY ingest_method
                    ORDER BY count DESC
                """)
            rows = cur.fetchall()
            total_ingests = sum(row[1] for row in rows)
            analytics["ingest_method_breakdown"] = [
                {
                    "method": row[0],
                    "count": row[1],
                    "pct": round((row[1] / total_ingests * 100), 1) if total_ingests > 0 else 0,
                }
                for row in rows
            ]

        # =================================================================
        # ACTOR TYPE BREAKDOWN (from audit log)
        # =================================================================
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT
                        actor_type,
                        COUNT(*) as count
                    FROM ingest_audit_log
                    WHERE collection_name = %s
                    GROUP BY actor_type
                    ORDER BY count DESC
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        actor_type,
                        COUNT(*) as count
                    FROM ingest_audit_log
                    GROUP BY actor_type
                    ORDER BY count DESC
                """)
            rows = cur.fetchall()
            total_actors = sum(row[1] for row in rows)
            analytics["actor_type_breakdown"] = [
                {
                    "actor": row[0],
                    "count": row[1],
                    "pct": round((row[1] / total_actors * 100), 1) if total_actors > 0 else 0,
                }
                for row in rows
            ]

        # =================================================================
        # INGESTION TIMELINE (last 30 days)
        # =================================================================
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE ingest_method = 'url') as url,
                        COUNT(*) FILTER (WHERE ingest_method = 'file') as file,
                        COUNT(*) FILTER (WHERE ingest_method = 'text') as text,
                        COUNT(*) FILTER (WHERE ingest_method = 'directory') as directory
                    FROM ingest_audit_log
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                      AND collection_name = %s
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE ingest_method = 'url') as url,
                        COUNT(*) FILTER (WHERE ingest_method = 'file') as file,
                        COUNT(*) FILTER (WHERE ingest_method = 'text') as text,
                        COUNT(*) FILTER (WHERE ingest_method = 'directory') as directory
                    FROM ingest_audit_log
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
            rows = cur.fetchall()
            analytics["ingestion_timeline"] = [
                {
                    "date": row[0].isoformat() if row[0] else None,
                    "total": row[1],
                    "url": row[2],
                    "file": row[3],
                    "text": row[4],
                    "directory": row[5],
                }
                for row in rows
            ]

        # =================================================================
        # CRAWL STATISTICS
        # =================================================================
        # Domains from crawled content
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT
                        sd.metadata->>'domain' as domain,
                        COUNT(*) as page_count,
                        AVG(sd.quality_score) as avg_quality
                    FROM source_documents sd
                    INNER JOIN document_chunks dch ON dch.source_document_id = sd.id
                    INNER JOIN chunk_collections cc ON cc.chunk_id = dch.id
                    INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
                    WHERE sd.metadata->>'crawl_root_url' IS NOT NULL
                      AND sd.metadata->>'domain' IS NOT NULL
                    GROUP BY sd.metadata->>'domain'
                    ORDER BY page_count DESC
                    LIMIT 10
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        metadata->>'domain' as domain,
                        COUNT(*) as page_count,
                        AVG(quality_score) as avg_quality
                    FROM source_documents
                    WHERE metadata->>'crawl_root_url' IS NOT NULL
                      AND metadata->>'domain' IS NOT NULL
                    GROUP BY metadata->>'domain'
                    ORDER BY page_count DESC
                    LIMIT 10
                """)
            rows = cur.fetchall()
            domains = [
                {
                    "domain": row[0],
                    "page_count": row[1],
                    "avg_quality": round(float(row[2]), 3) if row[2] else None,
                }
                for row in rows
            ]

        # Depth distribution
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT
                        COALESCE((sd.metadata->>'crawl_depth')::int, 0) as depth,
                        COUNT(*) as count
                    FROM source_documents sd
                    INNER JOIN document_chunks dch ON dch.source_document_id = sd.id
                    INNER JOIN chunk_collections cc ON cc.chunk_id = dch.id
                    INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
                    WHERE sd.metadata->>'crawl_root_url' IS NOT NULL
                    GROUP BY COALESCE((sd.metadata->>'crawl_depth')::int, 0)
                    ORDER BY depth
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        COALESCE((metadata->>'crawl_depth')::int, 0) as depth,
                        COUNT(*) as count
                    FROM source_documents
                    WHERE metadata->>'crawl_root_url' IS NOT NULL
                    GROUP BY COALESCE((metadata->>'crawl_depth')::int, 0)
                    ORDER BY depth
                """)
            rows = cur.fetchall()
            depth_labels = {0: "Root pages", 1: "1 hop", 2: "2+ hops"}
            depth_distribution = [
                {
                    "depth": row[0],
                    "count": row[1],
                    "label": depth_labels.get(row[0], f"{row[0]} hops"),
                }
                for row in rows
            ]

        # Total crawl sessions
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT COUNT(DISTINCT sd.metadata->>'crawl_session_id')
                    FROM source_documents sd
                    INNER JOIN document_chunks dch ON dch.source_document_id = sd.id
                    INNER JOIN chunk_collections cc ON cc.chunk_id = dch.id
                    INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
                    WHERE sd.metadata->>'crawl_session_id' IS NOT NULL
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT COUNT(DISTINCT metadata->>'crawl_session_id')
                    FROM source_documents
                    WHERE metadata->>'crawl_session_id' IS NOT NULL
                """)
            total_sessions = cur.fetchone()[0] or 0

        analytics["crawl_stats"] = {
            "domains": domains,
            "depth_distribution": depth_distribution,
            "total_crawl_sessions": total_sessions,
        }

        # =================================================================
        # STORAGE METRICS
        # =================================================================
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT
                        COALESCE(SUM(sd.file_size), 0) as total_bytes,
                        COUNT(*) as doc_count
                    FROM source_documents sd
                    INNER JOIN document_chunks dch ON dch.source_document_id = sd.id
                    INNER JOIN chunk_collections cc ON cc.chunk_id = dch.id
                    INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        COALESCE(SUM(file_size), 0) as total_bytes,
                        COUNT(*) as doc_count
                    FROM source_documents
                """)
            row = cur.fetchone()
            total_bytes = row[0] or 0
            doc_count = row[1] or 1  # Avoid division by zero
            avg_per_doc = total_bytes / doc_count if doc_count > 0 else 0

            analytics["storage"] = {
                "total_bytes": total_bytes,
                "total_human": _format_bytes(total_bytes),
                "avg_per_doc": round(avg_per_doc),
                "avg_human": _format_bytes(round(avg_per_doc)),
            }

        # =================================================================
        # CHUNK STATISTICS
        # =================================================================
        with conn.cursor() as cur:
            if collection_name:
                cur.execute("""
                    SELECT
                        COUNT(*) as total_chunks,
                        COUNT(DISTINCT ch.source_document_id) as doc_count
                    FROM document_chunks ch
                    INNER JOIN chunk_collections cc ON cc.chunk_id = ch.id
                    INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        COUNT(*) as total_chunks,
                        COUNT(DISTINCT source_document_id) as doc_count
                    FROM document_chunks
                """)
            row = cur.fetchone()
            total_chunks = row[0] or 0
            chunk_doc_count = row[1] or 1

            # Get min/max chunks per document
            if collection_name:
                cur.execute("""
                    SELECT
                        MIN(chunk_count) as min_chunks,
                        MAX(chunk_count) as max_chunks
                    FROM (
                        SELECT ch.source_document_id, COUNT(*) as chunk_count
                        FROM document_chunks ch
                        INNER JOIN chunk_collections cc ON cc.chunk_id = ch.id
                        INNER JOIN collections c ON c.id = cc.collection_id AND c.name = %s
                        GROUP BY ch.source_document_id
                    ) subq
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT
                        MIN(chunk_count) as min_chunks,
                        MAX(chunk_count) as max_chunks
                    FROM (
                        SELECT source_document_id, COUNT(*) as chunk_count
                        FROM document_chunks
                        GROUP BY source_document_id
                    ) subq
                """)
            minmax = cur.fetchone()

            analytics["chunks"] = {
                "total": total_chunks,
                "avg_per_doc": round(total_chunks / chunk_doc_count, 1) if chunk_doc_count > 0 else 0,
                "min_per_doc": minmax[0] if minmax and minmax[0] else 0,
                "max_per_doc": minmax[1] if minmax and minmax[1] else 0,
            }

        logger.info(f"Content analytics retrieved: {len(analytics['file_type_distribution'])} file types, {len(analytics['ingestion_timeline'])} days")
        return JSONResponse(analytics)

    except Exception as e:
        logger.error(f"Failed to get content analytics: {e}", exc_info=True)
        return JSONResponse(
            {"error": "analytics_failed", "message": str(e)},
            status_code=500,
        )
