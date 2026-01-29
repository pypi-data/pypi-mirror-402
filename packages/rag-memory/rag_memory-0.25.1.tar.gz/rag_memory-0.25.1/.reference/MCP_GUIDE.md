# MCP Server Guide

This guide covers setting up and using the RAG Memory MCP server with AI agents.

## Prerequisites

Before configuring the MCP server:

1. Complete installation (see INSTALLATION.md)
2. Databases running (PostgreSQL + Neo4j)
3. OpenAI API key available

Verify setup:
```bash
# Check containers running
docker ps | grep rag-memory

# Check database health
rag status
```

## Starting the MCP Server

The MCP server runs as a Docker container started during setup. Verify it's running:

```bash
docker ps | grep mcp-server
```

**Endpoint:** `http://localhost:3001/mcp` (streamable HTTP)

**Manual start (if needed):**
```bash
rag-mcp-http     # Starts MCP server on port 3001
```

## Configure AI Agents

### Claude Code

**IMPORTANT:** You must exit and restart Claude Code after adding the MCP server. MCP connections are only established at session start.

```bash
claude mcp add rag-memory -s user --transport http --url http://localhost:3001/mcp
```

**After adding:**
1. EXIT Claude Code completely
2. Start a fresh session
3. Test: "List RAG Memory collections"

### Claude Desktop

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "rag-memory": {
      "transport": "http",
      "url": "http://localhost:3001/mcp"
    }
  }
}
```

**After editing:** Restart Claude Desktop completely.

### Cursor

Add the MCP server with streamable HTTP transport:

**Endpoint:** `http://localhost:3001/mcp`

Check Cursor documentation for the specific configuration format.

## Test the Connection

### Method 1: Using Your AI Agent

1. Restart AI agent (quit and reopen)
2. Look for MCP server indicator
3. Ask: "List available RAG collections"
4. Should see `list_collections` tool being called

### Method 2: MCP Inspector

Test server without AI client:

```bash
# Start inspector (opens in browser)
mcp dev src/mcp/server.py
```

Inspector shows:
- All 20 available tools
- Tool parameters and descriptions
- Test tool calls interactively
- View call history

### Method 3: CLI Testing

Test components directly:

```bash
# Check database
rag status

# List collections
rag collection list

# Create test collection
rag collection create test \
  --description "Test collection" \
  --domain "Testing" \
  --domain-scope "Setup verification"

# Ingest test document
rag ingest text "PostgreSQL enables semantic search" \
  --collection test

# Search
rag search "semantic search" --collection test
```

## Available Tools (20 Total)

### Search & Discovery (4 tools)

**search_documents**
- Semantic vector similarity search
- Parameters: query, collection_name, limit, threshold
- Returns: Chunks with similarity scores (0.0-1.0)

**list_collections**
- Discover all knowledge bases
- Parameters: None
- Returns: Collections with document counts

**get_collection_info**
- Detailed collection statistics
- Parameters: collection_name
- Returns: Document count, chunk count, crawl metadata

**analyze_website**
- Parse sitemap and understand site structure
- Parameters: url, include_url_lists, max_urls_per_pattern
- Returns: URL patterns and statistics

### Document Management (5 tools)

**list_documents**
- Browse documents with pagination
- Parameters: collection_name, limit, offset
- Returns: Document IDs, filenames, metadata

**get_document_by_id**
- Retrieve full source document
- Parameters: document_id, include_chunks
- Returns: Full content, metadata, chunks

**ingest_text**
- Add text content with auto-chunking
- Parameters: content, collection_name, metadata
- Returns: document_id, num_chunks

**update_document**
- Edit document content or metadata
- Parameters: document_id, content, title, metadata
- Returns: Updated document_id

**delete_document**
- Remove documents
- Parameters: document_id
- Returns: Confirmation

### Collection Management (4 tools)

**create_collection**
- Create new named collection
- Parameters: name, description, domain, domain_scope, metadata_schema
- Returns: collection_id, created status

**get_collection_metadata_schema**
- Get metadata schema for a collection
- Parameters: collection_name
- Returns: Schema definition with custom and system fields

**update_collection_metadata**
- Add new optional metadata fields to existing collection (additive only)
- Parameters: collection_name, new_fields
- Returns: Updated collection with new schema

**delete_collection**
- Delete collection and all documents (requires confirmation)
- Parameters: name, confirm
- Returns: Deleted status

### Advanced Ingestion (3 tools)

**ingest_url**
- Crawl single or multiple web pages
- Parameters: url, collection_name, follow_links, max_pages, mode, dry_run, topic
- Returns: pages_crawled, num_chunks (or relevance scores if dry_run=True)
- Supports dry_run mode to preview and score page relevance before ingesting

**ingest_file**
- Add document from filesystem
- Parameters: file_path, collection_name, metadata
- Returns: document_id, num_chunks

**ingest_directory**
- Batch ingest entire directory
- Parameters: directory_path, collection_name, extensions, recursive
- Returns: List of ingested documents

### Directory Exploration (1 tool)

**list_directory**
- Explore local directory contents before ingesting
- Parameters: directory_path, file_extensions, recursive, include_preview, max_files
- Returns: File metadata, sizes, previews, extension summary
- Note: FREE operation (no AI models, just filesystem access)

### Knowledge Graph (2 tools)

**query_relationships**
- Search entity relationships
- Parameters: query, num_results
- Returns: Relationships with descriptions

**query_temporal**
- Track knowledge evolution
- Parameters: query, num_results, valid_from, valid_until
- Returns: Timeline of changes

### Document Linking (1 tool)

**manage_collection_link**
- Link or unlink a document to/from a collection
- Parameters: document_id, collection_name, unlink
- Returns: Link status and affected chunks

## Tool Usage Patterns

### Semantic Search
```
Agent asks: "How do I authenticate users?"
Tool call: search_documents(query="How do I authenticate users?", collection_name="tech-docs")
Response: Chunks about OAuth, tokens, authentication flows
```

### Web Crawling (with dry_run)
```
Agent asks: "Ingest React hooks documentation"
Tool call: ingest_url(url="https://react.dev/reference/react", follow_links=True, max_pages=15, dry_run=True, topic="React hooks")
Response: Found 15 pages - 10 recommended for ingest, 2 to review, 3 to skip
Agent: "I'll ingest the recommended pages about hooks"
Tool call: ingest_url(url="https://react.dev/reference/react/useState", collection_name="react-docs")
Response: Ingested 1 page, 8 chunks
```

### Local File Exploration
```
Agent asks: "Check what's in my docs folder"
Tool call: list_directory(directory_path="/docs/engineering", file_extensions=[".md"], include_preview=True)
Response: Found 12 files: ARCHITECTURE.md (17KB), API_GUIDE.md (8KB)...
Agent: "Those look relevant, let me ingest the architecture doc"
Tool call: ingest_file(file_path="/docs/engineering/ARCHITECTURE.md", collection_name="eng-docs")
```

### Knowledge Graph
```
Agent asks: "Which services depend on authentication?"
Tool call: query_relationships(query="services that depend on authentication")
Response: UserService, PaymentAPI, AdminPanel all depend on AuthService
```

## Troubleshooting

### Server Not Showing in AI Agent

**Check config syntax:**
- No trailing commas in JSON
- Double quotes only
- Correct file path

**Verify MCP server is running:**
```bash
curl http://localhost:3001/health
# Should return healthy status
```

**Check logs:**
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\Logs\mcp*.log`

### Database Connection Errors

```bash
# Verify containers running
docker ps | grep rag-memory

# Check database logs
docker logs rag-memory-postgres
docker logs rag-memory-neo4j

# Restart if needed
rag restart

# Test connection
rag status
```

### OpenAI API Key Errors

**Check configuration:**
```bash
# Verify config exists
ls ~/Library/Application\ Support/rag-memory/config.yaml

# Check for OPENAI_API_KEY in config
grep OPENAI_API_KEY ~/Library/Application\ Support/rag-memory/config.yaml
```

Never expose API keys to AI assistants or logs.

### Tools Not Working

**Verify database:**
```bash
rag status
# Both PostgreSQL and Neo4j must be healthy
```

**Check collections exist:**
```bash
rag collection list
```

**Test with sample data:**
```bash
rag collection create test --description "Test" --domain "Testing" --domain-scope "Verification"
rag ingest text "Test document" --collection test
rag search "test" --collection test
```

## Environment Variables

MCP server gets configuration from client environment:

**Required:**
- `OPENAI_API_KEY` - OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string

**Optional:**
- `NEO4J_URI` - Neo4j URI (default: bolt://localhost:7687)
- `NEO4J_USER` - Neo4j username (default: neo4j)
- `NEO4J_PASSWORD` - Neo4j password

See CONFIGURATION.md for details.

## Next Steps

- **CLI Usage** - See CLI_GUIDE.md for direct CLI commands
- **Search Details** - See VECTOR_SEARCH.md for semantic search
- **Graph Features** - See KNOWLEDGE_GRAPH.md for entity extraction
- **Troubleshooting** - See TROUBLESHOOTING.md for common issues
