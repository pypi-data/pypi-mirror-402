"""Search commands."""

import json
import sys

import click
from rich.console import Console

from src.core.collections import get_collection_manager
from src.core.database import get_database
from src.core.embeddings import get_embedding_generator
from src.retrieval.search import get_similarity_search

console = Console()


@click.command(name='search')
@click.argument("query")
@click.option("--collection", help="Search within specific collection")
@click.option("--limit", default=10, help="Maximum number of results")
@click.option("--threshold", type=float, help="Minimum similarity score (0-1)")
@click.option("--metadata", help="Filter by metadata (JSON string)")
@click.option("--verbose", is_flag=True, help="Show full chunk content")
@click.option("--show-source", is_flag=True, help="Include full source document content")
@click.option("--include-metadata", is_flag=True, help="Include chunk_id, chunk_index, char positions in output")
@click.option("--reviewed-only", is_flag=True, help="Only return results from human-reviewed documents")
@click.option("--unreviewed-only", is_flag=True, help="Only return results from unreviewed documents")
@click.option("--min-quality", type=float, help="Minimum quality score (0.0-1.0)")
@click.option("--min-topic-relevance", type=float, help="Minimum topic relevance score (0.0-1.0)")
def search(query, collection, limit, threshold, metadata, verbose, show_source,
           include_metadata, reviewed_only, unreviewed_only, min_quality, min_topic_relevance):
    """Search for similar document chunks."""
    try:
        # Validate mutually exclusive options
        if reviewed_only and unreviewed_only:
            console.print("[bold red]Error: --reviewed-only and --unreviewed-only are mutually exclusive[/bold red]")
            sys.exit(1)

        db = get_database()
        embedder = get_embedding_generator()
        coll_mgr = get_collection_manager(db)

        # Create searcher using baseline vector-only search
        searcher = get_similarity_search(db, embedder, coll_mgr)

        # Parse metadata filter if provided
        metadata_filter = None
        if metadata:
            try:
                metadata_filter = json.loads(metadata)
            except json.JSONDecodeError as e:
                console.print(f"[bold red]Invalid JSON in metadata filter: {e}[/bold red]")
                sys.exit(1)

        # Determine reviewed_by_human filter
        reviewed_by_human = None
        if reviewed_only:
            reviewed_by_human = True
        elif unreviewed_only:
            reviewed_by_human = False

        console.print(f"[bold blue]Searching for: {query}[/bold blue]")
        if metadata_filter:
            console.print(f"[dim]Metadata filter: {metadata_filter}[/dim]")
        if reviewed_by_human is not None:
            console.print(f"[dim]Reviewed filter: {'reviewed only' if reviewed_by_human else 'unreviewed only'}[/dim]")
        if min_quality:
            console.print(f"[dim]Min quality: {min_quality}[/dim]")
        if min_topic_relevance:
            console.print(f"[dim]Min topic relevance: {min_topic_relevance}[/dim]")

        # Execute vector-only search
        results = searcher.search_chunks(
            query, limit, threshold, collection,
            include_source=show_source,
            metadata_filter=metadata_filter,
            reviewed_by_human=reviewed_by_human,
            min_quality_score=min_quality,
            min_topic_relevance=min_topic_relevance
        )

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        console.print(f"\n[bold green]Found {len(results)} results:[/bold green]\n")

        for i, result in enumerate(results, 1):
            console.print(f"[bold cyan]Result {i}:[/bold cyan]")
            console.print(f"  Chunk ID: {result.chunk_id}")
            console.print(f"  Source: {result.source_filename} (Doc ID: {result.source_document_id})")
            console.print(f"  Chunk: {result.chunk_index + 1}")
            console.print(
                f"  Similarity: [bold green]{result.similarity:.4f}[/bold green]"
            )
            console.print(f"  Position: chars {result.char_start}-{result.char_end}")

            # Show evaluation metadata if requested
            if include_metadata:
                reviewed = getattr(result, 'reviewed_by_human', None)
                quality = getattr(result, 'quality_score', None)
                topic_rel = getattr(result, 'topic_relevance_score', None)
                if reviewed is not None:
                    status = "[green]✓ reviewed[/green]" if reviewed else "[dim]unreviewed[/dim]"
                    console.print(f"  Review status: {status}")
                if quality is not None:
                    console.print(f"  Quality score: {quality:.2f}")
                if topic_rel is not None:
                    console.print(f"  Topic relevance: {topic_rel:.2f}")

            if verbose:
                console.print(f"  Content:\n{result.content}")
                if result.metadata:
                    console.print(f"  Metadata: {json.dumps(result.metadata, indent=2)}")
                if show_source and result.source_content:
                    console.print(f"  [dim]Full Source ({len(result.source_content)} chars)[/dim]")
            else:
                preview_len = 150 if show_source else 100
                console.print(f"  Preview: {result.content[:preview_len]}...")

            console.print()

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)
