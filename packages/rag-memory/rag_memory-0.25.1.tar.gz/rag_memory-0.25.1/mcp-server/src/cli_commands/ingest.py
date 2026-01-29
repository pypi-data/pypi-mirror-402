"""Ingestion commands."""

import asyncio
import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console

from src.core.chunking import ChunkingConfig, get_document_chunker
from src.core.collections import get_collection_manager
from src.core.database import get_database
from src.core.embeddings import get_embedding_generator
from src.ingestion.document_store import get_document_store
from src.ingestion.web_crawler import WebCrawler, crawl_single_page

logger = logging.getLogger(__name__)
console = Console()


async def initialize_graph_components():
    """
    Initialize Knowledge Graph components within async context.

    This MUST be called from within an async function to avoid
    "Future attached to a different loop" errors.

    Returns:
        tuple: (graph_store, unified_mediator) if successful, (None, None) if failed
    """
    logger.info("Initializing Knowledge Graph components...")
    try:
        from graphiti_core import Graphiti
        from graphiti_core.llm_client.config import LLMConfig
        from graphiti_core.llm_client.openai_client import OpenAIClient

        from src.unified import GraphStore, UnifiedIngestionMediator

        # Read Neo4j connection details from environment
        import os

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found - Knowledge Graph will not be available")
            return None, None

        # Read optional Graphiti LLM model configuration from environment
        # If not specified, Graphiti will use its own defaults
        graphiti_model = os.getenv("GRAPHITI_MODEL")
        graphiti_small_model = os.getenv("GRAPHITI_SMALL_MODEL")

        # Create LLM client with optional model overrides
        llm_config_kwargs = {
            'api_key': openai_api_key
        }
        if graphiti_model:
            llm_config_kwargs['model'] = graphiti_model
            logger.info(f"Using configured Graphiti model: {graphiti_model}")
        if graphiti_small_model:
            llm_config_kwargs['small_model'] = graphiti_small_model
            logger.info(f"Using configured Graphiti small model: {graphiti_small_model}")

        llm_config = LLMConfig(**llm_config_kwargs)
        llm_client = OpenAIClient(llm_config)

        graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password, llm_client)

        # Initialize GraphStore wrapper
        graph_store = GraphStore(graphiti)

        # Initialize RAG components for unified mediator
        db = get_database()
        embedder = get_embedding_generator()
        coll_mgr = get_collection_manager(db)

        # Initialize unified mediator (creates rag_store internally)
        unified_mediator = UnifiedIngestionMediator(
            db=db,
            embedder=embedder,
            collection_mgr=coll_mgr,
            graph_store=graph_store
        )

        logger.info("Knowledge Graph components initialized successfully")
        return graph_store, unified_mediator

    except Exception as e:
        logger.warning(f"Failed to initialize Knowledge Graph: {e}")
        return None, None


@click.group()
def ingest():
    """Ingest documents."""
    pass


@ingest.command("text")
@click.argument("content")
@click.option("--collection", required=True, help="Collection name")
@click.option("--title", help="Document title")
@click.option("--metadata", help="Additional metadata as JSON string")
@click.option("--mode", type=click.Choice(["ingest", "reingest"]), default="ingest",
              help="ingest=new (error if exists), reingest=replace existing")
@click.option("--topic", help="Topic for relevance scoring (optional)")
@click.option("--reviewed", is_flag=True, help="Mark as human-reviewed content")
@click.option("--show-chunk-ids", is_flag=True, help="Display generated chunk IDs")
def ingest_text_cmd(content, collection, title, metadata, mode, topic, reviewed, show_chunk_ids):
    """Ingest text content directly with automatic chunking.

    Routes through unified mediator to update both RAG store and Knowledge Graph.
    Falls back to RAG-only mode if Knowledge Graph unavailable.

    Examples:
        rag ingest text "My content here" --collection docs

        # Update existing content
        rag ingest text "Updated content" --collection docs --mode reingest

        # With topic for relevance scoring
        rag ingest text "API documentation" --collection docs --topic "REST APIs"

        # Mark as human-reviewed
        rag ingest text "Verified info" --collection docs --reviewed
    """

    async def run_ingest():
        try:
            from src.mcp.tools import ingest_text_impl

            metadata_dict = json.loads(metadata) if metadata else None

            console.print(f"[bold blue]Ingesting text content[/bold blue]")
            if mode == "reingest":
                console.print(f"[dim]Mode: reingest (will replace existing)[/dim]")
            if topic:
                console.print(f"[dim]Topic: {topic}[/dim]")
            if reviewed:
                console.print(f"[dim]Marked as: human-reviewed[/dim]")

            # Initialize all components
            db = get_database()
            embedder = get_embedding_generator()
            coll_mgr = get_collection_manager(db)
            doc_store = get_document_store(db, embedder, coll_mgr)

            # Initialize Knowledge Graph components (lazy initialization within async context)
            local_graph_store, local_unified_mediator = (
                await initialize_graph_components()
            )

            # Call the same implementation as MCP tool for full feature parity
            result = await ingest_text_impl(
                db=db,
                doc_store=doc_store,
                unified_mediator=local_unified_mediator,
                graph_store=local_graph_store,
                content=content,
                collection_name=collection,
                document_title=title,
                metadata=metadata_dict,
                include_chunk_ids=show_chunk_ids,
                mode=mode,
                topic=topic,
                reviewed_by_human=reviewed,
                actor_type="user",  # CLI is always user-operated
            )

            # Display results
            console.print(
                f"[bold green]✓ Ingested text (ID: {result['source_document_id']}) "
                f"with {result['num_chunks']} chunks to collection '{collection}'[/bold green]"
            )

            # Show evaluation results if available
            if "evaluation" in result:
                eval_data = result["evaluation"]
                if eval_data.get("quality_score") is not None:
                    console.print(f"[dim]Quality score: {eval_data['quality_score']:.2f}[/dim]")
                if eval_data.get("topic_relevance_score") is not None:
                    console.print(f"[dim]Topic relevance: {eval_data['topic_relevance_score']:.2f}[/dim]")

            if local_unified_mediator:
                console.print(
                    f"[dim]Entities extracted: {result.get('entities_extracted', 0)}[/dim]"
                )
            else:
                console.print(
                    "[dim]Knowledge Graph not available - RAG-only mode[/dim]"
                )

            # Show chunk IDs if requested
            if show_chunk_ids and result.get("chunk_ids"):
                console.print(f"[dim]Chunk IDs: {result['chunk_ids']}[/dim]")

        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_ingest())


@ingest.command("file")
@click.argument("path", type=click.Path(exists=True))
@click.option("--collection", required=True, help="Collection name")
@click.option("--metadata", help="Additional metadata as JSON string")
@click.option("--mode", type=click.Choice(["ingest", "reingest"]), default="ingest",
              help="ingest=new (error if exists), reingest=replace existing")
@click.option("--topic", help="Topic for relevance scoring (optional)")
@click.option("--reviewed", is_flag=True, help="Mark as human-reviewed content")
@click.option("--show-chunk-ids", is_flag=True, help="Display generated chunk IDs")
def ingest_file_cmd(path, collection, metadata, mode, topic, reviewed, show_chunk_ids):
    """Ingest a document from a file with automatic chunking.

    Routes through unified mediator to update both RAG store and Knowledge Graph.
    Falls back to RAG-only mode if Knowledge Graph unavailable.

    Examples:
        rag ingest file /path/to/doc.md --collection docs

        # Update existing file
        rag ingest file /path/to/doc.md --collection docs --mode reingest

        # With topic for relevance scoring
        rag ingest file /path/to/api.md --collection docs --topic "REST APIs"
    """

    async def run_ingest():
        try:
            from src.mcp.tools import ingest_file_impl

            metadata_dict = json.loads(metadata) if metadata else None

            console.print(f"[bold blue]Ingesting file: {path}[/bold blue]")
            if mode == "reingest":
                console.print(f"[dim]Mode: reingest (will replace existing)[/dim]")
            if topic:
                console.print(f"[dim]Topic: {topic}[/dim]")
            if reviewed:
                console.print(f"[dim]Marked as: human-reviewed[/dim]")

            # Initialize all components
            db = get_database()
            embedder = get_embedding_generator()
            coll_mgr = get_collection_manager(db)
            doc_store = get_document_store(db, embedder, coll_mgr)

            # Initialize Knowledge Graph components (lazy initialization within async context)
            local_graph_store, local_unified_mediator = (
                await initialize_graph_components()
            )

            # Call the same implementation as MCP tool for full feature parity
            result = await ingest_file_impl(
                db=db,
                doc_store=doc_store,
                unified_mediator=local_unified_mediator,
                graph_store=local_graph_store,
                file_path=path,
                collection_name=collection,
                metadata=metadata_dict,
                include_chunk_ids=show_chunk_ids,
                mode=mode,
                topic=topic,
                reviewed_by_human=reviewed,
                actor_type="user",  # CLI is always user-operated
            )

            # Display results
            console.print(
                f"[bold green]✓ Ingested file (ID: {result['source_document_id']}) "
                f"with {result['num_chunks']} chunks to collection '{collection}'[/bold green]"
            )

            # Show evaluation results if available
            if "evaluation" in result:
                eval_data = result["evaluation"]
                if eval_data.get("quality_score") is not None:
                    console.print(f"[dim]Quality score: {eval_data['quality_score']:.2f}[/dim]")
                if eval_data.get("topic_relevance_score") is not None:
                    console.print(f"[dim]Topic relevance: {eval_data['topic_relevance_score']:.2f}[/dim]")

            if local_unified_mediator:
                console.print(
                    f"[dim]Entities extracted: {result.get('entities_extracted', 0)}[/dim]"
                )
            else:
                console.print(
                    "[dim]Knowledge Graph not available - RAG-only mode[/dim]"
                )

            # Show chunk IDs if requested
            if show_chunk_ids and result.get("chunk_ids"):
                console.print(f"[dim]Chunk IDs: {result['chunk_ids']}[/dim]")

        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_ingest())


@ingest.command("directory")
@click.argument("path", type=click.Path(exists=True))
@click.option("--collection", required=True, help="Collection name")
@click.option(
    "--extensions", default=".txt,.md", help="Comma-separated file extensions"
)
@click.option("--recursive", is_flag=True, help="Search subdirectories")
@click.option(
    "--metadata", help="Additional metadata as JSON string to apply to all files"
)
@click.option("--mode", type=click.Choice(["ingest", "reingest"]), default="ingest",
              help="ingest=new (error if exists), reingest=replace existing")
@click.option("--topic", help="Topic for relevance scoring (optional)")
@click.option("--reviewed", is_flag=True, help="Mark all files as human-reviewed")
@click.option("--show-document-ids", is_flag=True, help="Display generated document IDs")
def ingest_directory(path, collection, extensions, recursive, metadata, mode, topic, reviewed, show_document_ids):
    """Ingest all files from a directory with automatic chunking.

    Routes through unified mediator to update both RAG store and Knowledge Graph.
    Falls back to RAG-only mode if Knowledge Graph unavailable.

    Examples:
        rag ingest directory /docs --collection my-docs --extensions ".md,.txt"

        # Recursive with reingest mode
        rag ingest directory /docs --collection my-docs --recursive --mode reingest

        # With topic for relevance scoring
        rag ingest directory /api-docs --collection docs --topic "REST APIs"
    """

    async def run_ingest():
        try:
            from src.mcp.tools import ingest_directory_impl

            # Parse metadata if provided
            metadata_dict = json.loads(metadata) if metadata else None

            ext_list = [ext.strip() for ext in extensions.split(",")]

            console.print(
                f"[bold blue]Ingesting files from: {path} (extensions: {ext_list})[/bold blue]"
            )
            if mode == "reingest":
                console.print(f"[dim]Mode: reingest (will replace existing)[/dim]")
            if topic:
                console.print(f"[dim]Topic: {topic}[/dim]")
            if reviewed:
                console.print(f"[dim]Marked as: human-reviewed[/dim]")
            if metadata_dict:
                console.print(f"[dim]Applying metadata: {metadata}[/dim]")

            # Initialize all components
            db = get_database()
            embedder = get_embedding_generator()
            coll_mgr = get_collection_manager(db)
            doc_store = get_document_store(db, embedder, coll_mgr)

            # Initialize Knowledge Graph components (lazy initialization within async context)
            local_graph_store, local_unified_mediator = (
                await initialize_graph_components()
            )

            # Call the same implementation as MCP tool for full feature parity
            result = await ingest_directory_impl(
                db=db,
                doc_store=doc_store,
                unified_mediator=local_unified_mediator,
                graph_store=local_graph_store,
                directory_path=path,
                collection_name=collection,
                file_extensions=ext_list,
                recursive=recursive,
                metadata=metadata_dict,
                include_document_ids=show_document_ids,
                mode=mode,
                topic=topic,
                reviewed_by_human=reviewed,
                actor_type="user",  # CLI is always user-operated
            )

            # Display results
            console.print(
                f"[bold green]✓ Ingested {result['files_ingested']} files with {result['total_chunks']} total chunks to collection '{collection}'[/bold green]"
            )

            # Show evaluation summary if available
            if "evaluation_summary" in result and result["evaluation_summary"]:
                eval_summary = result["evaluation_summary"]
                if eval_summary.get("avg_quality_score") is not None:
                    console.print(f"[dim]Avg quality score: {eval_summary['avg_quality_score']:.2f}[/dim]")
                if eval_summary.get("avg_topic_relevance") is not None:
                    console.print(f"[dim]Avg topic relevance: {eval_summary['avg_topic_relevance']:.2f}[/dim]")

            if result.get("files_failed", 0) > 0:
                console.print(f"[yellow]Files failed: {result['files_failed']}[/yellow]")
                for failed in result.get("failed_files", []):
                    console.print(f"  [red]✗ {failed}[/red]")

            if local_unified_mediator:
                console.print(f"[dim]Knowledge Graph integration active[/dim]")
            else:
                console.print(
                    "[dim]Knowledge Graph not available - RAG-only mode[/dim]"
                )

            # Show document IDs if requested
            if show_document_ids and result.get("document_ids"):
                console.print(f"[dim]Document IDs: {result['document_ids']}[/dim]")

        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_ingest())


@ingest.command("url")
@click.argument("url")
@click.option("--collection", required=True, help="Collection name")
@click.option(
    "--mode",
    type=click.Choice(["ingest", "reingest", "crawl", "recrawl"], case_sensitive=False),
    default="ingest",
    help="ingest/reingest (preferred) or crawl/recrawl (deprecated). Fresh vs update mode.",
)
@click.option(
    "--headless/--no-headless", default=True, help="Run browser in headless mode"
)
@click.option("--verbose", is_flag=True, help="Enable verbose crawling output")
@click.option(
    "--chunk-size",
    type=int,
    default=2500,
    help="Chunk size for web pages (default: 2500)",
)
@click.option(
    "--chunk-overlap", type=int, default=300, help="Chunk overlap (default: 300)"
)
@click.option("--follow-links", is_flag=True, help="Follow internal links (multi-page crawl)")
@click.option(
    "--max-depth",
    type=int,
    default=1,
    help="Maximum crawl depth when following links (default: 1)",
)
@click.option(
    "--max-pages",
    type=int,
    default=10,
    help="Maximum pages to crawl when following links (default: 10, max: 20)",
)
@click.option(
    "--metadata", help="Additional metadata as JSON string to apply to all pages"
)
@click.option(
    "--dry-run", is_flag=True, help="Preview pages and score relevance without ingesting"
)
@click.option(
    "--topic", help="Topic to score relevance against (required with --dry-run)"
)
@click.option("--reviewed", is_flag=True, help="Mark all pages as human-reviewed")
@click.option("--show-document-ids", is_flag=True, help="Display generated document IDs")
def ingest_url(
    url,
    collection,
    mode,
    headless,
    verbose,
    chunk_size,
    chunk_overlap,
    follow_links,
    max_depth,
    max_pages,
    metadata,
    dry_run,
    topic,
    reviewed,
    show_document_ids,
):
    """Crawl and ingest a web page with automatic chunking.

    Routes through unified mediator to update both RAG store and Knowledge Graph.
    Falls back to RAG-only mode if Knowledge Graph unavailable.

    By default, only the specified page is crawled. Use --follow-links to crawl
    linked pages up to --max-depth levels deep (limited by --max-pages).

    Use --mode reingest to find and delete existing documents from previous crawls
    of the same URL before re-ingesting.

    Use --dry-run with --topic to preview pages and get relevance scores before
    ingesting. This helps filter out irrelevant pages.

    Examples:
        # Single page only
        rag ingest url https://example.com --collection docs

        # Re-ingest (delete old, then ingest fresh)
        rag ingest url https://example.com --collection docs --mode reingest

        # Follow direct links (depth=1)
        rag ingest url https://example.com --collection docs --follow-links

        # Follow links with max pages limit
        rag ingest url https://example.com --collection docs --follow-links --max-pages 15

        # Dry run - preview pages and score relevance
        rag ingest url https://docs.example.com --collection docs \\
          --follow-links --max-pages 20 --dry-run --topic "authentication and OAuth"

        # Mark pages as human-reviewed
        rag ingest url https://example.com --collection docs --reviewed
    """

    async def run_ingest():
        try:
            # Normalize mode: convert deprecated crawl/recrawl to ingest/reingest
            normalized_mode = mode.lower()
            if normalized_mode in ("crawl", "recrawl"):
                console.print(f"[yellow]Warning: '{mode}' is deprecated. Use '{'ingest' if normalized_mode == 'crawl' else 'reingest'}' instead.[/yellow]")
                normalized_mode = "ingest" if normalized_mode == "crawl" else "reingest"

            # Parse metadata if provided
            metadata_dict = json.loads(metadata) if metadata else None
            if metadata_dict:
                console.print(f"[dim]Applying metadata: {metadata}[/dim]")
            if reviewed:
                console.print(f"[dim]Marked as: human-reviewed[/dim]")

            # Validate dry_run parameters
            if dry_run and not topic:
                console.print("[bold red]Error: --topic is required when using --dry-run[/bold red]")
                console.print("[dim]Example: --dry-run --topic 'authentication and OAuth'[/dim]")
                sys.exit(1)

            # Validate max_pages
            if max_pages < 1 or max_pages > 20:
                console.print(f"[bold red]Error: --max-pages must be between 1 and 20 (got {max_pages})[/bold red]")
                sys.exit(1)

            # ========================================================================
            # DRY RUN MODE: Crawl and score without ingesting
            # ========================================================================
            if dry_run:
                from rich.table import Table
                from src.mcp.tools import score_page_relevance

                console.print(f"[bold blue]Dry run: Crawling {url}[/bold blue]")
                console.print(f"[dim]Topic: {topic}[/dim]")

                # Crawl pages
                if follow_links:
                    console.print(f"[dim]Following links (max {max_pages} pages)...[/dim]")
                    crawler = WebCrawler(headless=headless, verbose=verbose)
                    results = await crawler.crawl_with_depth(url, max_depth=max_depth, max_pages=max_pages)
                else:
                    result = await crawl_single_page(url, headless=headless, verbose=verbose)
                    results = [result] if result.success else []

                if not results:
                    console.print(f"[bold red]✗ No pages crawled from {url}[/bold red]")
                    sys.exit(1)

                successful_results = [r for r in results if r.success]
                console.print(f"[green]✓ Crawled {len(successful_results)} pages[/green]")
                console.print(f"[dim]Scoring relevance...[/dim]")

                # Prepare pages for scoring
                pages_to_score = []
                for result in successful_results:
                    pages_to_score.append({
                        "url": result.url,
                        "title": result.metadata.get("title", result.url),
                        "content": result.content,
                    })

                # Score relevance using same function as MCP
                scored_pages = await score_page_relevance(pages_to_score, topic)

                # Calculate summary stats
                ingest_count = sum(1 for p in scored_pages if p["recommendation"] == "ingest")
                review_count = sum(1 for p in scored_pages if p["recommendation"] == "review")
                skip_count = sum(1 for p in scored_pages if p["recommendation"] == "skip")

                # Display results in a table
                console.print()
                table = Table(title=f"Relevance Scores for: {topic}")
                table.add_column("Score", justify="right", style="cyan", width=6)
                table.add_column("Rec", justify="center", width=8)
                table.add_column("Title", style="white", max_width=50)
                table.add_column("Summary", style="dim", max_width=40)

                for page in scored_pages:
                    score = page["relevance_score"]
                    rec = page["recommendation"]

                    # Color-code recommendation
                    if rec == "ingest":
                        rec_style = "[green]ingest[/green]"
                    elif rec == "review":
                        rec_style = "[yellow]review[/yellow]"
                    else:
                        rec_style = "[red]skip[/red]"

                    table.add_row(
                        f"{score:.2f}",
                        rec_style,
                        page["title"][:50],
                        page["relevance_summary"][:40] if page.get("relevance_summary") else "",
                    )

                console.print(table)

                # Summary
                console.print()
                console.print(f"[bold]Summary:[/bold]")
                console.print(f"  [green]Ingest:[/green] {ingest_count} pages (score >= 0.50)")
                console.print(f"  [yellow]Review:[/yellow] {review_count} pages (score 0.40-0.49)")
                console.print(f"  [red]Skip:[/red] {skip_count} pages (score < 0.40)")
                console.print()
                console.print("[dim]To ingest recommended pages, run without --dry-run[/dim]")

                return  # Exit early - don't proceed to actual ingestion

            # Handle reingest mode: delete old documents first
            if normalized_mode == "reingest":
                console.print(f"[bold blue]Re-ingesting: {url}[/bold blue]")
                console.print(
                    f"[dim]Finding existing documents with crawl_root_url = {url}...[/dim]"
                )

                # Step 1: Find all source documents with matching crawl_root_url
                db = get_database()
                conn = db.connect()
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, filename, metadata
                        FROM source_documents
                        WHERE metadata->>'crawl_root_url' = %s
                        """,
                        (url,),
                    )
                    existing_docs = cur.fetchall()

                if not existing_docs:
                    console.print(
                        f"[yellow]No existing documents found with crawl_root_url = {url}[/yellow]"
                    )
                    console.print("[dim]Proceeding with fresh crawl...[/dim]")
                    old_doc_count = 0
                else:
                    old_doc_count = len(existing_docs)
                    console.print(
                        f"[yellow]Found {old_doc_count} existing documents to delete[/yellow]"
                    )

                    # Step 2: Delete the old documents and their chunks
                    embedder = get_embedding_generator()
                    coll_mgr = get_collection_manager(db)
                    web_chunking_config = ChunkingConfig(
                        chunk_size=chunk_size, chunk_overlap=chunk_overlap
                    )
                    web_chunker = get_document_chunker(web_chunking_config)
                    web_doc_store = get_document_store(
                        db, embedder, coll_mgr, chunker=web_chunker
                    )

                    for doc_id, filename, doc_metadata in existing_docs:
                        try:
                            # Get chunk count before deletion
                            chunks = web_doc_store.get_document_chunks(doc_id)
                            chunk_count = len(chunks)

                            # Delete the document (cascades to chunks and chunk_collections)
                            with conn.cursor() as cur:
                                # Delete chunks first
                                cur.execute(
                                    "DELETE FROM document_chunks WHERE source_document_id = %s",
                                    (doc_id,),
                                )
                                # Delete source document
                                cur.execute(
                                    "DELETE FROM source_documents WHERE id = %s",
                                    (doc_id,),
                                )

                            console.print(
                                f"  [dim]✓ Deleted document {doc_id}: {filename} ({chunk_count} chunks)[/dim]"
                            )
                        except Exception as e:
                            console.print(
                                f"  [red]✗ Failed to delete document {doc_id}: {e}[/red]"
                            )

                console.print(f"\n[bold blue]Starting crawl...[/bold blue]")
            else:
                old_doc_count = 0
                console.print(f"[bold blue]Crawling URL: {url}[/bold blue]")

            # Initialize Knowledge Graph components (lazy initialization within async context)
            local_graph_store, local_unified_mediator = (
                await initialize_graph_components()
            )

            if follow_links:
                # Multi-page crawl with link following
                if normalized_mode != "reingest":
                    console.print(
                        f"[bold blue]Crawling URL with link following: {url} (max_depth={max_depth}, max_pages={max_pages})[/bold blue]"
                    )

                crawler = WebCrawler(headless=headless, verbose=verbose)
                results = await crawler.crawl_with_depth(url, max_depth=max_depth, max_pages=max_pages)

                if not results:
                    console.print(
                        f"[bold red]✗ No pages crawled from {url}[/bold red]"
                    )
                    sys.exit(1)

                console.print(f"[green]✓ Crawled {len(results)} pages[/green]")

                # Ingest each page
                total_chunks = 0
                total_entities = 0
                successful_ingests = 0

                for i, result in enumerate(results, 1):
                    if not result.success:
                        console.print(
                            f"  [yellow]⚠ Skipped failed page {i}: {result.url}[/yellow]"
                        )
                        continue

                    try:
                        # Merge user metadata with page metadata
                        page_metadata = metadata_dict.copy() if metadata_dict else {}
                        page_metadata.update(result.metadata)

                        # Use unified mediator if available
                        if local_unified_mediator:
                            ingest_result = await local_unified_mediator.ingest_text(
                                content=result.content,
                                collection_name=collection,
                                document_title=result.metadata.get("title", result.url),
                                metadata=page_metadata,
                            )
                            total_chunks += ingest_result["num_chunks"]
                            total_entities += ingest_result.get("entities_extracted", 0)
                            successful_ingests += 1
                            console.print(
                                f"  ✓ Page {i}/{len(results)}: {result.metadata.get('title', result.url)[:50]}... "
                                f"({ingest_result['num_chunks']} chunks, {ingest_result.get('entities_extracted', 0)} entities, "
                                f"depth={result.metadata.get('crawl_depth', 0)})"
                            )

                        # Fallback: RAG-only mode
                        else:
                            db = get_database()
                            embedder = get_embedding_generator()
                            coll_mgr = get_collection_manager(db)
                            web_chunking_config = ChunkingConfig(
                                chunk_size=chunk_size, chunk_overlap=chunk_overlap
                            )
                            web_chunker = get_document_chunker(web_chunking_config)
                            web_doc_store = get_document_store(
                                db, embedder, coll_mgr, chunker=web_chunker
                            )

                            source_id, chunk_ids = web_doc_store.ingest_document(
                                content=result.content,
                                filename=result.metadata.get("title", result.url),
                                collection_name=collection,
                                metadata=page_metadata,
                                file_type="web_page",
                            )
                            total_chunks += len(chunk_ids)
                            successful_ingests += 1
                            console.print(
                                f"  ✓ Page {i}/{len(results)}: {result.metadata.get('title', result.url)[:50]}... "
                                f"({len(chunk_ids)} chunks, depth={result.metadata.get('crawl_depth', 0)})"
                            )

                    except Exception as e:
                        console.print(f"  [red]✗ Failed to ingest page {i}: {e}[/red]")

                if normalized_mode == "reingest":
                    console.print(f"\n[bold green]✓ Re-ingest complete![/bold green]")
                    console.print(
                        f"[bold]Deleted {old_doc_count} old pages, crawled {successful_ingests} new pages with {total_chunks} total chunks[/bold]"
                    )
                    console.print(f"[dim]Collection: '{collection}'[/dim]")
                else:
                    console.print(
                        f"\n[bold green]✓ Ingested {successful_ingests} pages with {total_chunks} total chunks "
                        f"to collection '{collection}'[/bold green]"
                    )
                if local_unified_mediator and total_entities > 0:
                    console.print(
                        f"[dim]Total entities extracted: {total_entities}[/dim]"
                    )
                elif not local_unified_mediator:
                    console.print(
                        "[dim]Knowledge Graph not available - RAG-only mode[/dim]"
                    )
                console.print(
                    f"[dim]Chunk size: {chunk_size} chars, Overlap: {chunk_overlap} chars[/dim]"
                )

            else:
                # Single-page crawl
                if normalized_mode != "reingest":
                    console.print(f"[bold blue]Crawling URL: {url}[/bold blue]")

                # Crawl the page
                result = await crawl_single_page(url, headless=headless, verbose=verbose)

                if not result.success:
                    console.print(f"[bold red]✗ Failed to crawl {url}[/bold red]")
                    if result.error:
                        console.print(
                            f"[bold red]Error: {result.error.error_message}[/bold red]"
                        )
                    sys.exit(1)

                console.print(
                    f"[green]✓ Successfully crawled page ({len(result.content)} chars)[/green]"
                )

                # Merge user metadata with page metadata
                page_metadata = metadata_dict.copy() if metadata_dict else {}
                page_metadata.update(result.metadata)

                # Use unified mediator if available
                if local_unified_mediator:
                    ingest_result = await local_unified_mediator.ingest_text(
                        content=result.content,
                        collection_name=collection,
                        document_title=result.metadata.get("title", url),
                        metadata=page_metadata,
                    )

                    if normalized_mode == "reingest":
                        console.print(f"\n[bold green]✓ Re-ingest complete![/bold green]")
                        console.print(
                            f"[bold]Deleted {old_doc_count} old pages, crawled 1 new page with {ingest_result['num_chunks']} chunks[/bold]"
                        )
                        console.print(f"[dim]Collection: '{collection}'[/dim]")
                        console.print(
                            f"[dim]Entities extracted: {ingest_result.get('entities_extracted', 0)}[/dim]"
                        )
                    else:
                        console.print(
                            f"[bold green]✓ Ingested web page (ID: {ingest_result['source_document_id']}) "
                            f"with {ingest_result['num_chunks']} chunks to collection '{collection}'[/bold green]"
                        )
                        console.print(
                            f"[dim]Entities extracted: {ingest_result.get('entities_extracted', 0)}[/dim]"
                        )
                    console.print(
                        f"[dim]Title: {result.metadata.get('title', 'N/A')}[/dim]"
                    )
                    console.print(
                        f"[dim]Domain: {result.metadata.get('domain', 'N/A')}[/dim]"
                    )

                # Fallback: RAG-only mode
                else:
                    db = get_database()
                    embedder = get_embedding_generator()
                    coll_mgr = get_collection_manager(db)
                    web_chunking_config = ChunkingConfig(
                        chunk_size=chunk_size, chunk_overlap=chunk_overlap
                    )
                    web_chunker = get_document_chunker(web_chunking_config)
                    web_doc_store = get_document_store(
                        db, embedder, coll_mgr, chunker=web_chunker
                    )

                    source_id, chunk_ids = web_doc_store.ingest_document(
                        content=result.content,
                        filename=result.metadata.get("title", url),
                        collection_name=collection,
                        metadata=page_metadata,
                        file_type="web_page",
                    )

                    if normalized_mode == "reingest":
                        console.print(f"\n[bold green]✓ Re-ingest complete![/bold green]")
                        console.print(
                            f"[bold]Deleted {old_doc_count} old pages, crawled 1 new page with {len(chunk_ids)} chunks[/bold]"
                        )
                        console.print(f"[dim]Collection: '{collection}'[/dim]")
                    else:
                        console.print(
                            f"[bold green]✓ Ingested web page (ID: {source_id}) with {len(chunk_ids)} chunks to collection '{collection}'[/bold green]"
                        )
                    console.print(
                        "[dim]Knowledge Graph not available - RAG-only mode[/dim]"
                    )
                    console.print(
                        f"[dim]Title: {result.metadata.get('title', 'N/A')}[/dim]"
                    )
                    console.print(
                        f"[dim]Domain: {result.metadata.get('domain', 'N/A')}[/dim]"
                    )
                    console.print(
                        f"[dim]Chunk size: {chunk_size} chars, Overlap: {chunk_overlap} chars[/dim]"
                    )

        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_ingest())


@ingest.command("list-dir")
@click.argument("path", type=click.Path(exists=True))
@click.option("--extensions", help="Comma-separated file extensions (e.g., '.md,.txt')")
@click.option("--recursive", is_flag=True, help="Search subdirectories")
@click.option("--preview", is_flag=True, help="Show content preview for text files")
@click.option("--preview-chars", default=500, type=int, help="Preview length in characters (default: 500)")
@click.option("--max-files", default=100, type=int, help="Maximum files to list (default: 100)")
def ingest_list_dir(path, extensions, recursive, preview, preview_chars, max_files):
    """List directory contents before ingesting.

    Use this to explore and assess directory contents before deciding what to ingest.
    This is a READ-ONLY operation that does not modify any data.

    Examples:
        # List all files in a directory
        rag ingest list-dir /path/to/docs

        # Filter by extensions
        rag ingest list-dir /path/to/docs --extensions ".md,.txt"

        # Recursive search with previews
        rag ingest list-dir /path/to/docs --recursive --preview

        # Limit results
        rag ingest list-dir /path/to/docs --max-files 50
    """
    from rich.table import Table
    from src.mcp.tools import list_directory_impl

    # Parse extensions if provided
    ext_list = None
    if extensions:
        ext_list = [ext.strip() for ext in extensions.split(",")]

    console.print(f"[bold blue]Listing directory: {path}[/bold blue]")
    if ext_list:
        console.print(f"[dim]Extensions filter: {ext_list}[/dim]")
    if recursive:
        console.print(f"[dim]Recursive: yes[/dim]")

    try:
        result = list_directory_impl(
            directory_path=path,
            file_extensions=ext_list,
            recursive=recursive,
            include_preview=preview,
            preview_chars=preview_chars,
            max_files=max_files,
        )

        if result.get("status") == "error":
            console.print(f"[bold red]Error: {result.get('error', 'Unknown error')}[/bold red]")
            sys.exit(1)

        files = result.get("files", [])

        if not files:
            console.print("[yellow]No files found matching criteria[/yellow]")
            return

        # Display results in a table
        table = Table(title=f"Files in {path}")
        table.add_column("Filename", style="white", max_width=40)
        table.add_column("Ext", style="cyan", width=6)
        table.add_column("Size", justify="right", style="green", width=10)
        table.add_column("Modified", style="dim", width=20)

        if preview:
            table.add_column("Preview", style="dim", max_width=50)

        for f in files:
            row = [
                f["filename"][:40],
                f.get("extension", ""),
                f.get("size_human", ""),
                f.get("modified", "")[:19] if f.get("modified") else "",
            ]
            if preview:
                preview_text = f.get("preview", "")[:50]
                if len(f.get("preview", "")) > 50:
                    preview_text += "..."
                row.append(preview_text)
            table.add_row(*row)

        console.print(table)

        # Summary
        console.print()
        console.print(f"[bold]Total: {result['total_files_found']} files found[/bold]")
        if result.get("truncated"):
            console.print(f"[yellow]Results truncated to {max_files} files. Use --max-files to see more.[/yellow]")

        # Extension breakdown
        ext_summary = result.get("extensions_found", {})
        if ext_summary:
            ext_str = ", ".join([f"{ext}: {count}" for ext, count in ext_summary.items()])
            console.print(f"[dim]Extensions: {ext_str}[/dim]")

        console.print()
        console.print("[dim]Use 'rag ingest file <path>' or 'rag ingest directory <path>' to ingest[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
