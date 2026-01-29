# Configuration Loading in RAG Memory

This document explains how RAG Memory loads configuration for both CLI and MCP server usage.

## Overview

RAG Memory uses a **priority-based configuration system** that supports multi-instance deployments. The implementation is in `mcp-server/src/core/config_loader.py` and uses a clear, predictable order to ensure you always know where your configuration is coming from.

## Configuration Locations

RAG Memory uses OS-standard configuration directories via `platformdirs`:

- **macOS:** `~/Library/Application Support/rag-memory/config.yaml`
- **Linux:** `~/.config/rag-memory/config.yaml` (respects `$XDG_CONFIG_HOME`)
- **Windows:** `%LOCALAPPDATA%\rag-memory\config.yaml`

You can override the config location with the `RAG_CONFIG_PATH` environment variable.

## Loading Priority Order (Highest to Lowest)

### 1. Environment Variables (Highest Priority)

Variables you set manually in your shell session take the highest priority.

**Examples:**
```bash
# Linux/macOS
export DATABASE_URL="postgresql://raguser:ragpass@localhost:54320/rag_memory"
export OPENAI_API_KEY="sk-..."
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"

# Windows PowerShell
$env:DATABASE_URL="postgresql://raguser:ragpass@localhost:54320/rag_memory"
$env:OPENAI_API_KEY="sk-..."
```

- These are **already in the environment** before the tool runs
- Take precedence over everything else
- Useful for temporary overrides, CI/CD, or Docker deployments

### 2. Instance Config from config.yaml

The YAML configuration file supports multiple instances with isolated settings.

**Multi-Instance Structure:**
```yaml
instances:
  primary:
    openai_api_key: "sk-..."
    database_url: "postgresql://raguser:ragpass@localhost:54320/rag_memory"
    neo4j_uri: "bolt://localhost:7687"
    neo4j_user: "neo4j"
    neo4j_password: "..."
    neo4j_http_port: 7474
    mcp_sse_port: 8000
    backup_cron_expression: "0 5 * * *"
    backup_archive_path: "./backups/primary"
    backup_retention_days: 14
    max_reflexion_iterations: 0
    mounts:
      - path: /Users/yourname
        read_only: true

  research:
    openai_api_key: "sk-..."
    database_url: "postgresql://raguser:ragpass@localhost:54330/rag_memory"
    neo4j_uri: "bolt://localhost:7688"
    neo4j_user: "neo4j"
    neo4j_password: "..."
    # ... other settings
```

### 3. Legacy Server Config (Backward Compatibility)

For older installations, the system still supports the legacy single-instance format:

```yaml
server:
  openai_api_key: "sk-..."
  database_url: "postgresql://..."
  neo4j_uri: "bolt://..."
  neo4j_user: "neo4j"
  neo4j_password: "..."

mounts:
  - path: /Users/yourname
    read_only: true
```

## Required Configuration Keys

Every instance must have these keys (either in config or environment):

| Config Key | Environment Variable | Description |
|------------|---------------------|-------------|
| `openai_api_key` | `OPENAI_API_KEY` | OpenAI API key for embeddings |
| `database_url` | `DATABASE_URL` | PostgreSQL connection string |
| `neo4j_uri` | `NEO4J_URI` | Neo4j Bolt connection URI |
| `neo4j_user` | `NEO4J_USER` | Neo4j username |
| `neo4j_password` | `NEO4J_PASSWORD` | Neo4j password |

## Optional Configuration Keys

These settings have sensible defaults:

| Config Key | Environment Variable | Default | Description |
|------------|---------------------|---------|-------------|
| `neo4j_http_port` | - | 7474 | Neo4j HTTP browser port |
| `mcp_sse_port` | - | 8000 | MCP server SSE port |
| `graphiti_model` | `GRAPHITI_MODEL` | gpt-4.1-mini | Model for entity extraction |
| `graphiti_small_model` | `GRAPHITI_SMALL_MODEL` | gpt-4.1-nano | Model for simple tasks |
| `max_reflexion_iterations` | `MAX_REFLEXION_ITERATIONS` | 0 | Recursive extraction depth |
| `search_strategy` | `SEARCH_STRATEGY` | semantic | Search strategy |
| `dry_run_model` | `DRY_RUN_MODEL` | gpt-4.1-mini | Model for dry run relevance |
| `dry_run_temperature` | `DRY_RUN_TEMPERATURE` | 0.3 | Temperature for dry run |
| `dry_run_max_tokens` | `DRY_RUN_MAX_TOKENS` | 500 | Max tokens for dry run |
| `allowed_origins` | `ALLOWED_ORIGINS` | - | CORS origins for HTTP uploads |
| `title_gen_model` | `TITLE_GEN_MODEL` | gpt-4.1-nano | Model for title generation |
| `title_gen_max_chars` | `TITLE_GEN_MAX_CHARS` | 2000 | Max content for title context |
| `title_gen_temperature` | `TITLE_GEN_TEMPERATURE` | 0.3 | Temperature for titles |
| `backup_cron_expression` | - | - | Cron schedule for backups |
| `backup_archive_path` | - | - | Path for backup archives |
| `backup_retention_days` | - | 14 | Days to keep backups |
| `mounts` | - | [] | Directory mounts for file access |

## MCP Server Configuration

For MCP server usage (Claude Desktop, Claude Code, Cursor), environment variables are passed via the MCP client configuration:

**Example (Cursor/Claude Code config):**
```json
{
  "mcpServers": {
    "rag-memory": {
      "command": "rag-mcp-stdio",
      "args": [],
      "env": {
        "OPENAI_API_KEY": "sk-your-api-key-here",
        "DATABASE_URL": "postgresql://raguser:ragpass@localhost:54320/rag_memory",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-neo4j-password"
      }
    }
  }
}
```

**Important:**
- MCP server can use either environment variables OR config.yaml
- Environment variables take precedence
- All 5 required keys must be provided

## Use Cases

### Use Case 1: Local Docker Development

The setup script (`scripts/setup.py`) creates config.yaml with all required settings:

1. Run: `python scripts/setup.py`
2. Follow interactive prompts
3. Config saved to OS-standard location
4. Run: `rag status` to verify

### Use Case 2: Multi-Instance Setup

Run setup.py multiple times with different instance names:

```bash
python scripts/setup.py --instance primary
python scripts/setup.py --instance research
```

Each instance gets isolated:
- PostgreSQL database (different ports)
- Neo4j database (different ports)
- MCP server (different ports)

### Use Case 3: Cloud Deployment

For Render + Neo4j Aura deployment, use the deployment script:

```bash
python scripts/deploy_to_cloud.py
```

Environment variables are set in Render's dashboard.

### Use Case 4: CI/CD Usage

```bash
# In your CI/CD pipeline, set environment variables
export DATABASE_URL="${SECRET_DB_URL}"
export OPENAI_API_KEY="${SECRET_API_KEY}"
export NEO4J_URI="${SECRET_NEO4J_URI}"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="${SECRET_NEO4J_PASSWORD}"

rag ingest file documentation.md --collection docs
```

## Directory Mounts (Security)

The `mounts` configuration controls which directories the MCP server can access:

```yaml
instances:
  primary:
    # ... other settings
    mounts:
      - path: /Users/yourname/Documents
        read_only: true
      - path: /Users/yourname/Projects
        read_only: true
```

- Only mounted paths can be accessed by `ingest_file` and `ingest_directory`
- `read_only: true` is recommended (ingestion doesn't need write access)
- If no mounts configured, file operations are blocked

## Troubleshooting

### "Required config key missing" error

**Check in order:**
1. Is the environment variable set? `echo $DATABASE_URL`
2. Does config.yaml exist? Check OS-standard location
3. Is the instance name correct? Check `INSTANCE_NAME` env var

### Finding your config file

```bash
# macOS
cat ~/Library/Application\ Support/rag-memory/config.yaml

# Linux
cat ~/.config/rag-memory/config.yaml

# Or use RAG_CONFIG_PATH
export RAG_CONFIG_PATH=/path/to/custom/config
cat $RAG_CONFIG_PATH/config.yaml
```

### MCP server can't connect

**Check:**
- All 5 required environment variables in MCP client config
- No trailing commas in JSON
- Databases are running: `rag status`

## Related Files

- `mcp-server/src/core/config_loader.py` - Configuration loading logic
- `mcp-server/src/core/first_run.py` - Interactive setup wizard
- `scripts/setup.py` - Instance setup script
- `scripts/deploy_to_cloud.py` - Cloud deployment script
