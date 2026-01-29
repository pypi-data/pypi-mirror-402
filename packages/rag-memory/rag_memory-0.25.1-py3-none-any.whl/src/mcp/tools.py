"""
Tool implementation functions for MCP server.

These are wrappers around existing RAG functionality, converting to/from
MCP-compatible formats (JSON-serializable dicts).
"""

import asyncio
import functools
import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from openai import OpenAI
from psycopg import OperationalError, DatabaseError

from src.core.database import Database
from src.core.collections import CollectionManager
from src.core.config_loader import get_instance_config
from src.retrieval.search import SimilaritySearch
from src.ingestion.document_store import DocumentStore
from src.ingestion.web_crawler import WebCrawler, crawl_single_page
from src.ingestion.website_analyzer import analyze_website_async
from src.unified.graph_store import GraphStore
from src.mcp.deduplication import deduplicate_request
from src.mcp.audit import create_audit_entry

# Import EntityNode for fetching missing entity names from knowledge graph
from graphiti_core.nodes import EntityNode

# Type variable for generic return type
T = TypeVar('T')

logger = logging.getLogger(__name__)

# ============================================================================
# PDF Extraction
# ============================================================================

# Lazy-loaded PDF extractor
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


def extract_text_from_pdf_file(file_path: Path) -> str:
    """
    Extract text from a PDF file using pymupdf4llm.

    Returns markdown-formatted text that preserves document structure,
    which works well with the existing hierarchical chunker.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text as markdown string

    Raises:
        ValueError: If PDF extraction fails
    """
    pymupdf4llm = _get_pdf_extractor()

    try:
        # pymupdf4llm.to_markdown() accepts a file path directly
        markdown_text = pymupdf4llm.to_markdown(str(file_path))

        if not markdown_text or not markdown_text.strip():
            raise ValueError("PDF appears to be empty or contains no extractable text")

        logger.info(f"Extracted {len(markdown_text)} chars of text from PDF '{file_path.name}'")
        return markdown_text

    except ImportError as e:
        raise ValueError(f"PDF extraction requires pymupdf4llm: {e}")
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF '{file_path.name}': {e}")


# ============================================================================
# File Validation (Source of Truth for all layers)
# ============================================================================

# Maximum file size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_FILE_SIZE_MB = 10

# Blocked file extensions (binary files that cannot be meaningfully ingested)
# These produce garbage when read as text - block at all layers
BLOCKED_EXTENSIONS = {
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp", ".tiff", ".tif",
    # Videos
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm",
    # Audio
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
    # Archives
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz",
    # Binary/Executables
    ".exe", ".dll", ".so", ".dylib", ".bin", ".app", ".msi",
    # Office docs (binary or ZIP-based, not plain text)
    ".docx", ".xlsx", ".pptx", ".doc", ".xls", ".ppt", ".odt", ".ods", ".odp",
    # Compiled/bytecode
    ".pyc", ".pyo", ".class", ".o", ".obj", ".wasm",
    # Database files
    ".db", ".sqlite", ".sqlite3", ".mdb",
    # Other binary
    ".pdf",  # Note: PDF handled specially, but block here - use validate_file_for_ingestion with allow_pdf=True
    ".iso", ".dmg", ".pkg", ".deb", ".rpm",
}

# PDF extension (handled specially via pymupdf4llm)
PDF_EXTENSION = ".pdf"


def validate_file_for_ingestion(
    file_path: Path,
    file_size: int = None,
    allow_pdf: bool = True,
) -> Dict[str, Any]:
    """
    Validate a file can be ingested (SOURCE OF TRUTH for all layers).

    This function is the single source of truth for file validation.
    Both MCP tools and HTTP routes should use this function.

    Args:
        file_path: Path to the file (or just filename for extension check)
        file_size: File size in bytes (if None, will stat the file)
        allow_pdf: If True, PDFs are allowed (handled via pymupdf4llm)

    Returns:
        Dict with:
            - valid: bool - True if file can be ingested
            - reason: str - Human-readable reason if invalid (None if valid)
            - category: str - Category of rejection (None if valid)
                Categories: "image", "video", "audio", "archive", "binary",
                           "office_doc", "too_large", "empty"
    """
    ext = file_path.suffix.lower()

    # Check if PDF (special handling)
    if ext == PDF_EXTENSION:
        if allow_pdf:
            return {"valid": True, "reason": None, "category": None}
        else:
            return {"valid": False, "reason": "PDF file", "category": "binary"}

    # Check blocked extensions
    if ext in BLOCKED_EXTENSIONS:
        # Determine category for better UX messaging
        if ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp", ".tiff", ".tif"}:
            category = "image"
            reason = "image file"
        elif ext in {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"}:
            category = "video"
            reason = "video file"
        elif ext in {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}:
            category = "audio"
            reason = "audio file"
        elif ext in {".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz"}:
            category = "archive"
            reason = "archive file"
        elif ext in {".docx", ".xlsx", ".pptx", ".doc", ".xls", ".ppt", ".odt", ".ods", ".odp"}:
            category = "office_doc"
            reason = "Office document (use PDF export)"
        else:
            category = "binary"
            reason = "binary file"

        return {"valid": False, "reason": reason, "category": category}

    # Check file size
    if file_size is None:
        try:
            file_size = file_path.stat().st_size
        except (FileNotFoundError, OSError):
            # Can't determine size, let it through (will fail later if truly invalid)
            file_size = 0

    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return {
            "valid": False,
            "reason": f"exceeds {MAX_FILE_SIZE_MB} MB ({size_mb:.1f} MB)",
            "category": "too_large"
        }

    if file_size == 0:
        return {"valid": False, "reason": "empty file", "category": "empty"}

    # File is valid
    return {"valid": True, "reason": None, "category": None}


# Human-readable description for UX (used by frontend and docstrings)
SUPPORTED_FILES_DESCRIPTION = (
    f"Supports text files, code, config, and PDFs up to {MAX_FILE_SIZE_MB} MB. "
    "Images, videos, Office documents, and binary files are not supported."
)


# ============================================================================
# Relevance Scoring for Dry Run Mode
# ============================================================================


async def score_page_relevance(
    pages: List[Dict[str, Any]],
    topic: str,
    max_preview_chars: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Score crawled pages for relevance to a topic using a configurable LLM.

    Uses a configurable model (default: gpt-4o-mini) to evaluate whether each
    page is relevant to the user's stated topic. Returns pages with relevance
    scores and summaries.

    Args:
        pages: List of crawled page dicts with 'url', 'title', 'content' keys
        topic: The user's topic of interest (e.g., "LCEL pipelines in LangChain")
        max_preview_chars: Max chars of content to send per page (default: 2000)

    Returns:
        List of dicts with:
        - url: Page URL
        - title: Page title
        - relevance_score: 0.0-1.0 score (1.0 = highly relevant)
        - relevance_summary: Brief explanation of relevance
        - recommendation: "ingest" or "skip"
    """
    if not pages:
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found for relevance scoring")

    # Load dry_run configuration with fallbacks
    try:
        config = get_instance_config()
        dry_run_model = config.get('dry_run_model', 'gpt-4o-mini')
        dry_run_temperature = float(config.get('dry_run_temperature', 0.1))
        dry_run_max_tokens = int(config.get('dry_run_max_tokens', 2000))
    except Exception:
        # Fallback to defaults if config loading fails
        dry_run_model = 'gpt-4o-mini'
        dry_run_temperature = 0.1
        dry_run_max_tokens = 2000

    client = OpenAI(api_key=api_key)

    # Build batch prompt for efficiency
    pages_for_scoring = []
    for i, page in enumerate(pages):
        preview = page.get("content", "")[:max_preview_chars]
        pages_for_scoring.append({
            "index": i,
            "url": page.get("url", ""),
            "title": page.get("title", page.get("url", "")),
            "preview": preview,
        })

    # Create the scoring prompt - V6 with semantic matching
    system_prompt = """You are a relevance evaluator helping users build focused knowledge bases.
Your goal: recommend pages that genuinely cover the user's topic, filter noise.

PHILOSOPHY: Err on the side of caution. Better to skip a marginally useful page than pollute
the knowledge base with irrelevant content. The user can always override your recommendations.

EVIDENCE TO LOOK FOR:
- Topic keywords OR semantic equivalents in page title or headings
  (don't require literal matches - look for conceptual overlap)
- Code examples demonstrating the topic
- Tutorials or detailed explanations about the topic
- The topic being a PRIMARY focus, not just mentioned

SEMANTIC MATCHING - consider these equivalent:
- "installation" ↔ "setup", "getting started", "quickstart"
- "commands" ↔ "CLI reference", "terminal", "flags", "options"
- "permissions" ↔ "security", "access control", "allowlist"
- "settings" ↔ "configuration", "options", "preferences"
- "tools" ↔ "integrations", "plugins", "extensions", "MCP"

SCORING RULES:
- 0.85-1.0: Topic is the PRIMARY focus (title match AND substantial content)
- 0.65-0.84: Topic is a MAJOR focus (detailed coverage, code examples, or tutorial)
- 0.45-0.64: Topic is DISCUSSED meaningfully but page has broader scope
- 0.25-0.44: Topic only MENTIONED in passing or tangentially related
- 0.0-0.24: No meaningful topic coverage

AUTOMATIC SCORE CAPS (apply these AFTER scoring):
- Generic homepages/landing pages: max 0.35
- Navigation-only or index pages: max 0.30
- Contributing/changelog/license pages: max 0.20
- Legal/compliance/data policy pages: max 0.25

RECOMMENDATION RULES:
- Score >= 0.50: recommend "ingest" - page has meaningful topic coverage
- Score 0.40-0.49: recommend "review" - borderline, user should decide
- Score < 0.40: recommend "skip" - insufficient topic coverage

SUMMARY REQUIREMENTS (CRITICAL):
Write summaries that help an AI agent advise users. Be specific about:
1. What the page ACTUALLY covers (its main subject)
2. Whether the topic match is DIRECT (page is about the topic) or INDIRECT (shares keywords but different subject)
3. If recommending "ingest", state what specific evidence you found
4. If recommending "skip", briefly state what the page is actually about

BAD summary: "Covers Agent Skills, relevant to multi-agent workflows."
GOOD summary: "Page covers giving Claude specialized domain skills. Not about spawning/coordinating multiple agents."

BAD summary: "Discusses MCP, related to agent tools."
GOOD summary: "Page explains MCP protocol for connecting external tools. No coverage of sub-agent orchestration."

Output JSON array with:
- "index": page index
- "relevance_score": float 0.0-1.0
- "relevance_summary": 1-2 sentences explaining what the page covers and why it does/doesn't match (max 200 chars)
- "recommendation": "ingest", "review", or "skip"

Only output valid JSON, no markdown formatting."""

    user_prompt = f"""Topic: {topic}

Pages to evaluate:
{json.dumps(pages_for_scoring, indent=2)}

Score each page's relevance to the topic."""

    try:
        response = client.chat.completions.create(
            model=dry_run_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=dry_run_temperature,
            max_completion_tokens=dry_run_max_tokens,
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            # Remove markdown code block formatting
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        scores = json.loads(response_text)

        # Build results with original page data
        results = []
        score_map = {s["index"]: s for s in scores}

        for i, page in enumerate(pages):
            score_data = score_map.get(i, {
                "relevance_score": 0.0,
                "relevance_summary": "Scoring failed",
                "recommendation": "skip"
            })

            results.append({
                "url": page.get("url", ""),
                "title": page.get("title", page.get("url", "")),
                "relevance_score": float(score_data.get("relevance_score", 0.0)),
                "relevance_summary": score_data.get("relevance_summary", ""),
                "recommendation": score_data.get("recommendation", "skip"),
            })

        # Sort by relevance score descending
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        ingest_count = sum(1 for r in results if r['recommendation'] == 'ingest')
        review_count = sum(1 for r in results if r['recommendation'] == 'review')
        skip_count = sum(1 for r in results if r['recommendation'] == 'skip')
        logger.info(
            f"Relevance scoring complete: {len(results)} pages scored - "
            f"ingest={ingest_count}, review={review_count}, skip={skip_count}"
        )

        return results

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse relevance scoring response: {e}")
        # Return pages with neutral scores on parse failure
        return [
            {
                "url": page.get("url", ""),
                "title": page.get("title", page.get("url", "")),
                "relevance_score": 0.5,
                "relevance_summary": "Scoring response could not be parsed",
                "recommendation": "review",
            }
            for page in pages
        ]
    except Exception as e:
        logger.error(f"Relevance scoring failed: {e}")
        raise


# ============================================================================
# Analysis Token Store (in-memory, ephemeral)
# ============================================================================
# Tokens are reusable, expire after 4 hours
# Long expiry accounts for real-world usage: user reviews analysis, gets
# distracted, comes back hours later to approve crawl
# Reusable design supports multiple targeted crawls of same site without
# redundant analysis calls


async def ensure_databases_healthy(
    db: Database, graph_store: Optional[GraphStore] = None
) -> Optional[Dict[str, Any]]:
    """
    Check both PostgreSQL and Neo4j are reachable before any write operation.

    This middleware function provides fail-fast validation with clear error
    messages when databases are unavailable.

    Args:
        db: Database instance (always required)
        graph_store: GraphStore instance (required for Option B: Mandatory Graph)

    Returns:
        None if both databases are healthy (operation can proceed).
        Otherwise returns error response dict for MCP client:
            {
                "error": str,                    # Error category
                "status": str,                   # MCP status code
                "message": str,                  # Human-readable message
                "details": {                     # Debug info (internal use)
                    "postgres": {...},           # PostgreSQL health result
                    "neo4j": {...},              # Neo4j health result
                    "retry_after_seconds": int
                }
            }

    Note:
        - PostgreSQL check is always mandatory
        - Neo4j check is mandatory per Gap 2.1 (Option B: All or Nothing)
        - Health check latency: ~5-30ms local, ~50-200ms cloud
    """
    # Check PostgreSQL (ALWAYS REQUIRED)
    pg_health = await db.health_check(timeout_ms=2000)
    if pg_health["status"] != "healthy":
        return {
            "error": "Database unavailable",
            "status": "service_unavailable",
            "message": "PostgreSQL is temporarily unavailable. Please try again in 30 seconds.",
            "details": {
                "postgres": pg_health,
                "retry_after_seconds": 30,
            },
        }

    # Check Neo4j if initialized (REQUIRED for Option B: Mandatory Graph)
    if graph_store is not None:
        graph_health = await graph_store.health_check(timeout_ms=2000)

        # "unavailable" status = Graphiti not initialized (graceful, not an error)
        # "unhealthy" status = Neo4j reachable but not responding (ERROR)
        if graph_health["status"] == "unhealthy":
            return {
                "error": "Knowledge graph unavailable",
                "status": "service_unavailable",
                "message": "Neo4j is temporarily unavailable. Please try again in 30 seconds.",
                "details": {
                    "postgres": pg_health,
                    "neo4j": graph_health,
                    "retry_after_seconds": 30,
                },
            }

    return None  # All checks passed, operation can proceed


# ============================================================================
# Database Error Handling Decorators
# ============================================================================
# These decorators wrap tool implementations to catch database connection errors
# and return clean, structured error responses instead of stack traces.


def handle_database_errors(operation_name: str = "operation"):
    """
    Decorator that catches database connection errors and returns clean error responses.

    Wraps tool implementation functions to:
    1. Catch OperationalError (connection terminated, timeout, etc.)
    2. Catch ConnectionError (retry exhausted in Database.connect())
    3. Return structured MCP-compatible error response instead of stack traces

    Args:
        operation_name: Human-readable name of the operation for error messages

    Example:
        @handle_database_errors("document search")
        def search_documents_impl(...):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except (OperationalError, DatabaseError) as e:
                error_msg = str(e)
                logger.error(f"Database error during {operation_name}: {error_msg}")

                # Detect specific error types for better messages
                if "terminating connection" in error_msg.lower():
                    message = (
                        f"Database connection was terminated during {operation_name}. "
                        "This may be temporary. Please retry in a few seconds."
                    )
                elif "connection" in error_msg.lower() and "refused" in error_msg.lower():
                    message = (
                        f"Cannot connect to database for {operation_name}. "
                        "Database may be temporarily unavailable. Please retry in 30 seconds."
                    )
                else:
                    message = (
                        f"Database error during {operation_name}. "
                        "Please retry. If the problem persists, check database connectivity."
                    )

                return {
                    "error": "database_error",
                    "status": "service_unavailable",
                    "message": message,
                    "retry_after_seconds": 30,
                }
            except ConnectionError as e:
                # Raised by Database.connect() after retries exhausted
                logger.error(f"Connection error during {operation_name}: {e}")
                return {
                    "error": "connection_failed",
                    "status": "service_unavailable",
                    "message": (
                        f"Could not establish database connection for {operation_name}. "
                        "Database may be down. Please retry in 30 seconds."
                    ),
                    "retry_after_seconds": 30,
                }
        return wrapper

    return decorator


def handle_database_errors_async(operation_name: str = "operation"):
    """
    Async version of handle_database_errors for async tool implementations.

    Same behavior as handle_database_errors but for async functions.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except (OperationalError, DatabaseError) as e:
                error_msg = str(e)
                logger.error(f"Database error during {operation_name}: {error_msg}")

                if "terminating connection" in error_msg.lower():
                    message = (
                        f"Database connection was terminated during {operation_name}. "
                        "This may be temporary. Please retry in a few seconds."
                    )
                elif "connection" in error_msg.lower() and "refused" in error_msg.lower():
                    message = (
                        f"Cannot connect to database for {operation_name}. "
                        "Database may be temporarily unavailable. Please retry in 30 seconds."
                    )
                else:
                    message = (
                        f"Database error during {operation_name}. "
                        "Please retry. If the problem persists, check database connectivity."
                    )

                return {
                    "error": "database_error",
                    "status": "service_unavailable",
                    "message": message,
                    "retry_after_seconds": 30,
                }
            except ConnectionError as e:
                logger.error(f"Connection error during {operation_name}: {e}")
                return {
                    "error": "connection_failed",
                    "status": "service_unavailable",
                    "message": (
                        f"Could not establish database connection for {operation_name}. "
                        "Database may be down. Please retry in 30 seconds."
                    ),
                    "retry_after_seconds": 30,
                }
        return wrapper

    return decorator


# ============================================================================
# Centralized Validation Functions (Single Source of Truth)
# ============================================================================
# These functions provide consistent validation across all ingest tools.
# Centralizing these patterns ensures that when we modify validation logic
# (e.g., add a new mode, change collection checks), we update ONE place
# instead of 4 separate tool implementations.


def validate_mode(mode: str) -> None:
    """
    Validate ingest mode parameter.

    Centralized validation ensures all 4 ingest tools accept the same modes.
    When we add a new mode (e.g., "update", "merge"), we update this ONE function.

    Args:
        mode: The mode string to validate

    Raises:
        ValueError: If mode is not valid
    """
    if mode not in ["ingest", "reingest"]:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'ingest' or 'reingest'")


def validate_collection_exists(doc_store: DocumentStore, collection_name: str) -> None:
    """
    Validate that collection exists before ingestion.

    Centralized validation ensures all 4 ingest tools check collections identically.
    When we add collection-level features (quotas, permissions), we update this ONE function.

    Args:
        doc_store: Document store instance
        collection_name: Collection name to validate

    Raises:
        ValueError: If collection doesn't exist
    """
    collection = doc_store.collection_mgr.get_collection(collection_name)
    if not collection:
        raise ValueError(
            f"Collection '{collection_name}' does not exist. "
            f"Create it first using create_collection('{collection_name}', 'description')."
        )


def read_file_with_metadata(
    file_path: Path, user_metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Read file and prepare metadata for ingestion.

    Centralized file reading ensures ingest_file and ingest_directory handle files identically.
    When we add file-level features (encoding detection, MIME types, file hashes),
    we update this ONE function.

    Supports:
    - Text files: Read as UTF-8 with error handling (any text-based format)
    - PDF files: Extract text as markdown using pymupdf4llm

    Does NOT support (will raise ValueError):
    - Images, videos, audio files
    - Archives (zip, tar, etc.)
    - Office documents (docx, xlsx - use PDF export)
    - Binary/executable files
    - Files larger than 10 MB

    Args:
        file_path: Path to file to read
        user_metadata: Optional user-provided metadata to merge

    Returns:
        Tuple of (file_content, merged_metadata)

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
        ValueError: If file type is not supported or PDF extraction fails
    """
    file_size = file_path.stat().st_size
    file_type = file_path.suffix.lstrip(".").lower() or "text"

    # Validate file can be ingested (SOURCE OF TRUTH)
    validation = validate_file_for_ingestion(file_path, file_size=file_size, allow_pdf=True)
    if not validation["valid"]:
        raise ValueError(
            f"Cannot ingest '{file_path.name}': {validation['reason']}. "
            f"{SUPPORTED_FILES_DESCRIPTION}"
        )

    # Handle PDF files specially using pymupdf4llm
    if file_type == "pdf":
        content = extract_text_from_pdf_file(file_path)
    else:
        # Read as text file (UTF-8 with error handling)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

    # Merge user metadata with file metadata
    metadata = user_metadata.copy() if user_metadata else {}
    metadata.update({
        "file_type": file_type,
        "file_size": file_size,
        "file_path": str(file_path.absolute()),
    })

    return content, metadata


@handle_database_errors("document search")
def search_documents_impl(
    searcher: SimilaritySearch,
    query: str,
    collection_name: Optional[str],
    limit: int,
    threshold: float,
    include_source: bool,
    include_metadata: bool,
    metadata_filter: dict | None = None,
    # Evaluation filters (all optional, default returns all)
    reviewed_by_human: bool | None = None,
    min_quality_score: float | None = None,
    min_topic_relevance: float | None = None,
) -> List[Dict[str, Any]]:
    """Implementation of search_documents tool."""
    try:
        # Execute search with evaluation filters
        results = searcher.search_chunks(
            query=query,
            limit=min(limit, 50),  # Cap at 50
            threshold=threshold if threshold is not None else 0.0,
            collection_name=collection_name,
            include_source=include_source,
            metadata_filter=metadata_filter,
            # Pass evaluation filters
            reviewed_by_human=reviewed_by_human,
            min_quality_score=min_quality_score,
            min_topic_relevance=min_topic_relevance,
        )

        # Convert ChunkSearchResult objects to dicts
        # Minimal response by default (optimized for AI agent context windows)
        results_list = []
        for r in results:
            result = {
                "content": r.content,
                "similarity": float(r.similarity),
                "source_document_id": r.source_document_id,
                "source_filename": r.source_filename,
                # Always include evaluation fields (from source_documents)
                "reviewed_by_human": r.reviewed_by_human,
                "quality_score": r.quality_score,
                "topic_relevance_score": r.topic_relevance_score,
            }

            # Optionally include extended metadata (chunk details)
            if include_metadata:
                result.update({
                    "chunk_id": r.chunk_id,
                    "chunk_index": r.chunk_index,
                    "char_start": r.char_start,
                    "char_end": r.char_end,
                    "metadata": r.metadata or {},
                })

            # Optionally include full source document content
            if include_source:
                result["source_content"] = r.source_content

            results_list.append(result)

        return results_list
    except Exception as e:
        logger.error(f"search_documents failed: {e}")
        raise


@handle_database_errors("list collections")
def list_collections_impl(coll_mgr: CollectionManager) -> List[Dict[str, Any]]:
    """Implementation of list_collections tool."""
    try:
        collections = coll_mgr.list_collections()

        # Convert datetime to ISO 8601 string
        return [
            {
                "name": c["name"],
                "description": c["description"] or "",
                "document_count": c["document_count"],
                "created_at": (
                    c["created_at"].isoformat() if c.get("created_at") else None
                ),
            }
            for c in collections
        ]
    except Exception as e:
        logger.error(f"list_collections failed: {e}")
        raise


def update_collection_metadata_impl(
    coll_mgr: CollectionManager,
    collection_name: str,
    new_fields: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Implementation of update_collection_metadata MCP tool.

    Updates a collection's metadata schema (additive only, mandatory fields immutable).

    MANDATORY FIELD UPDATE RULES:

    domain and domain_scope: IMMUTABLE - cannot be changed after creation.
        Attempting to change these fields will raise ValueError.

    topics: ADDITIVE-ONLY - new topics can be added, existing topics preserved.
        When updating topics, provide the new topics to ADD:
        {
            "mandatory": {
                "topics": ["new_topic_1", "new_topic_2"]
            }
        }
        System will merge new topics with existing (deduplicating), so you don't need to
        provide the full list - just the new ones you want to add.

    CUSTOM FIELD UPDATE RULES:

    New custom fields can be added (required=false, additive-only).
    Existing custom fields cannot be removed or have types changed.

    Args:
        coll_mgr: CollectionManager instance
        collection_name: Collection name to update
        new_fields: New schema fields to add/merge. Format:
            {
                "mandatory": {
                    "topics": ["new_topic_1", "new_topic_2"]  # Merged with existing
                },
                "custom": {
                    "new_field": {"type": "string", "required": false}
                }
            }

    Returns:
        {
            "name": str,
            "description": str,
            "metadata_schema": dict,
            "fields_added": int,
            "total_custom_fields": int
        }

    Raises:
        ValueError: If trying to change immutable fields (domain, domain_scope),
                   remove custom fields, or violate additive-only constraints
    """
    try:
        # Wrap new_fields in custom if it's just bare fields (backward compatibility)
        if "custom" not in new_fields and "mandatory" not in new_fields:
            new_fields = {"custom": new_fields}

        # Get current state before update
        current = coll_mgr.get_collection(collection_name)
        if not current:
            raise ValueError(f"Collection '{collection_name}' not found")

        current_custom_count = len(current["metadata_schema"].get("custom", {}))

        # Update the schema (handles mandatory validation)
        updated = coll_mgr.update_collection_metadata_schema(collection_name, new_fields)

        new_custom_count = len(updated["metadata_schema"].get("custom", {}))

        return {
            "name": updated["name"],
            "description": updated["description"],
            "metadata_schema": updated["metadata_schema"],
            "fields_added": new_custom_count - current_custom_count,
            "total_custom_fields": new_custom_count
        }
    except ValueError as e:
        logger.warning(f"update_collection_metadata failed: {e}")
        raise
    except Exception as e:
        logger.error(f"update_collection_metadata error: {e}")
        raise


def create_collection_impl(
    coll_mgr: CollectionManager,
    name: str,
    description: str,
    domain: str,
    domain_scope: str | None = None,
    metadata_schema: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Implementation of create_collection MCP tool.

    Creates a collection with mandatory scope fields (domain, domain_scope) and optional custom metadata fields.

    MANDATORY FIELDS (required at creation, define collection scope):

    domain (string, required):
        Single knowledge domain for this collection. Examples: "quantum computing", "molecular biology", "aviation"
        Immutable - cannot be changed after creation.
        Purpose: Partitions knowledge graph by meaningful knowledge areas.

    domain_scope (string, required):
        Natural language specification of collection boundaries.
        Example: "Covers quantum computing theory and applications. Excludes quantum biology, quantum cryptography outside computing."
        Immutable - cannot be changed after creation.
        Purpose: Helps LLMs understand scope when deciding what documents to ingest.

    CUSTOM FIELDS (optional, user-defined):

    metadata_schema (dict, optional):
        Declare custom metadata fields for documents in this collection. Format:
        {
            "custom": {
                "doc_type": {
                    "type": "string",
                    "description": "Type of document",
                    "required": false,
                    "enum": ["article", "paper", "book"]
                },
                "priority": {
                    "type": "string",
                    "required": false
                }
            }
        }
        New fields must be optional (required=false or omitted).
        Custom fields are additive-only - new fields can be added later but never removed.

    Args:
        coll_mgr: CollectionManager instance
        name: Unique collection name
        description: Collection description (mandatory, non-empty)
        domain: Knowledge domain (mandatory, singular, immutable)
        domain_scope: Domain boundary description (mandatory, immutable)
        metadata_schema: Optional custom field declarations

    Returns:
        {
            "collection_id": int,
            "name": str,
            "description": str,
            "domain": str,
            "domain_scope": str,
            "metadata_schema": dict,
            "created": true
        }

    Raises:
        ValueError: If mandatory fields invalid, custom schema invalid, or collection already exists
    """
    try:
        # Validate mandatory fields
        if not domain or not isinstance(domain, str):
            raise ValueError("domain must be a non-empty string")
        if not domain_scope or not isinstance(domain_scope, str):
            raise ValueError("domain_scope must be a non-empty string")

        # Call updated create_collection with mandatory fields
        collection_id = coll_mgr.create_collection(
            name=name,
            description=description,
            domain=domain,
            domain_scope=domain_scope,
            metadata_schema=metadata_schema,
        )

        collection = coll_mgr.get_collection(name)

        return {
            "collection_id": collection_id,
            "name": name,
            "description": description,
            "domain": domain,
            "domain_scope": domain_scope,
            "metadata_schema": collection.get("metadata_schema"),
            "created": True,
        }
    except ValueError as e:
        logger.warning(f"create_collection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"create_collection failed: {e}")
        raise


def get_collection_metadata_schema_impl(
    coll_mgr: CollectionManager, collection_name: str
) -> Dict[str, Any]:
    """
    Implementation of get_collection_metadata_schema MCP tool.

    Returns the metadata schema for a collection showing what fields to use when ingesting
    and what fields define the collection's scope.

    MANDATORY FIELDS (collection-scoped, immutable):
    - domain: Single knowledge domain (immutable)
    - domain_scope: Domain boundaries description (immutable)
    These define what the collection is about. Domain and domain_scope are automatically applied
    to all documents ingested into this collection.

    CUSTOM FIELDS (user-defined, required/optional):
    - User-declared fields for metadata on documents
    - Each field specifies type and whether it's required when ingesting
    - New fields can be added later, existing ones never removed

    Note: System fields are NOT included in this response. They are internal implementation
    details auto-generated during ingestion. LLMs should NOT provide system fields when ingesting.

    Args:
        coll_mgr: CollectionManager instance
        collection_name: Collection name to retrieve schema for

    Returns:
        {
            "collection_name": str,
            "description": str,
            "document_count": int,
            "metadata_schema": {
                "mandatory_fields": {
                    "domain": {
                        "type": "string",
                        "value": str,
                        "immutable": true,
                        "description": "..."
                    },
                    "domain_scope": {
                        "type": "string",
                        "value": str,
                        "immutable": true,
                        "description": "..."
                    }
                },
                "custom_fields": {
                    "field_name": {
                        "type": "string|number|array|object|boolean",
                        "required": true|false,
                        "enum": [...],
                        "description": "..."
                    },
                    ...
                }
            }
        }

    Raises:
        ValueError: If collection not found
    """
    try:
        collection = coll_mgr.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")

        schema = collection.get("metadata_schema", {})
        mandatory = schema.get("mandatory", {})
        custom = schema.get("custom", {})

        # Build mandatory fields section
        mandatory_fields = {}
        if mandatory:
            mandatory_fields["domain"] = {
                "type": "string",
                "value": mandatory.get("domain"),
                "immutable": True,
                "description": "Single knowledge domain for this collection. Set at creation, cannot be changed. Automatically applied to all ingested documents."
            }
            mandatory_fields["domain_scope"] = {
                "type": "string",
                "value": mandatory.get("domain_scope"),
                "immutable": True,
                "description": "Natural language definition of domain boundaries (what is/isn't in scope). Set at creation, cannot be changed. Automatically applied to all ingested documents."
            }

        # Build custom fields section
        custom_fields = {}
        for name, field_def in custom.items():
            custom_fields[name] = {
                "type": field_def.get("type", "string"),
                "required": field_def.get("required", False),
                "description": field_def.get("description", "")
            }
            # Include enum if present
            if "enum" in field_def:
                custom_fields[name]["enum"] = field_def["enum"]

        return {
            "collection_name": collection_name,
            "description": collection["description"],
            "document_count": collection["document_count"],
            "metadata_schema": {
                "mandatory_fields": mandatory_fields,
                "custom_fields": custom_fields
            }
        }
    except ValueError as e:
        logger.warning(f"get_collection_metadata_schema failed: {e}")
        raise
    except Exception as e:
        logger.error(f"get_collection_metadata_schema failed: {e}")
        raise


async def delete_collection_impl(
    coll_mgr: CollectionManager,
    name: str,
    confirm: bool = False,
    graph_store = None,
    db = None,
) -> Dict[str, Any]:
    """
    Implementation of delete_collection tool.

    Deletes a collection and all its documents permanently.
    Requires explicit confirmation to prevent accidental data loss.

    If graph_store is provided, also cleans up all episode nodes linked to documents
    in this collection (Phase 4 cleanup).

    Args:
        coll_mgr: CollectionManager instance
        name: Collection name to delete
        confirm: MUST be True to proceed (prevents accidental deletion)
        graph_store: Optional GraphStore for episode cleanup
        db: Optional Database instance (needed if graph_store provided)

    Returns:
        {
            "name": str,
            "deleted": bool,
            "message": str
        }

    Raises:
        ValueError: If collection not found or confirm not set
    """
    try:
        # Require explicit confirmation
        if not confirm:
            raise ValueError(
                f"Deletion requires confirmation. Use confirm=True to proceed. "
                f"WARNING: This will permanently delete collection '{name}' and all its documents."
            )

        # First, get collection info to report what's being deleted
        collection_info = coll_mgr.get_collection(name)
        if not collection_info:
            raise ValueError(f"Collection '{name}' not found")

        doc_count = collection_info.get("document_count", 0)

        # Get source document IDs for graph cleanup BEFORE deletion
        source_doc_ids = []
        if graph_store and db:
            try:
                conn = db.connect()
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT DISTINCT dc.source_document_id
                        FROM document_chunks dc
                        INNER JOIN chunk_collections cc ON dc.id = cc.chunk_id
                        INNER JOIN collections c ON cc.collection_id = c.id
                        WHERE c.name = %s
                        """,
                        (name,),
                    )
                    source_doc_ids = [row[0] for row in cur.fetchall()]
                logger.info(
                    f"Found {len(source_doc_ids)} source documents to clean from graph"
                )
            except Exception as e:
                logger.warning(f"Could not fetch source_doc_ids for graph cleanup: {e}")
                source_doc_ids = []

        # Perform RAG deletion
        deleted = await coll_mgr.delete_collection(name)

        if not deleted:
            raise ValueError(f"Collection '{name}' not found")

        logger.info(f"Deleted collection '{name}' with {doc_count} documents")

        # Clean up graph episodes (Phase 4 implementation)
        deleted_episodes = 0
        if graph_store and source_doc_ids:
            try:
                logger.info(f"Cleaning up {len(source_doc_ids)} episodes from graph...")
                for doc_id in source_doc_ids:
                    episode_name = f"doc_{doc_id}"
                    deleted = await graph_store.delete_episode_by_name(episode_name)
                    if deleted:
                        deleted_episodes += 1
                logger.info(
                    f"✅ Graph cleanup complete - {deleted_episodes} episodes deleted"
                )
            except Exception as e:
                logger.warning(
                    f"Graph cleanup encountered issues: {e}. "
                    "RAG data is clean, but some graph episodes may remain."
                )

        message = (
            f"Collection '{name}' and {doc_count} document(s) permanently deleted."
        )
        if deleted_episodes > 0:
            message += f" ({deleted_episodes} graph episodes cleaned)"
        elif graph_store and source_doc_ids:
            message += " (⚠️ Graph cleanup attempted but may have issues)"

        return {
            "name": name,
            "deleted": True,
            "message": message,
        }
    except ValueError as e:
        logger.warning(f"delete_collection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"delete_collection failed: {e}")
        raise


@handle_database_errors_async("text ingestion")
@deduplicate_request()
async def ingest_text_impl(
    db: Database,
    doc_store: DocumentStore,
    unified_mediator,
    graph_store: Optional[GraphStore],
    content: str,
    collection_name: str,
    document_title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    include_chunk_ids: bool = False,
    progress_callback=None,
    mode: str = "ingest",
    # Evaluation parameters
    topic: Optional[str] = None,
    reviewed_by_human: bool = False,
    # Audit parameters
    actor_type: str = "agent",
) -> Dict[str, Any]:
    """
    Implementation of ingest_text tool.

    Routes through unified mediator to update both RAG and Knowledge Graph.
    Uses content hash for reliable duplicate detection.

    Behavior:
    - mode=ingest + same content: Smart update (metadata, eval if topic changed, no re-embed/graph)
    - mode=reingest + same content: Full delete + fresh ingest
    - new content: Full ingest

    Args:
        progress_callback: Optional async callback for MCP progress notifications
        topic: Optional topic for relevance scoring (triggers re-eval if changed)
        reviewed_by_human: Set to True ONLY when user explicitly confirmed review
        actor_type: Who is performing this ingestion ("agent", "user", or "api")
    """
    # Import here to avoid circular imports
    from src.mcp.evaluation import evaluate_content

    try:
        # Health check: both PostgreSQL and Neo4j must be reachable
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return health_error

        # Validate collection exists (centralized)
        validate_collection_exists(doc_store, collection_name)

        # Validate mode (centralized)
        validate_mode(mode)

        # Compute content hash for duplicate detection
        content_hash = compute_content_hash(content)
        logger.info(f"Content hash: {content_hash[:12]}...")

        # Check for existing document with same content hash in ANY collection (global check)
        existing_doc = check_duplicate_by_hash_global(db, content_hash)

        # Get collection description for evaluation (needed for both paths)
        collection = doc_store.collection_mgr.get_collection(collection_name)
        collection_description = collection.get("description", "") if collection else ""

        # =====================================================================
        # CASE 0: Content exists in DIFFERENT collection + mode=ingest = Error with options
        # (mode=reingest will delete and re-ingest in CASE 2 below)
        # =====================================================================
        if mode == "ingest" and existing_doc and collection_name not in existing_doc.get("collections", []):
            existing_collection = existing_doc["collections"][0] if existing_doc["collections"] else "unknown"
            logger.warning(
                f"Content exists in different collection '{existing_collection}' "
                f"(doc_id={existing_doc['doc_id']}), target was '{collection_name}'"
            )
            return {
                "error": "content_exists_in_other_collection",
                "status": "error",
                "message": (
                    f"This content already exists in collection '{existing_collection}' "
                    f"(document_id: {existing_doc['doc_id']}, title: '{existing_doc['filename']}'). "
                    f"Use manage_collection_link to add it to '{collection_name}', "
                    f"or mode='reingest' to move it."
                ),
                "existing_document_id": existing_doc["doc_id"],
                "existing_collection": existing_collection,
                "existing_collections": existing_doc["collections"],
                "target_collection": collection_name,
                "options": {
                    "link": f"manage_collection_link(document_id={existing_doc['doc_id']}, collection_name='{collection_name}')",
                    "move": f"Use mode='reingest' to delete from '{existing_collection}' and ingest fresh to '{collection_name}'"
                }
            }

        # =====================================================================
        # CASE 1: mode=ingest + content hash matches in SAME collection = Smart Update
        # =====================================================================
        if mode == "ingest" and existing_doc and collection_name in existing_doc.get("collections", []):
            logger.info(f"Content hash matches existing doc ID={existing_doc['doc_id']} - smart update mode")

            if progress_callback:
                await progress_callback(10, 100, "Content unchanged, updating metadata...")

            # Determine if we need to re-run LLM evaluation
            # Re-evaluate if topic changed (including None→T, T→None, T1→T2)
            existing_topic = existing_doc.get("topic_provided")
            needs_eval = (topic != existing_topic)

            eval_result = None
            if needs_eval:
                logger.info(f"Topic changed ({existing_topic} → {topic}), re-running evaluation")
                if progress_callback:
                    await progress_callback(30, 100, "Re-evaluating with new topic...")
                eval_result = await evaluate_content(
                    content=content,
                    collection_name=collection_name,
                    collection_description=collection_description,
                    topic=topic,
                )

            # Build update parameters
            # Metadata: MERGE with existing (new values take precedence)
            # reviewed_by_human: Use if provided, else keep existing
            update_reviewed = reviewed_by_human if reviewed_by_human else None

            # MERGE existing metadata with new metadata (new values take precedence)
            # If no new metadata provided, don't update metadata at all
            merged_metadata = None
            if metadata is not None:
                merged_metadata = {**(existing_doc.get("metadata") or {}), **metadata}

            # Update document metadata without re-embedding or re-graphing
            if progress_callback:
                await progress_callback(70, 100, "Updating document metadata...")

            # Note: filename intentionally NOT updated to preserve existing LLM-generated title
            update_result = update_document_metadata_only(
                db=db,
                doc_id=existing_doc["doc_id"],
                metadata=merged_metadata,  # MERGE with existing, not replace
                reviewed_by_human=update_reviewed,
                topic_provided=topic if needs_eval else None,
                quality_score=eval_result.quality_score if eval_result else None,
                quality_summary=eval_result.quality_summary if eval_result else None,
                topic_relevance_score=eval_result.topic_relevance_score if eval_result else None,
                topic_relevance_summary=eval_result.topic_relevance_summary if eval_result else None,
                eval_model=eval_result.model if eval_result else None,
                eval_timestamp=eval_result.timestamp if eval_result else None,
            )

            if progress_callback:
                await progress_callback(100, 100, "Update complete")

            # Build evaluation response
            if eval_result:
                evaluation = {
                    "quality_score": eval_result.quality_score,
                    "quality_summary": eval_result.quality_summary,
                }
                if topic:
                    evaluation["topic_relevance_score"] = eval_result.topic_relevance_score
                    evaluation["topic_relevance_summary"] = eval_result.topic_relevance_summary
                    evaluation["topic_provided"] = eval_result.topic_provided
            else:
                # Keep existing evaluation
                evaluation = {
                    "quality_score": existing_doc.get("quality_score"),
                    "quality_summary": existing_doc.get("quality_summary"),
                }
                if existing_doc.get("topic_provided"):
                    evaluation["topic_relevance_score"] = existing_doc.get("topic_relevance_score")
                    evaluation["topic_relevance_summary"] = existing_doc.get("topic_relevance_summary")
                    evaluation["topic_provided"] = existing_doc.get("topic_provided")

            # Audit logging (use existing title, not caller-provided document_title)
            create_audit_entry(
                db=db,
                source_document_id=existing_doc["doc_id"],
                actor_type=actor_type,
                ingest_method="text",
                collection_name=collection_name,
                metadata={
                    "document_title": existing_doc["filename"],  # Preserved title
                    "content_length": len(content),
                    "action": "smart_update",
                    "evaluation_rerun": needs_eval,
                    "updated_fields": update_result["updated_fields"],
                },
            )

            return {
                "status": "updated",
                "source_document_id": existing_doc["doc_id"],
                "content_changed": False,
                "evaluation_rerun": needs_eval,
                "updated_fields": update_result["updated_fields"],
                "collection_name": collection_name,
                "evaluation": evaluation,
                "message": f"Content unchanged (hash match). Metadata updated. "
                           f"{'Evaluation re-run with new topic.' if needs_eval else 'Evaluation preserved.'}",
            }

        # =====================================================================
        # CASE 2: mode=reingest + content hash matches = Full Delete + Fresh Ingest
        # =====================================================================
        if mode == "reingest" and existing_doc:
            if progress_callback:
                await progress_callback(5, 100, f"Deleting old version (doc ID={existing_doc['doc_id']})...")

            logger.info(f"Reingest mode: Deleting old document ID={existing_doc['doc_id']}")

            # Use centralized deletion with error handling
            await delete_document_for_reingest(
                doc_id=existing_doc['doc_id'],
                doc_store=doc_store,
                graph_store=graph_store,
                filename=existing_doc.get('filename', 'unknown')
            )
            # Continue to full ingest below

        # =====================================================================
        # CASE 3: New content OR mode=reingest after deletion = Full Ingest
        # =====================================================================

        # Auto-generate title if not provided
        if not document_title:
            document_title = f"Agent-Text-{datetime.now().isoformat()}"

        # Run LLM evaluation (always for new content)
        logger.info(f"Running content evaluation (topic={'provided' if topic else 'none'})")
        eval_result = await evaluate_content(
            content=content,
            collection_name=collection_name,
            collection_description=collection_description,
            topic=topic,
        )

        # Route through unified mediator (RAG + Graph) with progress callback
        logger.info("Ingesting text through unified mediator (RAG + Graph)")
        result = await unified_mediator.ingest_text(
            content=content,
            collection_name=collection_name,
            document_title=document_title,
            metadata=metadata,
            progress_callback=progress_callback,
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

        # Remove chunk_ids if not requested (minimize response size)
        if not include_chunk_ids:
            result.pop("chunk_ids", None)

        # Add evaluation to response
        evaluation = {
            "quality_score": eval_result.quality_score,
            "quality_summary": eval_result.quality_summary,
        }
        if topic:
            evaluation["topic_relevance_score"] = eval_result.topic_relevance_score
            evaluation["topic_relevance_summary"] = eval_result.topic_relevance_summary
            evaluation["topic_provided"] = eval_result.topic_provided
        result["evaluation"] = evaluation

        # Add status to indicate full ingest vs reingest
        if mode == "reingest" and existing_doc:
            result["status"] = "reingested"
        else:
            result["status"] = "ingested"

        # Audit logging
        create_audit_entry(
            db=db,
            source_document_id=result["source_document_id"],
            actor_type=actor_type,
            ingest_method="text",
            collection_name=collection_name,
            metadata={
                "document_title": document_title,
                "content_length": len(content),
                "evaluation": evaluation,
                "action": "reingest" if mode == "reingest" else "ingest",
            },
        )

        return result
    except Exception as e:
        logger.error(f"ingest_text failed: {e}")
        raise


@handle_database_errors("get document")
def get_document_by_id_impl(
    doc_store: DocumentStore, document_id: int, include_chunks: bool
) -> Dict[str, Any]:
    """Implementation of get_document_by_id tool."""
    try:
        doc = doc_store.get_source_document(document_id)

        if not doc:
            raise ValueError(f"Document {document_id} not found")

        result = {
            "id": doc["id"],
            "filename": doc["filename"],
            "content": doc["content"],
            "file_type": doc["file_type"],
            "file_size": doc["file_size"],
            "metadata": doc["metadata"],
            "created_at": doc["created_at"].isoformat(),
            "updated_at": doc["updated_at"].isoformat(),
            # Collections this document belongs to
            "collections": doc.get("collections", []),
            # Evaluation fields
            "reviewed_by_human": doc.get("reviewed_by_human", False),
            "quality_score": doc.get("quality_score"),
            "quality_summary": doc.get("quality_summary"),
            "topic_relevance_score": doc.get("topic_relevance_score"),
            "topic_relevance_summary": doc.get("topic_relevance_summary"),
            "topic_provided": doc.get("topic_provided"),
            "eval_model": doc.get("eval_model"),
            "eval_timestamp": doc["eval_timestamp"].isoformat() if doc.get("eval_timestamp") else None,
        }

        if include_chunks:
            chunks = doc_store.get_document_chunks(document_id)
            result["chunks"] = [
                {
                    "chunk_id": c["id"],
                    "chunk_index": c["chunk_index"],
                    "content": c["content"],
                    "char_start": c["char_start"],
                    "char_end": c["char_end"],
                }
                for c in chunks
            ]

        return result
    except Exception as e:
        logger.error(f"get_document_by_id failed: {e}")
        raise


def get_collection_info_impl(
    db: Database, coll_mgr: CollectionManager, collection_name: str
) -> Dict[str, Any]:
    """Implementation of get_collection_info tool."""
    try:
        collection = coll_mgr.get_collection(collection_name)

        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")

        # Get chunk count
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(DISTINCT dc.id)
                FROM document_chunks dc
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                WHERE cc.collection_id = %s
                """,
                (collection["id"],),
            )
            chunk_count = cur.fetchone()[0]

            # Get sample documents
            cur.execute(
                """
                SELECT DISTINCT sd.filename
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                WHERE cc.collection_id = %s
                LIMIT 5
                """,
                (collection["id"],),
            )
            sample_docs = [row[0] for row in cur.fetchall()]

            # Get crawl history (web pages with crawl_root_url metadata)
            cur.execute(
                """
                SELECT DISTINCT
                    sd.metadata->>'crawl_root_url' as crawl_url,
                    sd.metadata->>'crawl_timestamp' as crawl_time,
                    COUNT(DISTINCT sd.id) as page_count,
                    COUNT(DISTINCT dc.id) as chunk_count
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                WHERE cc.collection_id = %s
                  AND sd.metadata->>'crawl_root_url' IS NOT NULL
                GROUP BY sd.metadata->>'crawl_root_url', sd.metadata->>'crawl_timestamp'
                ORDER BY sd.metadata->>'crawl_timestamp' DESC
                LIMIT 10
                """,
                (collection["id"],),
            )
            crawled_urls = [
                {
                    "url": row[0],
                    "timestamp": row[1],
                    "page_count": row[2],
                    "chunk_count": row[3],
                }
                for row in cur.fetchall()
            ]

        # Extract domain and domain_scope from metadata_schema
        # Note: Database stores as metadata_schema.mandatory.domain (direct string values)
        # NOT as mandatory_fields - that's only in get_collection_metadata_schema_impl response
        metadata_schema = collection.get("metadata_schema", {})
        mandatory = metadata_schema.get("mandatory", {})  # Correct key for database structure

        # Extract values directly (stored as strings, not nested dicts)
        domain = mandatory.get("domain")
        domain_scope = mandatory.get("domain_scope")

        return {
            "name": collection["name"],
            "description": collection["description"] or "",
            "document_count": collection.get("document_count", 0),
            "chunk_count": chunk_count,
            "created_at": collection["created_at"].isoformat(),
            "sample_documents": sample_docs,
            "crawled_urls": crawled_urls,
            "domain": domain,
            "domain_scope": domain_scope,
        }
    except Exception as e:
        logger.error(f"get_collection_info failed: {e}")
        raise


async def analyze_website_impl(
    base_url: str,
    timeout: int = 10,
    include_url_lists: bool = False,
    max_urls_per_pattern: int = 10
) -> Dict[str, Any]:
    """
    Implementation of analyze_website tool.

    Discovers URL patterns for a website from public sources.
    Includes 50-second hard timeout with graceful error handling.

    GUARANTEED to return structured response in ALL scenarios:
    - Success: URL patterns and statistics
    - Timeout: Informative message about site size
    - Error: Description of what went wrong
    - Tool unavailable: Setup instructions

    NO recommendations or heuristics - just facts for AI agent to reason about.

    By default, returns only pattern_stats summary (lightweight). Agent can request
    full URL lists if needed by setting include_url_lists=True.

    Args:
        base_url: The website URL to analyze (root domain or specific path)
        timeout: DEPRECATED - kept for backward compatibility, ignored
                (actual timeout is 50 seconds, hard-coded for reliability)
        include_url_lists: If True, includes full URL lists per pattern
        max_urls_per_pattern: Max URLs per pattern when include_url_lists=True

    Returns:
        Dictionary with analysis results. ALWAYS includes:
        - base_url: Input URL
        - status: "asyncurlseeder", "timeout", "error", or "not_available"
        - total_urls: Number of URLs discovered (0 on error)
        - pattern_stats: Dictionary of URL patterns (empty on error)
        - notes: Informative message describing results or error
        - elapsed_seconds: Time taken for analysis

        May include (on success):
        - url_groups: Full URL lists per pattern if include_url_lists=True
        - domains: List of domains found in results
        - url_patterns: Number of URL pattern groups found
    """
    try:
        # Call the async analyzer (ignoring deprecated timeout parameter)
        result = await analyze_website_async(
            base_url=base_url,
            include_url_lists=include_url_lists,
            max_urls_per_pattern=max_urls_per_pattern
        )
        return result
    except Exception as e:
        # Fallback error response (should not happen, analyzer handles all errors internally)
        logger.error(f"Unexpected error in analyze_website_impl: {e}")
        return {
            "base_url": base_url,
            "status": "error",
            "error": "unexpected",
            "total_urls": 0,
            "pattern_stats": {},
            "notes": f"Unexpected error during analysis: {str(e)}",
            "elapsed_seconds": 0,
        }


def check_existing_crawl(
    db: Database, url: str, collection_name: str
) -> Optional[Dict[str, Any]]:
    """
    Check if a URL has already been crawled into a collection.

    Args:
        db: Database connection
        url: The crawl root URL to check
        collection_name: The collection name to check

    Returns:
        Dict with crawl info if found, None otherwise
    """
    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sd.metadata->>'crawl_session_id' as session_id,
                    sd.metadata->>'crawl_timestamp' as timestamp,
                    COUNT(DISTINCT sd.id) as page_count,
                    COUNT(DISTINCT dc.id) as chunk_count
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.metadata->>'crawl_root_url' = %s
                  AND c.name = %s
                GROUP BY sd.metadata->>'crawl_session_id', sd.metadata->>'crawl_timestamp'
                ORDER BY sd.metadata->>'crawl_timestamp' DESC
                LIMIT 1
                """,
                (url, collection_name),
            )
            row = cur.fetchone()

            if row:
                return {
                    "crawl_session_id": row[0],
                    "crawl_timestamp": row[1],
                    "page_count": row[2],
                    "chunk_count": row[3],
                }
            return None
    except Exception as e:
        logger.error(f"check_existing_crawl failed: {e}")
        raise


def check_existing_file(
    db: Database, file_path: str, collection_name: str
) -> Optional[Dict[str, Any]]:
    """
    Check if a file path has already been ingested into a collection.

    Args:
        db: Database connection
        file_path: Absolute file path to check
        collection_name: Collection name to check within

    Returns:
        Dict with doc info if found, None otherwise
    """
    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    sd.id as doc_id,
                    sd.filename,
                    sd.created_at
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.metadata->>'file_path' = %s
                  AND c.name = %s
                LIMIT 1
                """,
                (file_path, collection_name),
            )
            row = cur.fetchone()

            if row:
                return {
                    "doc_id": row[0],
                    "filename": row[1],
                    "created_at": row[2].isoformat() if row[2] else None,
                }
            return None
    except Exception as e:
        logger.error(f"check_existing_file failed: {e}")
        raise


def check_existing_files_batch(
    db: Database, file_paths: List[str], collection_name: str
) -> List[Dict[str, Any]]:
    """
    Check if multiple file paths have already been ingested into a collection.

    Args:
        db: Database connection
        file_paths: List of absolute file paths to check
        collection_name: Collection name to check within

    Returns:
        List of existing documents (empty list if none found)
    """
    if not file_paths:
        return []

    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    sd.id as doc_id,
                    sd.filename,
                    sd.metadata->>'file_path' as file_path
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.metadata->>'file_path' = ANY(%s)
                  AND c.name = %s
                """,
                (file_paths, collection_name),
            )
            return [
                {
                    "doc_id": row[0],
                    "filename": row[1],
                    "file_path": row[2],
                }
                for row in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"check_existing_files_batch failed: {e}")
        raise


def check_existing_title(
    db: Database, title: str, collection_name: str
) -> Optional[Dict[str, Any]]:
    """
    Check if a document title has already been ingested into a collection.

    Args:
        db: Database connection
        title: Document title to check (stored in filename field)
        collection_name: Collection name to check within

    Returns:
        Dict with doc info if found, None otherwise
    """
    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    sd.id as doc_id,
                    sd.filename,
                    sd.created_at
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.filename = %s
                  AND c.name = %s
                LIMIT 1
                """,
                (title, collection_name),
            )
            row = cur.fetchone()

            if row:
                return {
                    "doc_id": row[0],
                    "filename": row[1],
                    "created_at": row[2].isoformat() if row[2] else None,
                }
            return None
    except Exception as e:
        logger.error(f"check_existing_title failed: {e}")
        raise


# ============================================================================
# Content Hash Duplicate Detection
# ============================================================================


def compute_content_hash(content: str) -> str:
    """
    Compute SHA256 hash of content for duplicate detection.

    Args:
        content: Text content to hash

    Returns:
        64-character hex string (SHA256 hash)
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def check_duplicate_by_hash(
    db: Database, content_hash: str, collection_name: str
) -> Optional[Dict[str, Any]]:
    """
    Find existing document with same content hash in a collection.

    This is the primary duplicate detection method for non-URL ingests.
    Same content hash = same content = duplicate.

    Args:
        db: Database connection
        content_hash: SHA256 hash of content
        collection_name: Collection to check within

    Returns:
        Dict with full document info if found (for smart update), None otherwise.
        Includes all fields needed to decide what to update vs keep.
    """
    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    sd.id as doc_id,
                    sd.filename,
                    sd.metadata,
                    sd.topic_provided,
                    sd.quality_score,
                    sd.quality_summary,
                    sd.topic_relevance_score,
                    sd.topic_relevance_summary,
                    sd.reviewed_by_human,
                    sd.eval_model,
                    sd.eval_timestamp,
                    sd.created_at
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.content_hash = %s
                  AND c.name = %s
                LIMIT 1
                """,
                (content_hash, collection_name),
            )
            row = cur.fetchone()

            if row:
                return {
                    "doc_id": row[0],
                    "filename": row[1],
                    "metadata": row[2] or {},
                    "topic_provided": row[3],
                    "quality_score": float(row[4]) if row[4] is not None else None,
                    "quality_summary": row[5],
                    "topic_relevance_score": float(row[6]) if row[6] is not None else None,
                    "topic_relevance_summary": row[7],
                    "reviewed_by_human": row[8] or False,
                    "eval_model": row[9],
                    "eval_timestamp": row[10],
                    "created_at": row[11].isoformat() if row[11] else None,
                }
            return None
    except Exception as e:
        logger.error(f"check_duplicate_by_hash failed: {e}")
        raise


def check_duplicate_by_hash_global(
    db: Database, content_hash: str
) -> Optional[Dict[str, Any]]:
    """
    Find existing document with same content hash in ANY collection (global check).

    Unlike check_duplicate_by_hash(), this searches across ALL collections.
    Used to enforce single-source-of-truth: same content should not exist
    in multiple collections as separate documents.

    Args:
        db: Database connection
        content_hash: SHA256 hash of content

    Returns:
        Dict with document info INCLUDING which collection(s) it belongs to,
        or None if content doesn't exist anywhere.
    """
    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    sd.id as doc_id,
                    sd.filename,
                    sd.metadata,
                    sd.topic_provided,
                    sd.quality_score,
                    sd.quality_summary,
                    sd.topic_relevance_score,
                    sd.topic_relevance_summary,
                    sd.reviewed_by_human,
                    sd.eval_model,
                    sd.eval_timestamp,
                    sd.created_at,
                    array_agg(DISTINCT c.name) as collections
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.content_hash = %s
                GROUP BY sd.id, sd.filename, sd.metadata, sd.topic_provided,
                         sd.quality_score, sd.quality_summary, sd.topic_relevance_score,
                         sd.topic_relevance_summary, sd.reviewed_by_human,
                         sd.eval_model, sd.eval_timestamp, sd.created_at
                LIMIT 1
                """,
                (content_hash,),
            )
            row = cur.fetchone()

            if row:
                return {
                    "doc_id": row[0],
                    "filename": row[1],
                    "metadata": row[2] or {},
                    "topic_provided": row[3],
                    "quality_score": float(row[4]) if row[4] is not None else None,
                    "quality_summary": row[5],
                    "topic_relevance_score": float(row[6]) if row[6] is not None else None,
                    "topic_relevance_summary": row[7],
                    "reviewed_by_human": row[8] or False,
                    "eval_model": row[9],
                    "eval_timestamp": row[10],
                    "created_at": row[11].isoformat() if row[11] else None,
                    "collections": row[12] or [],  # List of collection names
                }
            return None
    except Exception as e:
        logger.error(f"check_duplicate_by_hash_global failed: {e}")
        raise


def check_duplicates_by_hash_batch(
    db: Database, content_hashes: List[str], collection_name: str
) -> Dict[str, Dict[str, Any]]:
    """
    Check multiple content hashes for duplicates in a single query.

    Used by directory ingestion for efficient batch checking.

    Args:
        db: Database connection
        content_hashes: List of SHA256 hashes to check
        collection_name: Collection to check within

    Returns:
        Dict mapping content_hash -> document info for existing documents.
        Missing hashes are not in the dict (= new content).
    """
    if not content_hashes:
        return {}

    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    sd.content_hash,
                    sd.id as doc_id,
                    sd.filename,
                    sd.metadata,
                    sd.topic_provided,
                    sd.quality_score,
                    sd.quality_summary,
                    sd.topic_relevance_score,
                    sd.topic_relevance_summary,
                    sd.reviewed_by_human,
                    sd.eval_model,
                    sd.eval_timestamp,
                    sd.created_at
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.content_hash = ANY(%s)
                  AND c.name = %s
                """,
                (content_hashes, collection_name),
            )
            results = {}
            for row in cur.fetchall():
                results[row[0]] = {
                    "doc_id": row[1],
                    "filename": row[2],
                    "metadata": row[3] or {},
                    "topic_provided": row[4],
                    "quality_score": float(row[5]) if row[5] is not None else None,
                    "quality_summary": row[6],
                    "topic_relevance_score": float(row[7]) if row[7] is not None else None,
                    "topic_relevance_summary": row[8],
                    "reviewed_by_human": row[9] or False,
                    "eval_model": row[10],
                    "eval_timestamp": row[11],
                    "created_at": row[12].isoformat() if row[12] else None,
                }
            return results
    except Exception as e:
        logger.error(f"check_duplicates_by_hash_batch failed: {e}")
        raise


def check_duplicates_by_hash_batch_global(
    db: Database, content_hashes: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Check multiple content hashes for duplicates across ALL collections (global check).

    Unlike check_duplicates_by_hash_batch(), this searches all collections
    and returns which collection(s) each document belongs to.

    Args:
        db: Database connection
        content_hashes: List of SHA256 hashes to check

    Returns:
        Dict mapping content_hash -> document info INCLUDING collections list.
        Missing hashes are not in the dict (= new content).
    """
    if not content_hashes:
        return {}

    try:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sd.content_hash,
                    sd.id as doc_id,
                    sd.filename,
                    sd.metadata,
                    sd.topic_provided,
                    sd.quality_score,
                    sd.quality_summary,
                    sd.topic_relevance_score,
                    sd.topic_relevance_summary,
                    sd.reviewed_by_human,
                    sd.eval_model,
                    sd.eval_timestamp,
                    sd.created_at,
                    array_agg(DISTINCT c.name) as collections
                FROM source_documents sd
                JOIN document_chunks dc ON dc.source_document_id = sd.id
                JOIN chunk_collections cc ON cc.chunk_id = dc.id
                JOIN collections c ON c.id = cc.collection_id
                WHERE sd.content_hash = ANY(%s)
                GROUP BY sd.content_hash, sd.id, sd.filename, sd.metadata, sd.topic_provided,
                         sd.quality_score, sd.quality_summary, sd.topic_relevance_score,
                         sd.topic_relevance_summary, sd.reviewed_by_human,
                         sd.eval_model, sd.eval_timestamp, sd.created_at
                """,
                (content_hashes,),
            )
            results = {}
            for row in cur.fetchall():
                results[row[0]] = {
                    "doc_id": row[1],
                    "filename": row[2],
                    "metadata": row[3] or {},
                    "topic_provided": row[4],
                    "quality_score": float(row[5]) if row[5] is not None else None,
                    "quality_summary": row[6],
                    "topic_relevance_score": float(row[7]) if row[7] is not None else None,
                    "topic_relevance_summary": row[8],
                    "reviewed_by_human": row[9] or False,
                    "eval_model": row[10],
                    "eval_timestamp": row[11],
                    "created_at": row[12].isoformat() if row[12] else None,
                    "collections": row[13] or [],  # List of collection names
                }
            return results
    except Exception as e:
        logger.error(f"check_duplicates_by_hash_batch_global failed: {e}")
        raise


def update_document_metadata_only(
    db: Database,
    doc_id: int,
    metadata: Optional[Dict[str, Any]] = None,
    filename: Optional[str] = None,
    reviewed_by_human: Optional[bool] = None,
    topic_provided: Optional[str] = None,
    quality_score: Optional[float] = None,
    quality_summary: Optional[str] = None,
    topic_relevance_score: Optional[float] = None,
    topic_relevance_summary: Optional[str] = None,
    eval_model: Optional[str] = None,
    eval_timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Update document metadata and evaluation fields WITHOUT re-embedding or re-graphing.

    Used when content hash matches - no need to reprocess content, just update metadata.
    This is much more efficient than full re-ingestion.

    IMPORTANT: The metadata parameter REPLACES existing metadata entirely (does not merge).
    If you want to merge with existing metadata, do so BEFORE calling this function:
        merged = {**(existing.get("metadata") or {}), **new_metadata}
        update_document_metadata_only(db, doc_id, metadata=merged, ...)

    Args:
        db: Database connection
        doc_id: Document ID to update
        metadata: New metadata (REPLACES existing entirely - see note above)
        filename: New filename/title
        reviewed_by_human: New review status (only if explicitly provided)
        topic_provided: Topic used for evaluation
        quality_score: LLM quality score
        quality_summary: LLM quality explanation
        topic_relevance_score: LLM topic relevance score
        topic_relevance_summary: LLM topic relevance explanation
        eval_model: Model used for evaluation
        eval_timestamp: When evaluation was performed

    Returns:
        Dict with update results: {"document_id": X, "updated_fields": [...]}
    """
    from psycopg.types.json import Jsonb

    conn = db.connect()
    updated_fields = []

    # Build dynamic UPDATE query based on what's provided
    set_clauses = ["updated_at = CURRENT_TIMESTAMP"]
    params = []

    if metadata is not None:
        set_clauses.append("metadata = %s")
        params.append(Jsonb(metadata))
        updated_fields.append("metadata")

    if filename is not None:
        set_clauses.append("filename = %s")
        params.append(filename)
        updated_fields.append("filename")

    if reviewed_by_human is not None:
        set_clauses.append("reviewed_by_human = %s")
        params.append(reviewed_by_human)
        updated_fields.append("reviewed_by_human")

    if topic_provided is not None:
        set_clauses.append("topic_provided = %s")
        params.append(topic_provided)
        updated_fields.append("topic_provided")

    if quality_score is not None:
        set_clauses.append("quality_score = %s")
        params.append(quality_score)
        updated_fields.append("quality_score")

    if quality_summary is not None:
        set_clauses.append("quality_summary = %s")
        params.append(quality_summary)
        updated_fields.append("quality_summary")

    if topic_relevance_score is not None:
        set_clauses.append("topic_relevance_score = %s")
        params.append(topic_relevance_score)
        updated_fields.append("topic_relevance_score")

    if topic_relevance_summary is not None:
        set_clauses.append("topic_relevance_summary = %s")
        params.append(topic_relevance_summary)
        updated_fields.append("topic_relevance_summary")

    if eval_model is not None:
        set_clauses.append("eval_model = %s")
        params.append(eval_model)
        updated_fields.append("eval_model")

    if eval_timestamp is not None:
        set_clauses.append("eval_timestamp = %s")
        params.append(eval_timestamp)
        updated_fields.append("eval_timestamp")

    # Add doc_id for WHERE clause
    params.append(doc_id)

    query = f"""
        UPDATE source_documents
        SET {', '.join(set_clauses)}
        WHERE id = %s
    """

    with conn.cursor() as cur:
        cur.execute(query, params)

    updated_fields.append("updated_at")  # Always updated
    logger.info(f"✅ Updated document {doc_id} metadata: {updated_fields}")

    return {
        "document_id": doc_id,
        "updated_fields": updated_fields,
    }


async def delete_document_for_reingest(
    doc_id: int,
    doc_store: DocumentStore,
    graph_store: Optional[GraphStore],
    filename: str = "",
) -> None:
    """
    Centralized deletion logic for reingest operations across ALL ingest tools.

    Deletes document from both Knowledge Graph and RAG store with proper error handling.
    If ANY deletion step fails, raises exception to abort reingest.

    This function ensures:
    1. Graph episode is deleted (all entities, relationships, edges)
    2. RAG document is deleted (all chunks, embeddings, metadata, collection links via CASCADE)
    3. Deletion is verified before proceeding
    4. Any failure aborts reingest to prevent data corruption

    Args:
        doc_id: Document ID to delete
        doc_store: DocumentStore instance
        graph_store: GraphStore instance (required for deletion)
        filename: Document filename (for logging)

    Raises:
        Exception: If graph deletion fails, RAG deletion fails, or verification fails
    """
    try:
        # STEP 1: Delete from Knowledge Graph
        if graph_store:
            episode_name = f"doc_{doc_id}"
            logger.info(f"🗑️  Deleting Graph episode '{episode_name}' for document {doc_id} ({filename})")

            deleted = await graph_store.delete_episode_by_name(episode_name)
            if not deleted:
                logger.warning(f"⚠️  Graph episode '{episode_name}' not found (may not have been indexed)")
                # Don't fail if episode doesn't exist - document may not have been graphed yet
            else:
                logger.info(f"✅ Graph episode '{episode_name}' deleted successfully")
        else:
            logger.warning(f"⚠️  No graph_store provided - skipping graph deletion for doc {doc_id}")

        # STEP 2: Delete from RAG store (includes chunks, embeddings, metadata, collection links)
        logger.info(f"🗑️  Deleting RAG document {doc_id} ({filename})")

        delete_result = await doc_store.delete_document(doc_id, graph_store=None)  # Graph already deleted above

        logger.info(
            f"✅ Deleted document {doc_id}: "
            f"{delete_result['chunks_deleted']} chunks, "
            f"collections: {delete_result['collections_affected']}"
        )

        # STEP 3: Verify deletion succeeded
        verify_doc = doc_store.get_source_document(doc_id)
        if verify_doc is not None:
            raise Exception(
                f"CRITICAL: Document {doc_id} still exists after deletion! "
                f"Aborting reingest to prevent corruption."
            )

        logger.info(f"✅ Verified document {doc_id} completely removed")

    except Exception as e:
        logger.error(
            f"❌ DELETION FAILED for document {doc_id} ({filename}): {e}\n"
            f"ABORTING REINGEST to prevent data corruption."
        )
        raise  # Re-raise to abort reingest operation


@handle_database_errors_async("URL ingestion")
@deduplicate_request()
async def ingest_url_impl(
    db: Database,
    doc_store: DocumentStore,
    unified_mediator,
    graph_store: Optional[GraphStore],
    url: str,
    collection_name: str,
    follow_links: bool = False,
    max_pages: int = 10,
    mode: str = "ingest",
    metadata: Optional[Dict[str, Any]] = None,
    include_document_ids: bool = False,
    progress_callback=None,
    dry_run: bool = False,
    topic: str | None = None,
    # Evaluation parameters
    reviewed_by_human: bool = False,
    # Audit parameters
    actor_type: str = "agent",
) -> Dict[str, Any]:
    """
    Implementation of ingest_url tool with mode support and dry_run option.

    Routes through unified mediator to update both RAG and Knowledge Graph.
    Performs health checks on both databases before ingestion (Option B: Mandatory).

    Args:
        follow_links: If True, follows internal links for multi-page crawl
        max_pages: Maximum pages to crawl when follow_links=True (default=10, max=20)
        mode: "ingest" (new ingest, error if exists) or "reingest" (update existing)
        progress_callback: Optional async callback for MCP progress notifications
        dry_run: If True, crawls pages but doesn't ingest. Returns relevance scores.
        topic: Optional topic for relevance scoring (Mode A vs Mode B). Required for dry_run.
        reviewed_by_human: Set to True ONLY when user explicitly confirmed review
    """
    try:
        # Progress: Starting
        if progress_callback:
            await progress_callback(0, 100, "Starting URL ingest...")

        # ============================================================================
        # COMPREHENSIVE PARAMETER VALIDATION
        # ============================================================================

        # Validate max_pages range
        if max_pages < 1:
            raise ValueError(
                f"Invalid max_pages={max_pages}. Must be >= 1."
            )
        if max_pages > 20:
            raise ValueError(
                f"Invalid max_pages={max_pages}. Maximum allowed is 20. "
                f"For large sites, run analyze_website() to plan multiple targeted crawls."
            )

        # Validate dry_run parameters
        if dry_run and not topic:
            raise ValueError(
                "When dry_run=True, you must provide a 'topic' parameter. "
                "The topic describes what content you're looking for "
                "(e.g., 'LCEL pipelines in LangChain')."
            )

        # ========================================================================
        # DRY RUN MODE: Crawl and score without ingesting
        # ========================================================================
        if dry_run:
            if progress_callback:
                await progress_callback(0, 100, f"Dry run: Crawling {url}...")

            # Crawl pages (same as normal mode) with comprehensive error handling
            try:
                if follow_links:
                    crawler = WebCrawler(headless=True, verbose=False)
                    results = await crawler.crawl_with_depth(url, max_depth=1, max_pages=max_pages)
                else:
                    result = await crawl_single_page(url, headless=True, verbose=False)
                    results = [result]  # Include even failed results for reporting
            except Exception as e:
                # Catastrophic crawler failure (timeout, network error, etc.)
                logger.error(f"Crawler exception during dry run: {e}")
                error_msg = str(e)
                # Clean up common error patterns for user-friendly display
                if "Timeout" in error_msg or "timeout" in error_msg:
                    user_friendly_error = "❌ Page navigation timeout - website not responding or blocking access"
                elif "ConnectionRefusedError" in error_msg or "Connection refused" in error_msg:
                    user_friendly_error = "❌ Connection refused - website may be down or unreachable"
                elif "SSLError" in error_msg or "SSL" in error_msg:
                    user_friendly_error = "❌ SSL certificate error - website has certificate issues"
                else:
                    user_friendly_error = f"❌ Failed to access website: {error_msg[:100]}"

                return {
                    "dry_run": True,
                    "status": "failed",
                    "topic": topic,
                    "url": url,
                    "pages_crawled": 0,
                    "pages_recommended": 0,
                    "pages_to_review": 0,
                    "pages_to_skip": 0,
                    "pages_failed": 1,
                    "collection_name": collection_name,
                    "pages": [{
                        "url": url,
                        "title": url,
                        "status_code": None,
                        "relevance_score": None,
                        "relevance_summary": None,
                        "recommendation": "skip",
                        "reason": user_friendly_error,
                    }],
                    "error_summary": user_friendly_error,
                }

            # Separate pages by crawl success (not HTTP status code)
            # Crawl4AI reports initial HTTP status even after following redirects,
            # so we check result.success instead to determine if content was retrieved
            pages_to_score = []
            http_failed_pages = []

            for result in results:
                # Check if crawl succeeded (has content to process)
                if result.success and result.content:
                    # Crawl succeeded - add to scoring queue regardless of initial HTTP status
                    # (Crawl4AI reports initial status code even after successful redirect)
                    pages_to_score.append({
                        "url": result.url,
                        "title": result.metadata.get("title", result.url),
                        "content": result.content,
                        "status_code": result.status_code,
                    })
                else:
                    # Crawl failed - determine reason
                    if result.error:
                        reason = f"Crawl error: {result.error.error_message}"
                    elif not result.is_http_success():
                        reason = result.get_http_error_reason() or "HTTP error"
                    else:
                        reason = "No content retrieved"

                    http_failed_pages.append({
                        "url": result.url,
                        "title": result.metadata.get("title", result.url) if result.metadata else result.url,
                        "status_code": result.status_code,
                        "relevance_score": None,
                        "relevance_summary": None,
                        "recommendation": "skip",
                        "reason": reason,
                    })

            if progress_callback:
                score_msg = f"Scoring {len(pages_to_score)} pages for relevance to: {topic}"
                if http_failed_pages:
                    score_msg += f" ({len(http_failed_pages)} pages failed with HTTP errors)"
                await progress_callback(50, 100, score_msg)

            # Score relevance for successful pages only (with LLM failure handling)
            scored_pages = []
            if pages_to_score:
                try:
                    scored_results = await score_page_relevance(pages_to_score, topic)
                    # Add status_code to scored results
                    for scored, original in zip(scored_results, pages_to_score):
                        scored["status_code"] = original["status_code"]
                        scored_pages.append(scored)
                except Exception as e:
                    # LLM scoring failed - mark all pages as "review" (user must decide)
                    logger.error(f"LLM relevance scoring failed: {e}")
                    for page_data in pages_to_score:
                        scored_pages.append({
                            "url": page_data["url"],
                            "title": page_data["title"],
                            "status_code": page_data["status_code"],
                            "relevance_score": None,
                            "relevance_summary": f"⚠️ Automatic scoring unavailable - please review manually",
                            "recommendation": "review",
                        })

            # Combine scored pages with HTTP-failed pages
            all_pages = scored_pages + http_failed_pages

            if progress_callback:
                await progress_callback(100, 100, "Dry run complete!")

            # Calculate summary stats with three-tier system
            ingest_count = sum(1 for p in all_pages if p["recommendation"] == "ingest")
            review_count = sum(1 for p in all_pages if p["recommendation"] == "review")
            skip_count = sum(1 for p in all_pages if p["recommendation"] == "skip")
            http_error_count = len(http_failed_pages)

            # Determine overall status
            if ingest_count > 0:
                status = "success"
                error_summary = None
            elif review_count > 0:
                status = "review"
                error_summary = "⚠️ No highly relevant pages found - content needs manual review"
            else:
                status = "failed"
                error_summary = "❌ No relevant content found - all pages failed validation or are not relevant"

            return {
                "dry_run": True,
                "status": status,
                "topic": topic,
                "url": url,
                "pages_crawled": len(results),
                "pages_recommended": ingest_count,
                "pages_to_review": review_count,
                "pages_to_skip": skip_count,
                "pages_failed": http_error_count,
                "collection_name": collection_name,
                "pages": all_pages,
                "error_summary": error_summary,
            }

        # Health check: both PostgreSQL and Neo4j must be reachable
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return health_error

        # Validate mode (centralized) - ingest_url validates mode before collection
        validate_mode(mode)

        # Validate collection exists (centralized)
        validate_collection_exists(doc_store, collection_name)

        # Check for existing crawl
        existing_crawl = check_existing_crawl(db, url, collection_name)

        if mode == "ingest" and existing_crawl:
            raise ValueError(
                f"This URL has already been ingested into collection '{collection_name}'.\n"
                f"Existing ingest: {existing_crawl['page_count']} pages, "
                f"{existing_crawl['chunk_count']} chunks, "
                f"timestamp: {existing_crawl['crawl_timestamp']}\n"
                f"To overwrite existing content, use mode='reingest'."
            )

        # If reingest mode, delete old documents first
        old_pages_deleted = 0
        if mode == "reingest" and existing_crawl:
            if progress_callback:
                await progress_callback(5, 100, f"Deleting {existing_crawl['page_count']} old pages...")

            conn = db.connect()
            with conn.cursor() as cur:
                # Find all documents with matching crawl_root_url IN THIS COLLECTION ONLY
                cur.execute(
                    """
                    SELECT DISTINCT sd.id, sd.filename
                    FROM source_documents sd
                    JOIN document_chunks dc ON dc.source_document_id = sd.id
                    JOIN chunk_collections cc ON cc.chunk_id = dc.id
                    JOIN collections c ON c.id = cc.collection_id
                    WHERE sd.metadata->>'crawl_root_url' = %s
                      AND c.name = %s
                    """,
                    (url, collection_name),
                )
                existing_docs = cur.fetchall()

                old_pages_deleted = len(existing_docs)

                # Delete all old documents using centralized deletion with error handling
                logger.info(f"🗑️  Deleting {old_pages_deleted} old documents for reingest of {url}")
                for doc_id, filename in existing_docs:
                    await delete_document_for_reingest(
                        doc_id=doc_id,
                        doc_store=doc_store,
                        graph_store=graph_store,
                        filename=filename
                    )

        # Progress: Crawling web pages
        if progress_callback:
            crawl_msg = f"Crawling {url}" + (f" (max {max_pages} pages)" if follow_links else "")
            await progress_callback(10, 100, crawl_msg)

        # Crawl web pages
        if follow_links:
            crawler = WebCrawler(headless=True, verbose=False)
            # Use max_depth=1 (fixed depth) for sequential crawling with rate limiting
            results = await crawler.crawl_with_depth(url, max_depth=1, max_pages=max_pages)

            # Log if we hit the max_pages limit (crawler stopped early)
            if len(results) == max_pages:
                logger.info(
                    f"Crawl reached max_pages limit ({max_pages}). "
                    f"Consider multiple targeted crawls for complete coverage."
                )
        else:
            result = await crawl_single_page(url, headless=True, verbose=False)
            results = [result]  # Include all results for proper reporting

        # Progress: Web crawl complete, starting ingestion
        if progress_callback:
            await progress_callback(20, 100, f"Web crawl complete ({len(results)} pages), starting ingestion...")

        # Get collection description for evaluation (once, before loop)
        collection = doc_store.collection_mgr.get_collection(collection_name)
        collection_description = collection.get("description", "") if collection else ""

        # Import evaluation function
        from src.mcp.evaluation import evaluate_content

        # Ingest each page (route through unified mediator if available)
        document_ids = []
        total_chunks = 0
        total_entities = 0
        successful_ingests = 0
        pages_failed = []  # Track failed pages with reasons

        # Track evaluation stats for aggregate summary
        quality_scores = []
        topic_relevance_scores = []

        for idx, result in enumerate(results):
            # Check if crawl succeeded (has content to ingest)
            # Crawl4AI reports initial HTTP status even after following redirects,
            # so we check result.success instead to determine if content was retrieved
            if not result.success or not result.content:
                # Crawl failed - determine reason
                if result.error:
                    reason = f"Crawl error: {result.error.error_message}"
                elif not result.is_http_success():
                    reason = result.get_http_error_reason() or "HTTP error"
                else:
                    reason = "No content retrieved"

                pages_failed.append({
                    "url": result.url,
                    "status_code": result.status_code,
                    "reason": reason,
                })
                logger.warning(f"Skipping page {result.url}: {reason} (status={result.status_code})")
                continue

            # Progress: Per-page ingestion (20% to 90%)
            if progress_callback:
                page_progress = 20 + int((idx / len(results)) * 70)
                await progress_callback(
                    page_progress,
                    100,
                    f"Ingesting page {idx + 1}/{len(results)}: {result.metadata.get('title', result.url)[:50]}..."
                )

            try:
                page_title = result.metadata.get("title", result.url)

                # Merge user metadata with page metadata
                page_metadata = metadata.copy() if metadata else {}
                page_metadata.update(result.metadata)

                # Run LLM evaluation (advisory only, never blocks ingestion)
                eval_result = await evaluate_content(
                    content=result.content,
                    collection_name=collection_name,
                    collection_description=collection_description,
                    topic=topic,
                )

                # Track evaluation stats
                quality_scores.append(eval_result.quality_score)
                if topic and eval_result.topic_relevance_score is not None:
                    topic_relevance_scores.append(eval_result.topic_relevance_score)

                logger.info(f"Ingesting page through unified mediator: {page_title}")
                # Note: Don't pass progress_callback here - would conflict with parent progress
                ingest_result = await unified_mediator.ingest_text(
                    content=result.content,
                    collection_name=collection_name,
                    document_title=page_title,
                    metadata=page_metadata,
                    progress_callback=None,  # Skip nested progress for multi-page crawls
                    # Pass evaluation fields
                    reviewed_by_human=reviewed_by_human,
                    quality_score=eval_result.quality_score,
                    quality_summary=eval_result.quality_summary,
                    topic_relevance_score=eval_result.topic_relevance_score,
                    topic_relevance_summary=eval_result.topic_relevance_summary,
                    topic_provided=eval_result.topic_provided,
                    eval_model=eval_result.model,
                    eval_timestamp=eval_result.timestamp,
                )
                document_ids.append(ingest_result["source_document_id"])
                total_chunks += ingest_result["num_chunks"]
                total_entities += ingest_result.get("entities_extracted", 0)
                successful_ingests += 1

                # Audit logging for each ingested page
                create_audit_entry(
                    db=db,
                    source_document_id=ingest_result["source_document_id"],
                    actor_type=actor_type,
                    ingest_method="url",
                    collection_name=collection_name,
                    source_url=result.url,
                    metadata={
                        "page_title": page_title,
                        "crawl_root_url": url,
                        "content_length": len(result.content),
                        "quality_score": eval_result.quality_score,
                    },
                )

            except Exception as e:
                pages_failed.append({
                    "url": result.url,
                    "status_code": result.status_code,
                    "reason": f"Ingestion error: {str(e)}",
                })
                logger.warning(f"Failed to ingest page {result.url}: {e}")

        response = {
            "mode": mode,
            "pages_crawled": len(results),  # Total pages attempted
            "pages_ingested": successful_ingests,
            "total_chunks": total_chunks,
            "collection_name": collection_name,
            "entities_extracted": total_entities,
            "crawl_metadata": {
                "crawl_root_url": url,
                "crawl_session_id": (
                    results[0].metadata.get("crawl_session_id") if results and results[0].metadata else None
                ),
                "crawl_timestamp": datetime.now().isoformat(),
            },
        }

        # Include pages_failed if any pages failed
        if pages_failed:
            response["pages_failed"] = pages_failed

        if mode == "reingest":
            response["old_pages_deleted"] = old_pages_deleted

        if include_document_ids:
            response["document_ids"] = document_ids

        # Add aggregate evaluation summary
        if quality_scores:
            evaluation_summary = {
                "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 3),
                "min_quality_score": round(min(quality_scores), 3),
                "max_quality_score": round(max(quality_scores), 3),
            }
            if topic and topic_relevance_scores:
                evaluation_summary["avg_topic_relevance"] = round(sum(topic_relevance_scores) / len(topic_relevance_scores), 3)
                evaluation_summary["min_topic_relevance"] = round(min(topic_relevance_scores), 3)
                evaluation_summary["max_topic_relevance"] = round(max(topic_relevance_scores), 3)
                evaluation_summary["topic_provided"] = topic
            response["evaluation_summary"] = evaluation_summary

        return response
    except Exception as e:
        logger.error(f"ingest_url failed: {e}")
        raise


@handle_database_errors_async("file ingestion")
@deduplicate_request()
async def ingest_file_impl(
    db: Database,
    doc_store: DocumentStore,
    unified_mediator,
    graph_store: Optional[GraphStore],
    file_path: str,
    collection_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    include_chunk_ids: bool = False,
    progress_callback=None,
    mode: str = "ingest",
    # Evaluation parameters
    topic: Optional[str] = None,
    reviewed_by_human: bool = False,
    # Audit parameters
    actor_type: str = "agent",
) -> Dict[str, Any]:
    """
    Implementation of ingest_file tool.

    Routes through unified mediator to update both RAG and Knowledge Graph.
    Performs health checks on both databases before ingestion.

    **Supported file types:**
    - Text files: .txt, .md, .rst, .adoc, .tex, .org, and any UTF-8 text
    - Code files: .py, .js, .ts, .java, .go, .rs, .c, .cpp, .rb, .php, etc.
    - Config files: .json, .yaml, .yml, .toml, .xml, .ini, .env, etc.
    - Markup: .html, .css, .sql, .graphql, .proto, etc.
    - PDFs: Extracted to markdown via pymupdf4llm

    **NOT supported (will error):**
    - Images: .jpg, .png, .gif, .svg, etc.
    - Videos/Audio: .mp4, .mp3, .wav, etc.
    - Archives: .zip, .tar, .gz, etc.
    - Office docs: .docx, .xlsx, .pptx (use PDF export instead)
    - Binary files: .exe, .dll, .pyc, etc.

    **Size limit:** 10 MB per file

    Args:
        file_path: Path to the file to ingest
        collection_name: Target collection (must exist)
        metadata: Optional metadata to attach to the document
        include_chunk_ids: If True, include chunk IDs in response
        mode: "ingest" (error if exists) or "reingest" (overwrite)
        progress_callback: Optional async callback for MCP progress notifications
        topic: Optional topic for relevance scoring (Mode A vs Mode B)
        reviewed_by_human: Set to True ONLY when user explicitly confirmed review

    Returns:
        Dict with source_document_id, num_chunks, filename, file_type, evaluation, etc.

    Raises:
        ValueError: If file type not supported, file too large, or collection doesn't exist
        FileNotFoundError: If file doesn't exist
    """
    try:
        # Progress: Starting
        if progress_callback:
            await progress_callback(0, 100, "Starting file ingestion...")

        # Health check: both PostgreSQL and Neo4j must be reachable
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return health_error

        # Validate path is within configured mounts
        from src.core.config_loader import is_path_in_mounts
        is_valid, mount_msg = is_path_in_mounts(file_path)
        if not is_valid:
            raise PermissionError(mount_msg)

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate collection exists (centralized)
        validate_collection_exists(doc_store, collection_name)

        # Validate mode (centralized)
        validate_mode(mode)

        # Progress: Reading file
        if progress_callback:
            await progress_callback(5, 100, f"Reading file {path.name}...")

        logger.info(f"Ingesting file through unified mediator: {path.name}")

        # Read file and prepare metadata (centralized)
        content, file_metadata = read_file_with_metadata(path, metadata)

        # Compute content hash for duplicate detection
        content_hash = compute_content_hash(content)
        logger.info(f"Computed content hash: {content_hash[:16]}...")

        # Check for existing document with same content hash in ANY collection (global check)
        existing = check_duplicate_by_hash_global(db, content_hash)

        # Get collection info for evaluation
        collection = doc_store.collection_mgr.get_collection(collection_name)
        collection_description = collection.get("description", "") if collection else ""

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
            return {
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
            }

        # =================================================================
        # CASE 1: mode=ingest + hash matches in SAME collection = Smart Update
        # =================================================================
        if existing and mode == "ingest" and collection_name in existing.get("collections", []):
            logger.info(f"Content hash matches existing doc ID={existing['doc_id']}")
            logger.info("Smart update: Updating metadata only (no re-embed, no re-graph)")

            if progress_callback:
                await progress_callback(20, 100, "Same content detected, updating metadata...")

            # Determine if we need to re-run LLM evaluation
            needs_eval = (topic != existing.get("topic_provided"))

            eval_result = None
            if needs_eval:
                logger.info(f"Topic changed ('{existing.get('topic_provided')}' -> '{topic}'), re-running evaluation")
                from src.mcp.evaluation import evaluate_content
                eval_result = await evaluate_content(
                    content=content,
                    collection_name=collection_name,
                    collection_description=collection_description,
                    topic=topic,
                )

            if progress_callback:
                await progress_callback(50, 100, "Updating document metadata...")

            # Smart update - update metadata, timestamps, and eval fields if needed
            # Note: filename intentionally NOT updated to preserve existing LLM-generated title
            # MERGE existing metadata with new file_metadata (new values take precedence)
            merged_metadata = {**(existing.get("metadata") or {}), **file_metadata}
            update_result = update_document_metadata_only(
                db=db,
                doc_id=existing["doc_id"],
                metadata=merged_metadata,  # MERGE with existing, not replace
                reviewed_by_human=reviewed_by_human if reviewed_by_human else None,  # Only update if True
                # Eval fields - only update if we re-ran eval
                topic_provided=topic if needs_eval else None,
                quality_score=eval_result.quality_score if eval_result else None,
                quality_summary=eval_result.quality_summary if eval_result else None,
                topic_relevance_score=eval_result.topic_relevance_score if eval_result else None,
                topic_relevance_summary=eval_result.topic_relevance_summary if eval_result else None,
                eval_model=eval_result.model if eval_result else None,
                eval_timestamp=eval_result.timestamp if eval_result else None,
            )

            if progress_callback:
                await progress_callback(100, 100, "Update complete")

            # Build evaluation for response
            evaluation = {
                "quality_score": eval_result.quality_score if eval_result else existing.get("quality_score"),
                "quality_summary": eval_result.quality_summary if eval_result else existing.get("quality_summary"),
            }
            if topic:
                evaluation["topic_relevance_score"] = eval_result.topic_relevance_score if eval_result else existing.get("topic_relevance_score")
                evaluation["topic_relevance_summary"] = eval_result.topic_relevance_summary if eval_result else existing.get("topic_relevance_summary")
                evaluation["topic_provided"] = topic

            return {
                "status": "updated",
                "source_document_id": existing["doc_id"],
                "content_changed": False,
                "updated_fields": update_result["updated_fields"],
                "filename": path.name,
                "file_type": file_metadata["file_type"],
                "file_size": file_metadata["file_size"],
                "collection_name": collection_name,
                "evaluation": evaluation,
                "message": "Content unchanged. Metadata and timestamps updated."
            }

        # =================================================================
        # CASE 2: mode=reingest + hash matches = Full Delete + Fresh Ingest
        # =================================================================
        if existing and mode == "reingest":
            if progress_callback:
                await progress_callback(10, 100, f"Reingest: Deleting old document...")

            logger.info(f"Reingest mode: Full delete + fresh ingest for doc ID={existing['doc_id']}")

            # Delete old document, chunks, and graph episode
            await delete_document_for_reingest(
                doc_id=existing['doc_id'],
                doc_store=doc_store,
                graph_store=graph_store,
                filename=existing['filename']
            )
            # Continue to full ingest below...

        # =================================================================
        # CASE 3: New content (or mode=reingest) = Full Ingest
        # =================================================================
        if progress_callback:
            await progress_callback(15, 100, f"Running content evaluation...")

        # Run LLM evaluation (advisory only, never blocks ingestion)
        from src.mcp.evaluation import evaluate_content
        logger.info(f"Running content evaluation (topic={'provided' if topic else 'none'})")
        eval_result = await evaluate_content(
            content=content,
            collection_name=collection_name,
            collection_description=collection_description,
            topic=topic,
        )

        # Progress: Ingesting (pass callback to mediator)
        if progress_callback:
            await progress_callback(20, 100, f"Processing {path.name}...")

        ingest_result = await unified_mediator.ingest_text(
            content=content,
            collection_name=collection_name,
            document_title=path.name,
            metadata=file_metadata,
            progress_callback=progress_callback,
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

        result = {
            "status": "reingested" if (existing and mode == "reingest") else "ingested",
            "source_document_id": ingest_result["source_document_id"],
            "num_chunks": ingest_result["num_chunks"],
            "entities_extracted": ingest_result.get("entities_extracted", 0),
            "filename": path.name,
            "file_type": file_metadata["file_type"],
            "file_size": file_metadata["file_size"],
            "collection_name": collection_name,
        }

        if include_chunk_ids:
            result["chunk_ids"] = ingest_result.get("chunk_ids", [])

        # Add evaluation to response
        evaluation = {
            "quality_score": eval_result.quality_score,
            "quality_summary": eval_result.quality_summary,
        }
        if topic:
            evaluation["topic_relevance_score"] = eval_result.topic_relevance_score
            evaluation["topic_relevance_summary"] = eval_result.topic_relevance_summary
            evaluation["topic_provided"] = eval_result.topic_provided
        result["evaluation"] = evaluation

        # Audit logging
        create_audit_entry(
            db=db,
            source_document_id=result["source_document_id"],
            actor_type=actor_type,
            ingest_method="file",
            collection_name=collection_name,
            source_file_path=file_path,
            metadata={
                "filename": path.name,
                "file_type": file_metadata["file_type"],
                "file_size": file_metadata["file_size"],
                "evaluation": evaluation,
            },
        )

        return result
    except Exception as e:
        logger.error(f"ingest_file failed: {e}")
        raise


@handle_database_errors_async("directory ingestion")
@deduplicate_request()
async def ingest_directory_impl(
    db: Database,
    doc_store: DocumentStore,
    unified_mediator,
    graph_store: Optional[GraphStore],
    directory_path: str,
    collection_name: str,
    file_extensions: Optional[List[str]] = None,
    recursive: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
    include_document_ids: bool = False,
    progress_callback=None,
    mode: str = "ingest",
    # Evaluation parameters
    topic: Optional[str] = None,
    reviewed_by_human: bool = False,
    # Audit parameters
    actor_type: str = "agent",
) -> Dict[str, Any]:
    """
    Implementation of ingest_directory tool.

    Routes through unified mediator to update both RAG and Knowledge Graph.
    Performs health checks on both databases before ingestion.

    **Supported file types:**
    - Text files: .txt, .md, .rst, .adoc, .tex, .org, and any UTF-8 text
    - Code files: .py, .js, .ts, .java, .go, .rs, .c, .cpp, .rb, .php, etc.
    - Config files: .json, .yaml, .yml, .toml, .xml, .ini, .env, etc.
    - Markup: .html, .css, .sql, .graphql, .proto, etc.
    - PDFs: Extracted to markdown via pymupdf4llm

    **NOT supported (will be skipped or error):**
    - Images: .jpg, .png, .gif, .svg, etc.
    - Videos/Audio: .mp4, .mp3, .wav, etc.
    - Archives: .zip, .tar, .gz, etc.
    - Office docs: .docx, .xlsx, .pptx (use PDF export instead)
    - Binary files: .exe, .dll, .pyc, etc.

    **Size limit:** 10 MB per file

    Args:
        directory_path: Path to the directory to scan
        collection_name: Target collection (must exist)
        file_extensions: List of extensions to include (default: [".txt", ".md"])
        recursive: If True, scan subdirectories
        metadata: Optional metadata to attach to all documents
        include_document_ids: If True, include document IDs in response
        mode: "ingest" (error if exists) or "reingest" (overwrite)
        progress_callback: Optional async callback for MCP progress notifications
        topic: Optional topic for relevance scoring (Mode A vs Mode B)
        reviewed_by_human: Set to True ONLY when user explicitly confirmed review

    Returns:
        Dict with files_found, files_ingested, files_failed, total_chunks, evaluation_summary, etc.

    Raises:
        ValueError: If directory doesn't exist or collection doesn't exist
    """
    try:
        # Progress: Starting
        if progress_callback:
            await progress_callback(0, 100, "Starting directory ingestion...")

        # Health check: both PostgreSQL and Neo4j must be reachable
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return health_error

        # Validate path is within configured mounts
        from src.core.config_loader import is_path_in_mounts
        is_valid, mount_msg = is_path_in_mounts(directory_path)
        if not is_valid:
            raise PermissionError(mount_msg)

        path = Path(directory_path)

        if not path.exists() or not path.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")

        # Validate collection exists (centralized)
        validate_collection_exists(doc_store, collection_name)

        # Validate mode (centralized)
        validate_mode(mode)

        # Default extensions
        if not file_extensions:
            file_extensions = [".txt", ".md"]

        # Progress: Scanning directory
        if progress_callback:
            await progress_callback(5, 100, f"Scanning directory for {', '.join(file_extensions)} files...")

        # Find files
        files = []
        for ext in file_extensions:
            if recursive:
                files.extend(path.rglob(f"*{ext}"))
            else:
                files.extend(path.glob(f"*{ext}"))

        files = sorted(set(files))

        # Progress: Found files, reading content and computing hashes
        if progress_callback:
            await progress_callback(8, 100, f"Found {len(files)} files, reading content...")

        # Read all files and compute content hashes upfront
        file_data = []
        for file_path in files:
            try:
                content, file_metadata = read_file_with_metadata(file_path, metadata)
                content_hash = compute_content_hash(content)
                file_data.append({
                    "path": file_path,
                    "content": content,
                    "metadata": file_metadata,
                    "content_hash": content_hash,
                })
            except Exception as e:
                file_data.append({
                    "path": file_path,
                    "error": str(e),
                })

        # Progress: Checking for duplicates
        if progress_callback:
            await progress_callback(12, 100, f"Checking for duplicate content...")

        # Batch check content hashes for duplicates in ANY collection (global check)
        content_hashes = [f["content_hash"] for f in file_data if "content_hash" in f]
        existing_by_hash = check_duplicates_by_hash_batch_global(db, content_hashes)

        # Get collection description for evaluation (once, before loop)
        collection = doc_store.collection_mgr.get_collection(collection_name)
        collection_description = collection.get("description", "") if collection else ""

        # Import evaluation function
        from src.mcp.evaluation import evaluate_content

        # Process each file
        document_ids = []
        updated_files = []  # Files with same content, metadata updated
        ingested_files = []  # New files, fully ingested
        reingested_files = []  # mode=reingest files
        cross_collection_files = []  # Files that exist in OTHER collections (skipped)
        total_chunks = 0
        total_entities = 0
        failed_files = []

        # Track evaluation stats for aggregate summary
        quality_scores = []
        topic_relevance_scores = []

        for idx, fd in enumerate(file_data):
            # Progress: Per-file processing (15% to 90%)
            if progress_callback:
                file_progress = 15 + int((idx / len(file_data)) * 75)
                await progress_callback(
                    file_progress,
                    100,
                    f"Processing file {idx + 1}/{len(file_data)}: {fd['path'].name}..."
                )

            # Skip files that failed to read
            if "error" in fd:
                failed_files.append({"filename": fd["path"].name, "error": fd["error"]})
                continue

            file_path = fd["path"]
            content = fd["content"]
            file_metadata = fd["metadata"]
            content_hash = fd["content_hash"]

            try:
                # Check if this content hash has a duplicate (global check includes collections list)
                existing = existing_by_hash.get(content_hash)

                # =================================================================
                # CASE 0: Content exists in DIFFERENT collection + mode=ingest = Skip
                # (mode=reingest will delete and re-ingest in CASE 2 below)
                # =================================================================
                if mode == "ingest" and existing and collection_name not in existing.get("collections", []):
                    existing_collection = existing["collections"][0] if existing["collections"] else "unknown"
                    logger.warning(
                        f"File {file_path.name}: Content exists in different collection '{existing_collection}' "
                        f"(doc_id={existing['doc_id']}), skipping"
                    )
                    cross_collection_files.append({
                        "filename": file_path.name,
                        "existing_document_id": existing["doc_id"],
                        "existing_collection": existing_collection,
                        "existing_collections": existing["collections"],
                    })
                    continue  # Skip this file

                # =================================================================
                # CASE 1: mode=ingest + hash matches in SAME collection = Smart Update
                # =================================================================
                if existing and mode == "ingest" and collection_name in existing.get("collections", []):
                    logger.info(f"Content hash matches for {file_path.name}, doc ID={existing['doc_id']}")
                    logger.info("Smart update: Updating metadata only (no re-embed, no re-graph)")

                    # Determine if we need to re-run LLM evaluation
                    needs_eval = (topic != existing.get("topic_provided"))

                    eval_result = None
                    if needs_eval:
                        logger.info(f"Topic changed, re-running evaluation for {file_path.name}")
                        eval_result = await evaluate_content(
                            content=content,
                            collection_name=collection_name,
                            collection_description=collection_description,
                            topic=topic,
                        )
                        # Track eval stats
                        quality_scores.append(eval_result.quality_score)
                        if topic and eval_result.topic_relevance_score is not None:
                            topic_relevance_scores.append(eval_result.topic_relevance_score)
                    else:
                        # Use existing eval for stats
                        if existing.get("quality_score") is not None:
                            quality_scores.append(existing["quality_score"])
                        if topic and existing.get("topic_relevance_score") is not None:
                            topic_relevance_scores.append(existing["topic_relevance_score"])

                    # Smart update
                    # Note: filename intentionally NOT updated to preserve existing LLM-generated title
                    # MERGE existing metadata with new file_metadata (new values take precedence)
                    merged_metadata = {**(existing.get("metadata") or {}), **file_metadata}
                    update_document_metadata_only(
                        db=db,
                        doc_id=existing["doc_id"],
                        metadata=merged_metadata,  # MERGE with existing, not replace
                        reviewed_by_human=reviewed_by_human if reviewed_by_human else None,
                        topic_provided=topic if needs_eval else None,
                        quality_score=eval_result.quality_score if eval_result else None,
                        quality_summary=eval_result.quality_summary if eval_result else None,
                        topic_relevance_score=eval_result.topic_relevance_score if eval_result else None,
                        topic_relevance_summary=eval_result.topic_relevance_summary if eval_result else None,
                        eval_model=eval_result.model if eval_result else None,
                        eval_timestamp=eval_result.timestamp if eval_result else None,
                    )

                    document_ids.append(existing["doc_id"])
                    updated_files.append(file_path.name)
                    continue

                # =================================================================
                # CASE 2: mode=reingest + hash matches = Full Delete + Fresh Ingest
                # =================================================================
                if existing and mode == "reingest":
                    logger.info(f"Reingest mode: Full delete + fresh ingest for {file_path.name}")

                    # Delete old document
                    await delete_document_for_reingest(
                        doc_id=existing['doc_id'],
                        doc_store=doc_store,
                        graph_store=graph_store,
                        filename=existing['filename']
                    )
                    # Continue to full ingest below...

                # =================================================================
                # CASE 3: New content (or mode=reingest) = Full Ingest
                # =================================================================
                logger.info(f"Full ingest for {file_path.name}")

                # Run LLM evaluation
                eval_result = await evaluate_content(
                    content=content,
                    collection_name=collection_name,
                    collection_description=collection_description,
                    topic=topic,
                )

                # Track evaluation stats
                quality_scores.append(eval_result.quality_score)
                if topic and eval_result.topic_relevance_score is not None:
                    topic_relevance_scores.append(eval_result.topic_relevance_score)

                # Full ingest through unified mediator
                ingest_result = await unified_mediator.ingest_text(
                    content=content,
                    collection_name=collection_name,
                    document_title=file_path.name,
                    metadata=file_metadata,
                    progress_callback=None,  # Skip nested progress for batch operations
                    reviewed_by_human=reviewed_by_human,
                    quality_score=eval_result.quality_score,
                    quality_summary=eval_result.quality_summary,
                    topic_relevance_score=eval_result.topic_relevance_score,
                    topic_relevance_summary=eval_result.topic_relevance_summary,
                    topic_provided=eval_result.topic_provided,
                    eval_model=eval_result.model,
                    eval_timestamp=eval_result.timestamp,
                    content_hash=content_hash,
                )

                document_ids.append(ingest_result["source_document_id"])
                total_chunks += ingest_result["num_chunks"]
                total_entities += ingest_result.get("entities_extracted", 0)

                if existing and mode == "reingest":
                    reingested_files.append(file_path.name)
                else:
                    ingested_files.append(file_path.name)

                # Audit logging
                create_audit_entry(
                    db=db,
                    source_document_id=ingest_result["source_document_id"],
                    actor_type=actor_type,
                    ingest_method="directory",
                    collection_name=collection_name,
                    source_file_path=str(file_path),
                    metadata={
                        "filename": file_path.name,
                        "directory": directory_path,
                        "quality_score": eval_result.quality_score,
                    },
                )

            except Exception as e:
                failed_files.append({"filename": file_path.name, "error": str(e)})

        result = {
            "files_found": len(files),
            "files_ingested": len(ingested_files),
            "files_updated": len(updated_files),
            "files_reingested": len(reingested_files),
            "files_skipped_cross_collection": len(cross_collection_files),
            "files_failed": len(failed_files),
            "total_chunks": total_chunks,
            "collection_name": collection_name,
            "entities_extracted": total_entities,
        }

        # Include file lists for clarity
        if ingested_files:
            result["ingested"] = ingested_files
        if updated_files:
            result["updated"] = updated_files
        if reingested_files:
            result["reingested"] = reingested_files

        if include_document_ids:
            result["document_ids"] = document_ids

        if failed_files:
            result["failed_files"] = failed_files

        # Include cross-collection files with actionable info
        if cross_collection_files:
            result["cross_collection_files"] = cross_collection_files
            result["cross_collection_message"] = (
                f"{len(cross_collection_files)} file(s) skipped because content already exists in another collection. "
                f"Use manage_collection_link() to add them to '{collection_name}', or mode='reingest' to move them."
            )

        # Add aggregate evaluation summary
        if quality_scores:
            evaluation_summary = {
                "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 3),
                "min_quality_score": round(min(quality_scores), 3),
                "max_quality_score": round(max(quality_scores), 3),
            }
            if topic and topic_relevance_scores:
                evaluation_summary["avg_topic_relevance"] = round(sum(topic_relevance_scores) / len(topic_relevance_scores), 3)
                evaluation_summary["min_topic_relevance"] = round(min(topic_relevance_scores), 3)
                evaluation_summary["max_topic_relevance"] = round(max(topic_relevance_scores), 3)
                evaluation_summary["topic_provided"] = topic
            result["evaluation_summary"] = evaluation_summary

        # Add summary message
        parts = []
        if ingested_files:
            parts.append(f"{len(ingested_files)} new files ingested")
        if updated_files:
            parts.append(f"{len(updated_files)} files updated (content unchanged)")
        if reingested_files:
            parts.append(f"{len(reingested_files)} files reingested")
        if cross_collection_files:
            parts.append(f"{len(cross_collection_files)} files skipped (exist in other collection)")
        if failed_files:
            parts.append(f"{len(failed_files)} files failed")
        result["message"] = ", ".join(parts) if parts else "No files processed"

        return result
    except Exception as e:
        logger.error(f"ingest_directory failed: {e}")
        raise


async def update_document_impl(
    db: Database,
    doc_store: DocumentStore,
    document_id: int,
    content: Optional[str],
    title: Optional[str],
    metadata: Optional[Dict[str, Any]],
    reviewed_by_human: Optional[bool] = None,
    graph_store: Optional[GraphStore] = None,
) -> Dict[str, Any]:
    """
    Implementation of update_document tool.

    Updates document content, title, metadata, or review status with health checks.
    If content changes, Graph episode is cleaned up and re-indexed.
    Performs health checks on both databases before update (Option B: Mandatory).
    """
    try:
        # Health check: both PostgreSQL and Neo4j must be reachable
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return health_error

        if content is None and title is None and metadata is None and reviewed_by_human is None:
            raise ValueError(
                "At least one of content, title, metadata, or reviewed_by_human must be provided"
            )

        # Update RAG store (also deletes old graph episode if content changed)
        result = await doc_store.update_document(
            document_id=document_id,
            content=content,
            filename=title,
            metadata=metadata,
            reviewed_by_human=reviewed_by_human,
            graph_store=graph_store
        )

        # If content was updated, re-index into knowledge graph
        if content and graph_store and result.get("graph_episode_deleted"):
            logger.info(f"🕸️  Re-indexing document {document_id} into Knowledge Graph after content update")

            # Get updated document with merged metadata
            updated_doc = doc_store.get_source_document(document_id)
            if not updated_doc:
                raise ValueError(f"Document {document_id} not found after update")

            # Get collection name from chunks (since doc might be in multiple collections)
            conn = db.connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT c.name
                    FROM collections c
                    JOIN chunk_collections cc ON cc.collection_id = c.id
                    JOIN document_chunks dc ON dc.id = cc.chunk_id
                    WHERE dc.source_document_id = %s
                    LIMIT 1
                    """,
                    (document_id,)
                )
                row = cur.fetchone()
                collection_name = row[0] if row else "unknown"

            # Build graph metadata
            graph_metadata = updated_doc["metadata"].copy() if updated_doc["metadata"] else {}
            graph_metadata["collection_name"] = collection_name
            graph_metadata["document_title"] = updated_doc["filename"]

            # Re-index into graph
            try:
                entities = await graph_store.add_knowledge(
                    content=content,
                    source_document_id=document_id,
                    metadata=graph_metadata,
                    group_id=collection_name,
                    ingestion_timestamp=datetime.now()
                )
                logger.info(f"✅ Graph re-indexing completed - {len(entities)} entities extracted")
                result["entities_extracted"] = len(entities)
            except Exception as e:
                logger.error(f"❌ Graph re-indexing FAILED after RAG update (doc_id={document_id})")
                logger.error(f"   Error: {e}", exc_info=True)
                raise Exception(
                    f"Graph re-indexing failed after RAG update (doc_id={document_id}). "
                    f"Stores may be inconsistent. Error: {e}"
                )

        return result
    except Exception as e:
        logger.error(f"update_document failed: {e}")
        raise


async def delete_document_impl(
    db: Database,
    doc_store: DocumentStore,
    document_id: int,
    graph_store: Optional[GraphStore] = None,
) -> Dict[str, Any]:
    """
    Implementation of delete_document tool.

    Permanently removes document from RAG store and Graph.
    Performs health checks on both databases before deletion (Option B: Mandatory).

    ⚠️ WARNING: This operation is permanent and cannot be undone.
    """
    try:
        # Health check: both PostgreSQL and Neo4j must be reachable
        health_error = await ensure_databases_healthy(db, graph_store)
        if health_error:
            return health_error

        result = await doc_store.delete_document(document_id, graph_store=graph_store)
        return result
    except Exception as e:
        logger.error(f"delete_document failed: {e}")
        raise


def manage_collection_link_impl(
    db: Database,
    doc_store: DocumentStore,
    document_id: int,
    collection_name: str,
    unlink: bool = False,
) -> Dict[str, Any]:
    """
    Link or unlink a document to/from a collection.

    This tool manages the relationship between documents and collections:
    - Link (default): Add document to a collection so it appears in that collection's searches
    - Unlink: Remove document from a collection (with orphan protection)

    No re-embedding or re-graphing occurs - this is a metadata-only operation.
    Documents can exist in multiple collections without duplicating content.

    Args:
        db: Database connection
        doc_store: Document store for validation
        document_id: ID of existing document
        collection_name: Target collection (must exist)
        unlink: If False (default), link document to collection.
                If True, remove document from collection.

    Returns:
        Link: {"document_id": int, "collection_name": str, "chunks_linked": int, "status": "linked"}
        Unlink: {"document_id": int, "collection_name": str, "chunks_unlinked": int,
                 "status": "unlinked", "remaining_collections": list}

    Raises:
        ValueError: If document/collection doesn't exist, already linked (for link),
                    not linked (for unlink), or would orphan document (for unlink)
    """
    try:
        # 1. Verify document exists
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT filename FROM source_documents WHERE id = %s",
                (document_id,)
            )
            doc_row = cur.fetchone()
            if not doc_row:
                raise ValueError(f"Document {document_id} not found")
            doc_filename = doc_row[0]

        # 2. Verify collection exists
        collection = doc_store.collection_mgr.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")

        # 3. Get all chunks for this document
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM document_chunks WHERE source_document_id = %s",
                (document_id,)
            )
            chunk_rows = cur.fetchall()
            if not chunk_rows:
                raise ValueError(f"Document {document_id} has no chunks")
            chunk_ids = [row[0] for row in chunk_rows]

        # 4. Check current link status
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM chunk_collections cc
                JOIN document_chunks dc ON dc.id = cc.chunk_id
                WHERE dc.source_document_id = %s AND cc.collection_id = %s
                """,
                (document_id, collection["id"])
            )
            is_linked = cur.fetchone()[0] > 0

        if unlink:
            # === UNLINK OPERATION ===
            if not is_linked:
                raise ValueError(
                    f"Document {document_id} ('{doc_filename}') is not in collection '{collection_name}'"
                )

            # Get all collections this document is currently in
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT c.name FROM collections c
                    JOIN chunk_collections cc ON cc.collection_id = c.id
                    JOIN document_chunks dc ON dc.id = cc.chunk_id
                    WHERE dc.source_document_id = %s
                    """,
                    (document_id,)
                )
                current_collections = [row[0] for row in cur.fetchall()]

            # Orphan protection: document must remain in at least one collection
            if len(current_collections) <= 1:
                raise ValueError(
                    f"Cannot unlink document {document_id} ('{doc_filename}') from '{collection_name}' - "
                    f"it's the document's only collection. Use delete_document to remove entirely."
                )

            # Remove chunks from this collection
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM chunk_collections
                    WHERE collection_id = %s AND chunk_id IN (
                        SELECT id FROM document_chunks WHERE source_document_id = %s
                    )
                    """,
                    (collection["id"], document_id)
                )
                unlinked_count = cur.rowcount

            conn.commit()

            remaining_collections = [c for c in current_collections if c != collection_name]

            logger.info(
                f"Unlinked document {document_id} ('{doc_filename}') from collection '{collection_name}' "
                f"({unlinked_count} chunks). Remaining collections: {remaining_collections}"
            )

            return {
                "document_id": document_id,
                "document_title": doc_filename,
                "collection_name": collection_name,
                "chunks_unlinked": unlinked_count,
                "status": "unlinked",
                "remaining_collections": remaining_collections,
                "message": f"Document '{doc_filename}' removed from collection '{collection_name}'"
            }

        else:
            # === LINK OPERATION ===
            if is_linked:
                raise ValueError(
                    f"Document {document_id} ('{doc_filename}') is already in collection '{collection_name}'"
                )

            # Link all chunks to collection
            linked_count = 0
            with conn.cursor() as cur:
                for chunk_id in chunk_ids:
                    cur.execute(
                        "INSERT INTO chunk_collections (chunk_id, collection_id) VALUES (%s, %s)",
                        (chunk_id, collection["id"])
                    )
                    linked_count += 1

            conn.commit()

            logger.info(
                f"Linked document {document_id} ('{doc_filename}') to collection '{collection_name}' "
                f"({linked_count} chunks)"
            )

            return {
                "document_id": document_id,
                "document_title": doc_filename,
                "collection_name": collection_name,
                "chunks_linked": linked_count,
                "status": "linked",
                "message": f"Document '{doc_filename}' now appears in collection '{collection_name}'"
            }

    except ValueError:
        raise  # Re-raise validation errors as-is
    except Exception as e:
        logger.error(f"manage_collection_link failed: {e}")
        raise


@handle_database_errors("list documents")
def list_documents_impl(
    doc_store: DocumentStore,
    collection_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    include_details: bool = False,
) -> Dict[str, Any]:
    """
    Implementation of list_documents tool.

    Thin facade over DocumentStore.list_source_documents() business logic.
    """
    try:
        # Cap limit at 200
        if limit > 200:
            limit = 200

        # Call business logic layer
        result = doc_store.list_source_documents(
            collection_name=collection_name,
            limit=limit,
            offset=offset,
            include_details=include_details
        )

        # Convert datetime objects to ISO 8601 strings for JSON serialization
        for doc in result["documents"]:
            if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                doc["created_at"] = doc["created_at"].isoformat()
            if "updated_at" in doc and hasattr(doc["updated_at"], "isoformat"):
                doc["updated_at"] = doc["updated_at"].isoformat()

        return result
    except Exception as e:
        logger.error(f"list_documents failed: {e}")
        raise


# =============================================================================
# Knowledge Graph Query Tools
# =============================================================================


async def resolve_episodes_to_source_docs(
    graph_store,
    db,
    episode_uuids: list[str]
) -> dict[str, Any]:
    """
    Resolve episode UUIDs to source document IDs and fetch evaluation metadata.

    Args:
        graph_store: GraphStore instance (for Neo4j queries)
        db: Database instance (for PostgreSQL queries)
        episode_uuids: List of episode UUIDs from edge.episodes

    Returns:
        {
            "document_ids": [int, ...],
            "all_reviewed": bool,  # True if ALL source docs reviewed by human
            "any_reviewed": bool,  # True if ANY source doc reviewed by human
            "avg_quality_score": float | None,
            "min_quality_score": float | None,
        }
    """
    if not episode_uuids:
        return {
            "document_ids": [],
            "all_reviewed": False,
            "any_reviewed": False,
            "avg_quality_score": None,
            "min_quality_score": None,
        }

    # Step 1: Query Neo4j to get episode names from UUIDs
    try:
        query = """
        MATCH (e:Episodic)
        WHERE e.uuid IN $uuids
        RETURN e.uuid as uuid, e.name as name
        """
        result = await graph_store.graphiti.driver.execute_query(
            query,
            uuids=episode_uuids
        )

        # Parse episode names to extract document IDs (format: "doc_42")
        doc_ids = []
        for record in result.records:
            name = record.get('name', '')
            if name and name.startswith('doc_'):
                try:
                    doc_id = int(name[4:])  # Extract number after "doc_"
                    doc_ids.append(doc_id)
                except ValueError:
                    continue

        if not doc_ids:
            return {
                "document_ids": [],
                "all_reviewed": False,
                "any_reviewed": False,
                "avg_quality_score": None,
                "min_quality_score": None,
            }

        # Step 2: Query PostgreSQL for document evaluation metadata
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, reviewed_by_human, quality_score
                FROM source_documents
                WHERE id = ANY(%s)
                """,
                (doc_ids,)
            )
            rows = cur.fetchall()

        if not rows:
            return {
                "document_ids": doc_ids,
                "all_reviewed": False,
                "any_reviewed": False,
                "avg_quality_score": None,
                "min_quality_score": None,
            }

        # Step 3: Compute aggregates
        reviewed_flags = [bool(row[1]) for row in rows]
        quality_scores = [float(row[2]) for row in rows if row[2] is not None]

        return {
            "document_ids": doc_ids,
            "all_reviewed": all(reviewed_flags) if reviewed_flags else False,
            "any_reviewed": any(reviewed_flags) if reviewed_flags else False,
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else None,
            "min_quality_score": min(quality_scores) if quality_scores else None,
        }

    except Exception as e:
        logger.warning(f"Failed to resolve episodes to source docs: {e}")
        return {
            "document_ids": [],
            "all_reviewed": False,
            "any_reviewed": False,
            "avg_quality_score": None,
            "min_quality_score": None,
        }


async def query_relationships_impl(
    graph_store,
    query: str,
    collection_name: str | None = None,
    num_results: int = 5,
    threshold: float = 0.2,
    # Source document enrichment and filtering (Phase 4b)
    db=None,
    include_source_docs: bool = False,
    reviewed_by_human: bool | None = None,
    min_quality_score: float | None = None,
) -> Dict[str, Any]:
    """
    Implementation of query_relationships tool.

    Searches the knowledge graph for entity relationships using natural language.
    Returns relationships (edges) between entities that match the query.

    Args:
        graph_store: GraphStore instance
        query: Natural language query
        collection_name: Optional collection to scope search
        num_results: Maximum number of results to return
        threshold: Minimum relevance score (0.0-1.0, default 0.2)
                  Higher = stricter filtering (fewer, more relevant results)
                  Lower = more permissive (more results, may include less relevant)
                  Strategy-specific defaults apply if not overridden
        db: Database instance (required for source doc enrichment/filtering)
        include_source_docs: If True, include source document info for each relationship
        reviewed_by_human: Filter by human review (True=only reviewed, False=only unreviewed, None=all)
        min_quality_score: Filter by minimum quality score (0.0-1.0)
    """
    try:
        if not graph_store:
            return {
                "status": "unavailable",
                "message": "Knowledge Graph is not available. Only RAG search is enabled.",
                "relationships": []
            }

        # Convert collection_name to group_ids for internal implementation
        group_ids = [collection_name] if collection_name else None

        # Search the knowledge graph with specified threshold and collection scope
        results = await graph_store.search_relationships(
            query,
            num_results=num_results,
            reranker_min_score=threshold,
            group_ids=group_ids
        )

        # Handle both old API (object with .edges) and new API (returns list directly)
        if hasattr(results, 'edges'):
            edges = results.edges
            logger.info(f"DEBUG: results has edges, count={len(edges)}")

            # Build UUID-to-name mapping from nodes
            node_names = {}
            if hasattr(results, 'nodes'):
                logger.info(f"DEBUG: results has nodes, count={len(results.nodes)}")
                for node in results.nodes:
                    if hasattr(node, 'uuid') and hasattr(node, 'name'):
                        node_names[str(node.uuid)] = node.name
                        logger.info(f"DEBUG: Added node {node.uuid[:8]}... -> {node.name}")
                logger.info(f"DEBUG: Built node_names mapping with {len(node_names)} entries")
            else:
                logger.warning("DEBUG: results has NO nodes attribute!")
        elif isinstance(results, list):
            edges = results
            node_names = {}
            logger.info("DEBUG: results is a list (old API)")
        else:
            edges = []
            node_names = {}
            logger.warning("DEBUG: results is neither object with edges nor list!")

        # Check if source doc enrichment/filtering is needed
        needs_source_docs = include_source_docs or reviewed_by_human is not None or min_quality_score is not None

        # Convert edge objects to JSON-serializable dicts
        relationships = []
        for edge in edges[:num_results]:
            try:
                rel = {
                    "id": str(getattr(edge, 'uuid', '')),
                    "relationship_type": getattr(edge, 'name', 'RELATED_TO'),
                    "fact": getattr(edge, 'fact', ''),
                }

                # Add source entity info - fetch from database if not in results.nodes
                if hasattr(edge, 'source_node_uuid'):
                    source_uuid = str(edge.source_node_uuid)
                    rel["source_node_id"] = source_uuid

                    if source_uuid in node_names:
                        rel["source_node_name"] = node_names[source_uuid]
                        logger.info(f"DEBUG: Matched source {source_uuid[:8]}... -> {node_names[source_uuid]}")
                    else:
                        # Fetch missing source node using Graphiti API
                        logger.info(f"DEBUG: Fetching missing source node {source_uuid[:8]}...")
                        try:
                            source_node = await EntityNode.get_by_uuid(graph_store.graphiti.driver, edge.source_node_uuid)
                            if source_node and hasattr(source_node, 'name'):
                                node_names[source_uuid] = source_node.name
                                rel["source_node_name"] = source_node.name
                                logger.info(f"DEBUG: Fetched source {source_uuid[:8]}... -> {source_node.name}")
                            else:
                                logger.warning(f"DEBUG: Source node {source_uuid[:8]}... not found in database")
                        except Exception as fetch_error:
                            logger.warning(f"DEBUG: Failed to fetch source node {source_uuid[:8]}...: {fetch_error}")

                # Add target entity info - fetch from database if not in results.nodes
                if hasattr(edge, 'target_node_uuid'):
                    target_uuid = str(edge.target_node_uuid)
                    rel["target_node_id"] = target_uuid

                    if target_uuid in node_names:
                        rel["target_node_name"] = node_names[target_uuid]
                        logger.info(f"DEBUG: Matched target {target_uuid[:8]}... -> {node_names[target_uuid]}")
                    else:
                        # Fetch missing target node using Graphiti API
                        logger.info(f"DEBUG: Fetching missing target node {target_uuid[:8]}...")
                        try:
                            target_node = await EntityNode.get_by_uuid(graph_store.graphiti.driver, edge.target_node_uuid)
                            if target_node and hasattr(target_node, 'name'):
                                node_names[target_uuid] = target_node.name
                                rel["target_node_name"] = target_node.name
                                logger.info(f"DEBUG: Fetched target {target_uuid[:8]}... -> {target_node.name}")
                            else:
                                logger.warning(f"DEBUG: Target node {target_uuid[:8]}... not found in database")
                        except Exception as fetch_error:
                            logger.warning(f"DEBUG: Failed to fetch target node {target_uuid[:8]}...: {fetch_error}")

                # Add when relationship was established (temporal info is for query_temporal only)
                if hasattr(edge, 'valid_at') and edge.valid_at:
                    rel["valid_from"] = edge.valid_at.isoformat()

                # Source document enrichment and filtering (Phase 4b)
                if needs_source_docs and db:
                    episode_uuids = getattr(edge, 'episodes', []) or []
                    if episode_uuids:
                        source_docs = await resolve_episodes_to_source_docs(
                            graph_store, db, episode_uuids
                        )

                        # Apply filters
                        passes_filter = True

                        if reviewed_by_human is True and not source_docs["any_reviewed"]:
                            passes_filter = False
                        elif reviewed_by_human is False and source_docs["any_reviewed"]:
                            passes_filter = False

                        if min_quality_score is not None:
                            min_score = source_docs["min_quality_score"]
                            if min_score is None or min_score < min_quality_score:
                                passes_filter = False

                        if not passes_filter:
                            continue  # Skip this relationship

                        # Include source_docs in response if requested
                        if include_source_docs:
                            rel["source_docs"] = source_docs

                relationships.append(rel)
            except Exception as e:
                logger.warning(f"Failed to serialize edge: {e}")
                continue

        return {
            "status": "success",
            "query": query,
            "num_results": len(relationships),
            "relationships": relationships
        }

    except Exception as e:
        logger.error(f"query_relationships failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "relationships": []
        }


async def query_temporal_impl(
    graph_store,
    query: str,
    collection_name: str | None = None,
    num_results: int = 10,
    threshold: float = 0.2,
    valid_from: str | None = None,
    valid_until: str | None = None,
    # Source document enrichment and filtering (Phase 4b)
    db=None,
    include_source_docs: bool = False,
    reviewed_by_human: bool | None = None,
    min_quality_score: float | None = None,
) -> Dict[str, Any]:
    """
    Implementation of query_temporal tool.

    Queries how knowledge has evolved over time. Shows facts with their
    temporal validity intervals to understand how information changed.

    Args:
        graph_store: GraphStore instance
        query: Natural language query about temporal changes
        collection_name: Optional collection to scope search
        num_results: Max results to return
        valid_from: (OPTIONAL) ISO 8601 date - filter facts valid after this date
        valid_until: (OPTIONAL) ISO 8601 date - filter facts valid before this date
        db: Database instance (required for source doc enrichment/filtering)
        include_source_docs: If True, include source document info for each timeline item
        reviewed_by_human: Filter by human review (True=only reviewed, False=only unreviewed, None=all)
        min_quality_score: Filter by minimum quality score (0.0-1.0)
    """
    try:
        if not graph_store:
            return {
                "status": "unavailable",
                "message": "Knowledge Graph is not available. Only RAG search is enabled.",
                "timeline": []
            }

        # Convert collection_name to group_ids for internal implementation
        group_ids = [collection_name] if collection_name else None

        # Delegate to GraphStore.search_temporal() - no direct Graphiti calls
        results = await graph_store.search_temporal(
            query,
            num_results=num_results,
            reranker_min_score=threshold,
            group_ids=group_ids,
            valid_from=valid_from,
            valid_until=valid_until
        )

        # Extract edges and build UUID-to-name mapping from nodes
        if hasattr(results, 'edges'):
            edges = results.edges
            # Build UUID-to-name mapping from nodes
            node_names = {}
            if hasattr(results, 'nodes'):
                for node in results.nodes:
                    if hasattr(node, 'uuid') and hasattr(node, 'name'):
                        node_names[str(node.uuid)] = node.name
        elif isinstance(results, list):
            edges = results
            node_names = {}
        else:
            edges = []
            node_names = {}

        # Check if source doc enrichment/filtering is needed
        needs_source_docs = include_source_docs or reviewed_by_human is not None or min_quality_score is not None

        # Convert to timeline format, grouped by temporal validity
        timeline_items = []
        for edge in edges[:num_results]:
            try:
                item = {
                    "fact": getattr(edge, 'fact', ''),
                    "relationship_type": getattr(edge, 'name', 'RELATED_TO'),
                }

                # Add entity names from node mapping
                if hasattr(edge, 'source_node_uuid'):
                    source_uuid = str(edge.source_node_uuid)
                    item["source_node_id"] = source_uuid
                    if source_uuid in node_names:
                        item["source_node_name"] = node_names[source_uuid]

                if hasattr(edge, 'target_node_uuid'):
                    target_uuid = str(edge.target_node_uuid)
                    item["target_node_id"] = target_uuid
                    if target_uuid in node_names:
                        item["target_node_name"] = node_names[target_uuid]

                # Add temporal validity (when the fact was true)
                if hasattr(edge, 'valid_at') and edge.valid_at:
                    item["valid_from"] = edge.valid_at.isoformat()
                else:
                    item["valid_from"] = None

                if hasattr(edge, 'invalid_at') and edge.invalid_at:
                    item["valid_until"] = edge.invalid_at.isoformat()
                else:
                    item["valid_until"] = None

                # Determine status based on whether Graphiti marked it as expired/superseded
                # expired_at = fact was replaced by newer version (superseded in knowledge graph)
                # invalid_at = fact's temporal validity ended (different from being superseded)
                if hasattr(edge, 'expired_at') and edge.expired_at:
                    item["status"] = "superseded"
                    item["expired_at"] = edge.expired_at.isoformat()
                else:
                    item["status"] = "current"
                    item["expired_at"] = None

                # Add creation timestamp
                if hasattr(edge, 'created_at') and edge.created_at:
                    item["created_at"] = edge.created_at.isoformat()

                # Source document enrichment and filtering (Phase 4b)
                if needs_source_docs and db:
                    episode_uuids = getattr(edge, 'episodes', []) or []
                    if episode_uuids:
                        source_docs = await resolve_episodes_to_source_docs(
                            graph_store, db, episode_uuids
                        )

                        # Apply filters
                        passes_filter = True

                        if reviewed_by_human is True and not source_docs["any_reviewed"]:
                            passes_filter = False
                        elif reviewed_by_human is False and source_docs["any_reviewed"]:
                            passes_filter = False

                        if min_quality_score is not None:
                            min_score = source_docs["min_quality_score"]
                            if min_score is None or min_score < min_quality_score:
                                passes_filter = False

                        if not passes_filter:
                            continue  # Skip this timeline item

                        # Include source_docs in response if requested
                        if include_source_docs:
                            item["source_docs"] = source_docs

                timeline_items.append(item)
            except Exception as e:
                logger.warning(f"Failed to serialize temporal edge: {e}")
                continue

        # Sort by valid_from date (most recent first)
        timeline_items.sort(
            key=lambda x: x.get('valid_from') or '',
            reverse=True
        )

        return {
            "status": "success",
            "query": query,
            "num_results": len(timeline_items),
            "timeline": timeline_items
        }

    except Exception as e:
        logger.error(f"query_temporal failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timeline": []
        }


# =============================================================================
# Directory Exploration Tools
# =============================================================================


def format_size_human(size_bytes: int) -> str:
    """Convert bytes to human-readable format (e.g., '14.9 KB')."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def list_directory_impl(
    directory_path: str,
    file_extensions: list = None,
    recursive: bool = False,
    include_preview: bool = False,
    preview_chars: int = 500,
    max_files: int = 100,
) -> Dict[str, Any]:
    """
    List files in a directory WITHOUT ingesting them.

    This is a READ-ONLY exploration tool that helps agents understand what files
    exist before deciding which ones to ingest into the knowledge base.

    Args:
        directory_path: Absolute path to the directory to explore
        file_extensions: Filter by extensions, e.g., [".md", ".pdf"]. None = all files
        recursive: If True, searches subdirectories recursively
        include_preview: If True, returns first N chars of text files for assessment
        preview_chars: Characters to preview (default 500)
        max_files: Maximum files to return (default 100)

    Returns:
        {
            "status": "success" or "error",
            "directory_path": str,
            "total_files_found": int,
            "files_returned": int,
            "truncated": bool,
            "files": [...],
            "extensions_found": {".md": 8, ".pdf": 5},
            "error": str or None
        }
    """
    try:
        # Validate path is within configured mounts
        from src.core.config_loader import is_path_in_mounts
        is_valid, mount_msg = is_path_in_mounts(directory_path)
        if not is_valid:
            return {
                "status": "error",
                "directory_path": directory_path,
                "total_files_found": 0,
                "files_returned": 0,
                "truncated": False,
                "files": [],
                "extensions_found": {},
                "error": mount_msg,
            }

        path = Path(directory_path)

        # Check if path exists
        if not path.exists():
            return {
                "status": "error",
                "directory_path": directory_path,
                "total_files_found": 0,
                "files_returned": 0,
                "truncated": False,
                "files": [],
                "extensions_found": {},
                "error": f"Directory not found: {directory_path}",
            }

        # Check if path is a directory
        if not path.is_dir():
            return {
                "status": "error",
                "directory_path": directory_path,
                "total_files_found": 0,
                "files_returned": 0,
                "truncated": False,
                "files": [],
                "extensions_found": {},
                "error": f"Path is a file, not a directory: {directory_path}",
            }

        # Collect files
        all_files = []

        if file_extensions:
            # Normalize extensions to include leading dot
            normalized_exts = [
                ext if ext.startswith(".") else f".{ext}"
                for ext in file_extensions
            ]

            for ext in normalized_exts:
                if recursive:
                    all_files.extend(path.rglob(f"*{ext}"))
                else:
                    all_files.extend(path.glob(f"*{ext}"))
        else:
            # All files
            if recursive:
                all_files = [f for f in path.rglob("*") if f.is_file()]
            else:
                all_files = [f for f in path.glob("*") if f.is_file()]

        # Deduplicate and sort
        all_files = sorted(set(all_files))
        total_found = len(all_files)

        # Apply max_files limit
        truncated = len(all_files) > max_files
        files_to_process = all_files[:max_files]

        # Build file list with metadata
        file_list = []
        extensions_count = {}

        # Text-like extensions for preview
        text_extensions = {
            ".txt", ".md", ".markdown", ".rst", ".json", ".yaml", ".yml",
            ".xml", ".html", ".htm", ".css", ".js", ".ts", ".tsx", ".jsx",
            ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs",
            ".rb", ".php", ".sh", ".bash", ".zsh", ".sql", ".csv",
            ".toml", ".ini", ".cfg", ".conf", ".log", ".env",
        }

        for file_path in files_to_process:
            try:
                stat = file_path.stat()
                ext = file_path.suffix.lower()

                # Count extensions
                extensions_count[ext] = extensions_count.get(ext, 0) + 1

                file_info = {
                    "path": str(file_path.absolute()),
                    "filename": file_path.name,
                    "extension": ext,
                    "size_bytes": stat.st_size,
                    "size_human": format_size_human(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

                # Add preview if requested and file is text-based
                if include_preview and ext in text_extensions:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            preview = f.read(preview_chars)
                            if len(preview) == preview_chars:
                                preview += "..."
                            file_info["preview"] = preview
                    except Exception as e:
                        file_info["preview"] = f"[Could not read: {e}]"

                file_list.append(file_info)

            except PermissionError:
                # Skip files we can't access, but note them
                file_list.append({
                    "path": str(file_path.absolute()),
                    "filename": file_path.name,
                    "extension": file_path.suffix.lower(),
                    "size_bytes": 0,
                    "size_human": "0 B",
                    "modified": None,
                    "error": "Permission denied",
                })
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
                continue

        return {
            "status": "success",
            "directory_path": directory_path,
            "total_files_found": total_found,
            "files_returned": len(file_list),
            "truncated": truncated,
            "files": file_list,
            "extensions_found": extensions_count,
            "error": None,
        }

    except PermissionError:
        return {
            "status": "error",
            "directory_path": directory_path,
            "total_files_found": 0,
            "files_returned": 0,
            "truncated": False,
            "files": [],
            "extensions_found": {},
            "error": f"Permission denied: {directory_path}",
        }
    except Exception as e:
        logger.error(f"list_directory failed: {e}")
        return {
            "status": "error",
            "directory_path": directory_path,
            "total_files_found": 0,
            "files_returned": 0,
            "truncated": False,
            "files": [],
            "extensions_found": {},
            "error": str(e),
        }
