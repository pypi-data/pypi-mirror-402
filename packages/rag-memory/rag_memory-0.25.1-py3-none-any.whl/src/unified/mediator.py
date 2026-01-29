"""
UnifiedIngestionMediator - Orchestrates ingestion to both RAG and Graph stores.

This module provides a single entry point for content ingestion that ensures
both the vector-based RAG store and the knowledge graph are updated together.

Note: This is Phase 1 implementation without true atomic transactions.
Both stores are updated sequentially, with potential for inconsistency if
the second operation fails. Two-phase commit will be added in Phase 2.
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Callable, Awaitable

from openai import AsyncOpenAI

from src.core.database import Database
from src.core.embeddings import EmbeddingGenerator
from src.core.collections import CollectionManager
from src.ingestion.document_store import DocumentStore, get_document_store
from .graph_store import GraphStore

logger = logging.getLogger(__name__)

# =============================================================================
# Title Generation Configuration
# =============================================================================
# These can be overridden via environment variables

# Model for title generation (lightweight, fast)
TITLE_GEN_MODEL = os.getenv("TITLE_GEN_MODEL", "gpt-4o-mini")

# Maximum content to send for title generation (characters)
TITLE_GEN_MAX_CHARS = int(os.getenv("TITLE_GEN_MAX_CHARS", "2500"))

# Temperature for title generation (lower = more consistent)
TITLE_GEN_TEMPERATURE = float(os.getenv("TITLE_GEN_TEMPERATURE", "0.3"))

# Common file extensions that indicate a filename (not a real title)
FILE_EXTENSIONS = {
    ".txt", ".md", ".json", ".yaml", ".yml", ".html", ".css",
    ".js", ".ts", ".tsx", ".jsx", ".py", ".java", ".c", ".cpp",
    ".go", ".rs", ".rb", ".php", ".sh", ".xml", ".toml", ".log",
    ".csv", ".sql", ".graphql", ".proto", ".dockerfile", ".makefile",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}

# Generic titles that should be replaced (case-insensitive)
GENERIC_TITLES = {
    "home", "welcome", "index", "untitled", "document", "page",
    "readme", "test", "temp", "tmp", "draft", "copy", "new",
    "file", "data", "content", "text", "note", "notes",
}

# Pattern for auto-generated titles from ingest_text
AUTO_GENERATED_PATTERN = re.compile(r"^Agent-Text-")


class UnifiedIngestionMediator:
    """
    Orchestrates content ingestion to both RAG and Graph stores.

    This mediator ensures that content is added to both:
    1. Vector-based RAG store (pgvector) - for semantic search
    2. Knowledge graph (Graphiti/Neo4j) - for relationship queries

    Currently uses sequential updates (RAG first, then Graph).
    Future enhancement: Add two-phase commit for atomicity.
    """

    def __init__(
        self,
        db: Database,
        embedder: EmbeddingGenerator,
        collection_mgr: CollectionManager,
        graph_store: GraphStore
    ):
        """
        Initialize the mediator with RAG and Graph dependencies.

        Args:
            db: Database connection
            embedder: Embeddings generator
            collection_mgr: Collection manager
            graph_store: Graph store wrapper (Graphiti)
        """
        self.rag_store: DocumentStore = get_document_store(db, embedder, collection_mgr)
        self.graph_store = graph_store
        self._openai_client: Optional[AsyncOpenAI] = None

    def _get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client for title generation."""
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI()
        return self._openai_client

    def _needs_title_generation(self, title: Optional[str]) -> bool:
        """
        Determine if a title needs LLM generation.

        Returns True if:
        - Title is None or empty
        - Title looks like a filename (has file extension)
        - Title matches auto-generated pattern (Agent-Text-*)
        - Title is a generic/placeholder title
        - Title is a URL

        Args:
            title: The current title (may be filename, HTML title, user-provided, etc.)

        Returns:
            True if LLM should generate a new title
        """
        if not title or not title.strip():
            return True

        title_stripped = title.strip()
        title_lower = title_stripped.lower()

        # Check for auto-generated pattern
        if AUTO_GENERATED_PATTERN.match(title_stripped):
            logger.debug(f"Title '{title_stripped}' matches auto-generated pattern")
            return True

        # Check for file extension (indicates filename)
        suffix = Path(title_stripped).suffix.lower()
        if suffix in FILE_EXTENSIONS:
            logger.debug(f"Title '{title_stripped}' looks like a filename (extension: {suffix})")
            return True

        # Check for generic titles
        # Strip extension first for comparison
        title_without_ext = Path(title_lower).stem
        if title_without_ext in GENERIC_TITLES or title_lower in GENERIC_TITLES:
            logger.debug(f"Title '{title_stripped}' is a generic title")
            return True

        # Check if it's a URL
        if title_lower.startswith(("http://", "https://", "www.")):
            logger.debug(f"Title '{title_stripped}' is a URL")
            return True

        # Title looks intentional/meaningful
        return False

    async def _generate_title(self, content: str) -> str:
        """
        Generate a descriptive title for document content using LLM.

        Uses the first N characters of content (configurable via TITLE_GEN_MAX_CHARS)
        to generate a clear, descriptive title.

        Args:
            content: Full document content

        Returns:
            Generated title string
        """
        # Take first N characters for context
        content_sample = content[:TITLE_GEN_MAX_CHARS]

        logger.info(f"Generating title from {len(content_sample)} chars of content...")

        try:
            client = self._get_openai_client()

            response = await client.chat.completions.create(
                model=TITLE_GEN_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate a clear, descriptive title for this document based on its content. "
                            "The title should summarize the document's main topic or purpose. "
                            "Keep it concise but informative (typically 5-15 words). "
                            "Return only the title text, no quotes, no formatting, no explanation."
                        )
                    },
                    {
                        "role": "user",
                        "content": content_sample
                    }
                ],
                max_tokens=60,
                temperature=TITLE_GEN_TEMPERATURE,
            )

            generated_title = response.choices[0].message.content.strip()

            # Clean up any quotes the model might have added
            if generated_title.startswith('"') and generated_title.endswith('"'):
                generated_title = generated_title[1:-1]
            if generated_title.startswith("'") and generated_title.endswith("'"):
                generated_title = generated_title[1:-1]

            logger.info(f"Generated title: '{generated_title}'")
            return generated_title

        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            # Fallback: use first 50 chars of content as title
            fallback = content[:50].strip()
            if len(content) > 50:
                fallback += "..."
            logger.warning(f"Using fallback title: '{fallback}'")
            return fallback

    async def ingest_text(
        self,
        content: str,
        collection_name: str,
        document_title: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        progress_callback: Optional[Callable[[float, float, str], Awaitable[None]]] = None,
        # Evaluation fields
        reviewed_by_human: bool = False,
        quality_score: Optional[float] = None,
        quality_summary: Optional[str] = None,
        topic_relevance_score: Optional[float] = None,
        topic_relevance_summary: Optional[str] = None,
        topic_provided: Optional[str] = None,
        eval_model: Optional[str] = None,
        eval_timestamp: Optional[datetime] = None,
        # Content hash for duplicate detection
        content_hash: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Ingest text content into both RAG and Graph stores.

        Args:
            content: Text content to ingest
            collection_name: Collection to add content to (must exist)
            document_title: Optional human-readable title
            metadata: Optional metadata dict
            progress_callback: Optional async callback(progress, total, message) for MCP progress notifications
            reviewed_by_human: True only if user explicitly confirmed review
            quality_score: LLM quality assessment (0.0-1.0)
            quality_summary: Explanation of quality assessment
            topic_relevance_score: Relevance to topic (0.0-1.0), NULL if no topic
            topic_relevance_summary: Explanation of topic relevance, NULL if no topic
            topic_provided: The topic caller provided for evaluation, NULL if no topic
            eval_model: Model used for evaluation
            eval_timestamp: When evaluation was performed
            content_hash: SHA256 hash of content for duplicate detection

        Returns:
            dict with:
                - source_document_id: ID of source document in RAG store
                - num_chunks: Number of chunks created
                - entities_extracted: Number of entities extracted by graph
                - collection_name: Collection name

        Raises:
            ValueError: If collection doesn't exist
            Exception: If either RAG or Graph ingestion fails
        """
        logger.info(f"🔄 UnifiedIngestionMediator.ingest_text() - Starting dual ingestion")
        logger.info(f"   Collection: {collection_name}")
        logger.info(f"   Original title: {document_title}")
        logger.info(f"   Content length: {len(content)} chars")

        # Progress: Starting
        if progress_callback:
            await progress_callback(0, 100, "Starting ingestion...")

        # =================================================================
        # Title Generation: Ensure every document has a meaningful title
        # =================================================================
        # If no title provided, or title looks like a filename/generic,
        # generate a descriptive title using LLM
        original_title = document_title  # Keep for metadata
        if self._needs_title_generation(document_title):
            if progress_callback:
                await progress_callback(2, 100, "Generating document title...")
            document_title = await self._generate_title(content)
            logger.info(f"   Generated title: {document_title}")
        else:
            logger.info(f"   Using provided title: {document_title}")

        # Preserve original title in metadata (for reference)
        if original_title and original_title != document_title:
            if metadata is None:
                metadata = {}
            metadata["original_title"] = original_title

        # Step 1: Ingest into RAG store (existing functionality, unchanged)
        logger.info(f"📥 Step 1/2: Ingesting into RAG store (pgvector)...")

        # Progress: RAG phase
        if progress_callback:
            await progress_callback(10, 100, "Processing RAG embeddings...")

        source_id, chunk_ids = self.rag_store.ingest_document(
            content=content,
            filename=document_title or f"Agent-Text-{content[:20]}",
            collection_name=collection_name,
            metadata=metadata,
            file_type="text",
            # Pass evaluation fields
            reviewed_by_human=reviewed_by_human,
            quality_score=quality_score,
            quality_summary=quality_summary,
            topic_relevance_score=topic_relevance_score,
            topic_relevance_summary=topic_relevance_summary,
            topic_provided=topic_provided,
            eval_model=eval_model,
            eval_timestamp=eval_timestamp,
            # Pass content hash for duplicate detection
            content_hash=content_hash,
        )
        logger.info(f"✅ RAG ingestion completed - doc_id={source_id}, {len(chunk_ids)} chunks created")

        # Progress: RAG complete
        if progress_callback:
            await progress_callback(40, 100, "RAG complete, starting knowledge graph extraction...")

        # Validate document metadata against collection (guidance only, doesn't fail)
        try:
            self.rag_store.collection_mgr.validate_document_mandatory_fields(
                collection_name, metadata or {}
            )
        except ValueError:
            # Log but don't fail - validation is guidance only
            pass

        # Step 2: Ingest into Graph store (new functionality)
        logger.info(f"🕸️  Step 2/2: Ingesting into Knowledge Graph (Neo4j/Graphiti)...")

        # Progress: Graph extraction phase (this is the slow part!)
        if progress_callback:
            await progress_callback(50, 100, "Extracting entities and relationships (may take 1-2 minutes)...")

        # Build enhanced metadata with collection and title
        graph_metadata = metadata.copy() if metadata else {}
        graph_metadata["collection_name"] = collection_name
        if document_title:
            graph_metadata["document_title"] = document_title

        try:
            entities = await self.graph_store.add_knowledge(
                content=content,
                source_document_id=source_id,
                metadata=graph_metadata,
                group_id=collection_name,
                ingestion_timestamp=datetime.now()
            )
            logger.info(f"✅ Graph ingestion completed - {len(entities)} entities extracted")

            # Progress: Graph complete
            if progress_callback:
                await progress_callback(90, 100, f"Graph extraction complete ({len(entities)} entities)")

        except Exception as e:
            # Note: In Phase 1, we don't rollback RAG ingestion if graph fails
            # This is acceptable for POC but should be fixed in Phase 2
            logger.error(f"❌ Graph ingestion FAILED after RAG succeeded (doc_id={source_id})")
            logger.error(f"   Error: {e}", exc_info=True)
            raise Exception(
                f"Graph ingestion failed after RAG succeeded (doc_id={source_id}). "
                f"Stores may be inconsistent. Error: {e}"
            )

        logger.info(f"🎉 Unified ingestion completed successfully!")

        return {
            "source_document_id": source_id,
            "num_chunks": len(chunk_ids),
            "entities_extracted": len(entities),
            "collection_name": collection_name,
            "chunk_ids": chunk_ids  # Include for compatibility
        }

    async def close(self):
        """Close graph store connection (RAG store uses connection pool)."""
        await self.graph_store.close()
