# RAG Memory Web Interface

React + FastAPI web application for managing RAG Memory knowledge base through a conversational interface.

## Prerequisites

1. **Node.js 18+** for frontend
2. **Python 3.11+** with uv package manager
3. **Docker** for PostgreSQL and Neo4j containers
4. **OpenAI API Key** (required for LLM and embeddings)

## Quick Start

### 1. Configure API Key

```bash
# Edit backend/.env and add your OpenAI API key
# The file already exists with a placeholder
nano backend/.env

# Replace this line:
# OPENAI_API_KEY=your-openai-api-key-here

# With your actual key:
# OPENAI_API_KEY=sk-...
```

### 2. Start All Services (Recommended)

```bash
# From rag-memory root directory
python manage.py start
```

This single command:
- Starts RAG Memory Docker services (PostgreSQL + Neo4j)
- Starts Web App Docker service (PostgreSQL for checkpointing)
- Starts RAG Memory MCP server on port 3001
- Starts Backend FastAPI on port 8000
- Starts Frontend Vite on port 5173

**Access:** http://localhost:5173

### 3. Manage Services

```bash
# Check status
python manage.py status

# View logs
python manage.py logs

# Restart all services
python manage.py restart

# Stop all services
python manage.py stop
```

## Manual Setup (Alternative)

If you prefer to start services individually:

### 1. Start RAG Memory Services

```bash
uv run rag start  # PostgreSQL + Neo4j
```

### 2. Start Web App Database

```bash
docker-compose -f docker-compose.web.yml up -d
```

### 3. Start MCP Server

```bash
uv run rag-mcp-http  # Port 3001
```

### 4. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 5. Start Frontend

```bash
cd frontend
npm run dev
```

## Architecture

```
React Frontend (port 5173)
    ↓ SSE streaming + REST API
FastAPI Backend (port 8000)
    ↓ MultiServerMCPClient
RAG Memory MCP Server (port 3001)
    ↓
PostgreSQL + Neo4j (RAG Memory databases)
```

**Two PostgreSQL databases:**
1. RAG Memory database (port 5432) - Knowledge storage
2. Web app database (port 5433) - Conversation persistence

## Key Features

- **Conversational Interface**: Chat-based interaction with 20 MCP tools
- **ReAct Agent**: LLM dynamically chooses tools based on user intent
- **Web Search Integration**: Discover content before ingestion
- **Knowledge Graph**: Track relationships and temporal evolution
- **Starter Prompts**: Database-backed exploration prompts
- **3-Column Layout**: Collections | Chat | Document Viewer
- **SSE Streaming**: Token-by-token response streaming
- **PostgresSaver**: Conversation state persistence

## API Endpoints

### Chat
- `POST /api/chat/stream` - SSE streaming chat endpoint

### Conversations
- `GET /api/conversations` - List all conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/{id}` - Get conversation
- `DELETE /api/conversations/{id}` - Delete conversation

### Messages
- `GET /api/conversations/{id}/messages` - Get conversation messages

### Starter Prompts
- `GET /api/starter-prompts` - Get all starter prompts

### Health
- `GET /api/health` - Health check

## Development

### Backend Development

```bash
cd backend

# Run tests
pytest

# Format code
black app/

# Lint code
ruff check app/
```

### Frontend Development

```bash
cd frontend

# Run type checking
npm run typecheck

# Build for production
npm run build
```

## Troubleshooting

### "MCP server not responding"
- Ensure RAG Memory MCP server is running: `uv run rag-mcp-http`
- Check health: `curl http://localhost:3001/health`

### "Database connection failed"
- Check web app PostgreSQL is running: `docker-compose -f docker-compose.web.yml ps`
- Verify DATABASE_URL in backend/.env uses port 5433

### "Agent creation failed"
- Ensure OPENAI_API_KEY is set in backend/.env
- Check all dependencies installed: `uv pip install -r requirements.txt`

## Tech Stack

**Frontend:**
- React 19
- Mantine UI 8
- Zustand (state management)
- TypeScript
- Vite

**Backend:**
- FastAPI
- LangGraph (ReAct agent)
- LangChain 0.3.12
- PostgresSaver (conversation persistence)
- SQLAlchemy (async)

**Integration:**
- MCP (Model Context Protocol) via streamable HTTP
- MultiServerMCPClient (langchain-mcp-adapters)

**Tools:**
- 20 MCP tools (from RAG Memory server)
- 3 Python tools (web search, URL validation, fetch)
