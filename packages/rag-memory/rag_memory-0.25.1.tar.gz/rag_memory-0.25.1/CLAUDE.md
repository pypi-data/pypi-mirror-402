# CLAUDE.md

This file provides guidance to Claude Code when working with RAG Memory.

## Keep This File Accurate

**IMPORTANT:** If you notice anything in this file is outdated, inaccurate, or missing - recommend an update and ask permission to fix it. This includes:

- Commands that no longer work or have changed
- File paths or project structure that has changed
- Rules that no longer apply
- New patterns or quirks discovered during development

Don't wait to be asked. Proactively flag when this file needs updating.

---

## Critical Rules

### Ask Permission Before Touching Services

The user runs a multi-instance setup with 4 PostgreSQL containers managed by custom scripts (`setup.py`, `update_mcp.py`). **Ask permission before running:**

- `docker restart`, `docker stop`, `docker start`, `docker run`
- `docker compose up`, `docker compose down`, `docker compose restart`
- `uv run rag start`, `uv run rag stop`, `uv run rag restart`
- `docker build`, `docker compose build`
- Any command that kills or modifies running processes

**After code changes that need a restart:** Tell the user what changed, tell them they need to restart, then wait for them to do it.

### Ask Permission Before Installing Dependencies

**Ask before running:** `uv add`, `pip install`, `npm install`, or modifying `pyproject.toml` dependencies.

### Database Migration Rules

**IMPORTANT:** Never modify an already-applied migration. Alembic tracks applied revisions - editing them has no effect.

```bash
# Check migration status across all instances
uv run python scripts/db_migrate.py status

# Create new migration (always create new, never edit existing)
uv run python scripts/db_migrate.py create "description_here"

# Apply migrations to all 4 database instances
uv run python scripts/db_migrate.py apply
```

The user has 4 PostgreSQL instances on ports 54320, 54321, 54322, 54323. The `db_migrate.py` script handles all of them.

### MCP Tool Parameter Types

MCP tool parameters must NOT use `Optional[T]` type hints. This is absolute - MCP/Pydantic rejects them.

```python
# Correct
@mcp.tool()
def my_tool(param: str = None): ...

# Wrong - will fail validation
@mcp.tool()
def my_tool(param: Optional[str] = None): ...
```

---

## Quick Reference

```bash
# Development
uv sync                                       # Install dependencies
uv run pytest                                 # Run tests
uv run pytest mcp-server/tests/unit/          # Unit tests only
uv run black mcp-server/src/ mcp-server/tests/    # Format code
uv run ruff check mcp-server/src/ mcp-server/tests/  # Lint

# MCP Server
uv run rag-mcp-stdio                 # For Claude Desktop/Cursor
uv run rag-mcp-sse                   # For MCP Inspector (localhost:3001)

# Database
uv run python scripts/db_migrate.py status   # Check all instances
uv run python scripts/db_migrate.py apply    # Apply pending migrations
```

---

## Project Structure

```
mcp-server/
├── src/
│   ├── mcp/
│   │   ├── server.py          # MCP entry point, @mcp.tool() wrappers
│   │   ├── tools.py           # Tool implementations (*_impl functions)
│   │   └── evaluation.py      # LLM content evaluation
│   ├── unified/
│   │   ├── mediator.py        # Orchestrates RAG + Graph writes
│   │   └── graph_store.py     # Neo4j/Graphiti interface
│   ├── ingestion/
│   │   ├── document_store.py  # PostgreSQL document storage
│   │   └── web_crawler.py     # Crawl4AI-based crawler
│   ├── retrieval/
│   │   └── search.py          # Vector similarity search
│   └── cli_commands/          # CLI command groups
└── tests/                     # Test suite (unit + integration)

deploy/
├── alembic/versions/      # Database migrations (never edit applied ones)
└── docker/init.sql        # Fresh install schema

scripts/
└── db_migrate.py          # Multi-instance migration tool
```

---

## Architecture

**Dual Storage:**
- PostgreSQL + pgvector for semantic search (RAG layer)
- Neo4j + Graphiti for knowledge graphs

**Unified Ingestion:** `UnifiedIngestionMediator` writes to RAG first, then Graph. Not atomic - second write can fail leaving inconsistent state.

**Evaluation System:** Every ingest runs LLM evaluation:
- `quality_score` / `quality_summary` - Always populated
- `topic_relevance_score` / `topic_relevance_summary` / `topic_provided` - Only when caller provides topic

**Multi-Instance:** Each instance has isolated PostgreSQL, Neo4j, MCP server on different ports.

---

## Code Patterns

### Adding MCP Tools
1. Add `new_tool_impl()` in `mcp-server/src/mcp/tools.py`
2. Add `@mcp.tool()` wrapper in `mcp-server/src/mcp/server.py`
3. No `Optional[T]` in parameters

### Modifying Schema
1. `uv run python scripts/db_migrate.py create "description"`
2. Edit the new migration file in `deploy/alembic/versions/`
3. `uv run python scripts/db_migrate.py apply`

### Crawl Modes
- `mode="ingest"` - New content, errors if URL exists
- `mode="reingest"` - Update existing, deletes old first

---

## Known Quirks

**Graphiti orphan bug:** Deleting a collection from PostgreSQL doesn't clean up Neo4j entities/episodes. Manual cleanup required.

**Forked Crawl4AI:** We maintain a fork with custom fixes.

**Config priority:** Environment vars > `.env` file > system config (`~/.config/rag-memory/config.yaml`)

---

## Debugging

```bash
# PostgreSQL
docker exec -it rag-memory-mcp-postgres-primary psql -U raguser -d rag_memory
SELECT COUNT(*) FROM source_documents;

# Neo4j browser
open http://localhost:7474
MATCH (n) RETURN count(n);

# MCP logs
tail -f logs/mcp_server.log
```

**Common fixes:**
- "Database not found" → Check `.env` has `DATABASE_URL`
- "Neo4j connection failed" → Service not running
- MCP parameter errors → Check for `Optional[T]` type hints
