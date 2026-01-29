# RAG Memory Architecture

## Structured Workflows for AI

> **Goal:** Apply structured workflows to guide AI behavior

```mermaid
flowchart LR
    A[Structured Workflows] --> B[Guided AI]
    B --> C[Reliable Outputs]

    style A fill:#f59e0b,color:#000
    style B fill:#8b5cf6,color:#fff
    style C fill:#22c55e,color:#000
```

| Principle | What It Means |
|-----------|---------------|
| **Reliability** | AI produces correct results, not hallucinations |
| **Consistency** | Same input yields same quality output every time |
| **Repeatability** | Workflows can be reproduced across teams and projects |
| **Productivity** | Engineers ship faster with AI as a force multiplier |

---

## System Architecture

```mermaid
flowchart LR
    subgraph Client
        FE[React Frontend]
    end

    subgraph Backend
        API[FastAPI + LangGraph Agent]
    end

    subgraph MCP[MCP Server]
        RAG[RAG Memory Engine]
    end

    subgraph Storage
        PG[(PostgreSQL + pgvector)]
        NEO[(Neo4j + Graphiti)]
    end

    FE -->|REST / SSE| API
    API -->|MCP Protocol| RAG
    RAG --> PG
    RAG --> NEO

    style FE fill:#f59e0b,color:#000
    style API fill:#0ea5e9,color:#000
    style RAG fill:#8b5cf6,color:#fff
    style PG fill:#22c55e,color:#000
    style NEO fill:#22c55e,color:#000
```

## Layer Overview

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React + Mantine | Chat UI, document browser, search interface |
| **Backend** | FastAPI + LangGraph | REST API, AI agent with 20 tools, SSE streaming |
| **MCP Server** | Python MCP SDK | Ingestion, semantic search, knowledge graph queries |
| **Storage** | PostgreSQL + Neo4j | Vectors & documents (PG) / Knowledge graph (Neo4j) |

## Data Flow

1. **User interacts** with React frontend
2. **Backend routes** requests - either direct proxy or through AI agent
3. **MCP Server** handles all RAG operations via standardized tools
4. **Dual storage** - vectors in PostgreSQL, relationships in Neo4j
