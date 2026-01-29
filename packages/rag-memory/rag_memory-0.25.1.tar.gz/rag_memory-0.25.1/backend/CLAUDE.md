# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Note:** The root `/CLAUDE.md` contains project-wide rules. This file covers backend-specific patterns.

## Quick Reference

```bash
# Run the backend server
uvicorn app.main:app --reload --port 8000

# Run from project root (if dependencies are in root pyproject.toml)
cd backend && uvicorn app.main:app --reload

# Backend-specific database migrations (separate from root MCP migrations)
cd backend
alembic upgrade head           # Apply pending migrations
alembic revision -m "desc"     # Create new migration
alembic current                # Show current revision
```

## Architecture Overview

The backend is a **stateful chat interface** that wraps the RAG Memory MCP server with:
- FastAPI REST API + SSE streaming
- LangGraph ReAct agent with 20 tools (17 MCP + 3 Python)
- Conversation persistence in its own PostgreSQL database

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend (this directory)                                        │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ FastAPI Routes │  │ LangGraph Agent  │  │ SSE Streaming   │  │
│  │ /api/chat/*    │──│ (ReAct pattern)  │──│ (chat_bridge)   │  │
│  │ /api/rag-*     │  │ 17 MCP + 3 local │  │                 │  │
│  └────────────────┘  └──────────────────┘  └─────────────────┘  │
│           │                    │                                 │
│           ▼                    ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Web App Database (conversations, messages, checkpoints)     ││
│  │ postgresql+asyncpg://...                                    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (via mcp.json config)
┌─────────────────────────────────────────────────────────────────┐
│  RAG Memory MCP Server (http://localhost:18000/mcp)             │
│  (Documents, vectors, knowledge graph - separate database)      │
└─────────────────────────────────────────────────────────────────┘
```

## Two-Database Architecture

The backend uses a **separate database** from the RAG Memory MCP server:

| Database | Purpose | Connection |
|----------|---------|------------|
| Web App DB | conversations, messages, starter_prompts, LangGraph checkpoints | `DATABASE_URL` in `.env` |
| RAG Memory DB | documents, vectors, collections, knowledge graph | Accessed via MCP protocol |

**Critical:** Backend migrations (`backend/alembic/`) are separate from MCP server migrations (`deploy/alembic/`).

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI entry point, routers, CORS |
| `app/rag_agent/agent.py` | LangGraph ReAct agent creation |
| `app/shared/chat_bridge.py` | SSE streaming from agent to frontend |
| `app/tools/search_tools.py` | Python tools: web_search, validate_url, fetch_url |
| `app/rag/mcp_proxy.py` | Proxy routes to RAG Memory MCP server |
| `mcp.json` | MCP server connection config |

## Agent Tool Stack

The ReAct agent has 20 tools:

**MCP Tools (17)** - from RAG Memory server:
- Collection: list_collections, create_collection, delete_collection, get_collection_info
- Search: search_documents, query_relationships, query_temporal
- Ingest: ingest_text, ingest_url, ingest_file, ingest_directory, analyze_website
- Document: get_document_by_id, list_documents, update_document, delete_document

**Python Tools (3)** - local to backend:
- `web_search()` - Google (primary) or DuckDuckGo (fallback)
- `validate_url()` - HEAD request to check URL accessibility
- `fetch_url()` - Extract main content using trafilatura

## SSE Event Types

`chat_bridge.py` emits these events to the frontend:

| Event | When |
|-------|------|
| `token` | Text chunks from agent (75-char chunks) |
| `tool_start` | Agent calling a tool |
| `tool_end` | Tool execution completed |
| `search_results` | Result from search_documents |
| `web_search_results` | Result from web_search |
| `knowledge_graph` | Result from query_relationships |
| `temporal_data` | Result from query_temporal |
| `document_selected` | Result from get_document_by_id |
| `done` | Stream complete |
| `error` | Error occurred |

## Code Patterns

### Adding Python Tools

Add in `app/tools/search_tools.py`:

```python
@tool
async def my_tool(param: str) -> dict:
    """Tool description for LLM."""
    # Implementation
    return {"result": "..."}
```

Then add to agent in `app/rag_agent/agent.py`:
```python
from ..tools import web_search, validate_url, fetch_url, my_tool
python_tools = [web_search, validate_url, fetch_url, my_tool]
```

### Database Async Pattern

Always use async sessions:

```python
from ..database import async_session_maker

async with async_session_maker() as db:
    result = await db.execute(query)
    await db.commit()
```

### Rate Limiting

Python tools use `RateLimiter` class for HTTP requests:

```python
from ..tools.search_tools import RateLimiter

rate_limiter = RateLimiter(requests_per_second=1.0)
await rate_limiter.wait()  # Blocks if needed
# Make request
```

## Configuration

Key environment variables (`.env`):

| Variable | Notes |
|----------|-------|
| `LLM_MODEL` | Default: `gpt-5-mini` (NOT gpt-4o-mini) |
| `LLM_TEMPERATURE` | Must be 1.0 for GPT-5 series |
| `DATABASE_URL` | Must use `postgresql+asyncpg://` (async driver) |
| `MCP_CONFIG_PATH` | Path to mcp.json (default: `mcp.json`) |

## Known Quirks

**MCP Server Must Be Running:** Agent creation fails if RAG Memory MCP server isn't running at URL in `mcp.json`.

**LangGraph Checkpointer:** Uses psycopg (NOT asyncpg) for the checkpointer. The checkpointer connection pool is separate from SQLAlchemy sessions.

**Thread ID Format:** Conversations are keyed as `chat_{conversation_id}` for LangGraph state persistence.

## Debugging

```bash
# Check backend logs
uvicorn app.main:app --reload --log-level debug

# Test MCP connection
curl http://localhost:18000/mcp  # Should return MCP response

# Manual endpoint tests
python test_endpoints.py
```
