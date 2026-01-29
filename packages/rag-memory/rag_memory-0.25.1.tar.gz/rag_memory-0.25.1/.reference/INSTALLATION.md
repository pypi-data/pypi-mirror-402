# Installation

This guide covers setting up RAG Memory locally with Docker.

## Prerequisites

**Required Software**
- Docker Desktop (for Mac/Windows) or Docker Engine (for Linux)
- Git
- Python 3.11 or higher (for the setup script)

**Required Credentials**
- OpenAI API key (get from https://platform.openai.com/api-keys)

**System Requirements**
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- macOS, Linux, or Windows with WSL2

## Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/codingthefuturewithai/rag-memory.git
cd rag-memory

# 2. Install dependencies (REQUIRED)
uv sync

# 3. Activate virtual environment (REQUIRED)
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows alternative

# 4. Run setup script
python scripts/setup.py
```

The setup script handles:
- Docker container startup (PostgreSQL + Neo4j)
- Database initialization
- System configuration
- CLI tool installation
- Health verification

## Detailed Setup Steps

### 1. Install Docker

**macOS**
```bash
# Download Docker Desktop from docker.com
# Or use Homebrew:
brew install --cask docker
```

**Linux**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

**Windows**
- Install Docker Desktop for Windows
- Enable WSL2 backend
- Restart system if prompted

### 2. Verify Docker

```bash
docker --version
docker ps
```

Should show Docker version and no errors.

### 3. Clone Repository

```bash
git clone https://github.com/codingthefuturewithai/rag-memory.git
cd rag-memory
```

### 4. Activate Virtual Environment

```bash
# CRITICAL: This step is required for setup.py to work
source .venv/bin/activate

# Verify activation (prompt should show (.venv))
which python
```

### 5. Run Setup Script

```bash
python scripts/setup.py
```

**Setup Script Does:**
1. Checks Docker is installed and running
2. Checks for existing RAG Memory containers
3. **Prompts for OpenAI API key**
4. Finds available ports (54320 for PostgreSQL, 7474/7687 for Neo4j)
5. **Configures directory mounts** (for file ingestion access)
6. **Configures backup schedule** (daily backup time)
7. **Configures backup location** (where backups are stored)
8. **Configures backup retention** (how long to keep backups)
9. **Configures entity extraction quality** (standard vs enhanced)
10. Creates configuration files (config.yaml, .env, docker-compose.yml)
11. Builds MCP server Docker image
12. Starts all containers (PostgreSQL, Neo4j, MCP, backup)
13. Waits for health checks (all services ready)
14. Initializes Neo4j Graphiti indices (28 indexes/constraints)
15. Creates Neo4j vector indices (performance optimization)
16. Installs CLI tool globally (rag command)
17. Validates database schemas
18. Displays connection details and next steps

**Expected Output:**
```
================================================================================
RAG Memory Setup Script
================================================================================

STEP 1: Checking Docker Installation
✓ Docker is installed

STEP 2: Checking Docker Daemon
✓ Docker daemon is running

STEP 3: Checking for Existing RAG Memory Containers
ℹ No existing RAG Memory local containers found

STEP 4: OpenAI API Key
Enter your OpenAI API key (sk-...): sk-proj-...
✓ API key accepted: sk-proj-...***

STEP 5: Finding Available Ports
✓ postgres: 54320 (default)
✓ neo4j_http: 7474 (default)
✓ neo4j_bolt: 7687 (default)
✓ mcp: 18000 (default)

STEP 6: Configure Directory Access for File Ingestion
Mount home directory as read-only? (yes/no, default: yes): yes
✓ Added mount: /Users/you (read-only)

STEP 7: Configure Backup Schedule
Enter backup time in Local Time (HH:MM, default: 02:05): 02:05
✓ Backup schedule: Daily at 02:05

STEP 8: Configure Backup Location
Backup directory (default: ./backups):
✓ Backup location: ./backups

STEP 9: Configure Backup Retention
Keep backups for how many days? (default: 14): 14
✓ Backup retention: 14 days

STEP 10: Entity Extraction Quality (Optional)
Enter choice (0-2, default: 0): 0
✓ Using standard quality (fast, cost-effective)

STEP 11: Creating Configuration Files
✓ Configuration created: /Users/you/Library/Application Support/rag-memory/config.yaml
✓ Environment file created: deploy/docker/compose/.env
✓ Docker Compose configuration created: deploy/docker/compose/docker-compose.yml

STEP 12: Building and Starting Containers
✓ MCP image built (fresh build)
✓ Containers started (fresh recreate)

STEP 13: Waiting for Services to Be Ready
✓ PostgreSQL is ready and accepting connections
✓ Neo4j is ready and accepting connections
✓ MCP server is running and responding on port 18000

STEP 14: Initializing Neo4j Indices
✓ Neo4j indices initialized successfully

STEP 14.5: Creating Neo4j Vector Indices
✓ Entity.name_embedding vector index created
✓ RELATES_TO.fact_embedding vector index created

STEP 15: Installing CLI Tool
✓ CLI tool installed successfully

STEP 16: Validating Database Schemas
✓ PostgreSQL schema validated (4 tables found)
✓ Neo4j is accessible

✨ Setup Complete!
```

## Verify Installation

### Check Services

```bash
# Check Docker containers
docker ps

# Should show 4 containers with your stack name:
# - rag-memory-mcp-postgres-{yourstack}
# - rag-memory-mcp-neo4j-{yourstack}
# - rag-memory-mcp-server-{yourstack}
# - rag-memory-mcp-backup-{yourstack}
#
# The stack name is what you entered during setup (e.g., "local", "dev", "work")
```

### Check CLI Tool

```bash
# CLI should be available globally
rag status

# Expected output:
# ✓ PostgreSQL: healthy
# ✓ Neo4j: healthy
```

### First Use Walkthrough

This walkthrough verifies both RAG (vector search) and Graph (knowledge graph) stores are working.

**If using Claude Code:** Skip to the [Claude Code Users](#claude-code-users) section. You'll use `/setup-collections` to create collections and verify everything works.

**If using CLI only:** Continue with the steps below.

#### Step 1: Create a Test Collection

```bash
rag collection create test-docs \
  --description "Test collection for setup verification" \
  --domain "Testing" \
  --domain-scope "Setup verification only"
```

#### Step 2: Ingest Your First Document

When you ingest content, RAG Memory processes it into BOTH stores:

```bash
# Replace test-docs with your collection name from Step 1
rag ingest text "React is a JavaScript library for building user interfaces. It uses a virtual DOM for efficient updates and supports component-based architecture with hooks for state management." \
  --collection test-docs
```

**What happens:**

1. **RAG Store (PostgreSQL):**
   - Text split into chunks
   - Each chunk converted to 1536-dimension vector
   - Stored for semantic similarity search

2. **Graph Store (Neo4j):**
   - Entities extracted: React, JavaScript, virtual DOM, hooks, etc.
   - Relationships identified: React → USES → virtual DOM
   - Stored for relationship queries

**Expected output:**
```
✓ Ingested 1 document (X chunks) into collection
  Quality score: 0.XX
```

#### Step 3: Your First RAG Search (Vector Similarity)

RAG search finds content by meaning, not exact keywords:

```bash
# Replace test-docs with your collection name
rag search "How does React handle UI updates efficiently?" --collection test-docs
```

**Expected output:**
```
Results: 1 match

[1] Score: 0.75
    Content: React is a JavaScript library for building user interfaces...
    Source: document_id=1
```

**What this tells you:**
- Similarity score (0.0-1.0) indicates relevance
- Content chunks are returned, not full documents
- Works even though query words differ from document words

#### Step 4: Your First Graph Query (Entity Relationships)

Graph queries find how concepts connect:

```bash
rag graph query-relationships "What technologies does React use?" --collection test-docs
```

**Expected output:**
```
Relationships Found: 2

[1] React → USES → virtual DOM
    Fact: React uses a virtual DOM for efficient updates

[2] React → SUPPORTS → hooks
    Fact: React supports hooks for state management
```

**What this tells you:**
- Entities and their relationships are extracted
- Returns structured facts, not text chunks
- Complements RAG search with relationship intelligence

#### Step 5: Understanding When to Use Each

**Use RAG search when asking:**
- "What information exists about X?"
- "How do I configure X?"
- "Show me documentation about X"

**Use Graph queries when asking:**
- "What connects to X?"
- "Which services depend on X?"
- "How has X evolved over time?"

**Use both together:**
- Graph to understand structure and relationships
- RAG to get detailed content

See KNOWLEDGE_GRAPH.md for comprehensive guidance on RAG vs Graph queries.

#### Step 6: Clean Up (Optional)

```bash
# Delete the test collection
rag collection delete test-docs --confirm
```

## Configuration Files

Setup creates configuration at:
- **macOS**: `~/Library/Application Support/rag-memory/config.yaml`
- **Linux**: `~/.config/rag-memory/config.yaml`
- **Windows**: `%APPDATA%\rag-memory\config.yaml`

Configuration contains:
- Database connection strings
- OpenAI API key
- Neo4j credentials
- Backup settings

See CONFIGURATION.md for details.

## Post-Installation

### Start Services

```bash
# Start containers (if stopped)
rag start

# Verify status
rag status
```

### Stop Services

```bash
# Stop containers (data persists)
rag stop
```

### View Logs

```bash
# View all service logs
rag logs

# View specific service
rag logs --service postgres
rag logs --service neo4j
```

## Web Interface (Optional)

RAG Memory includes a full React + FastAPI web application for conversational knowledge management.

### Prerequisites

- Node.js 18+ (for frontend)
- The core RAG Memory services must be running (`rag status` shows healthy)

### Quick Start

```bash
# From rag-memory root directory
python manage.py setup    # First time only: installs dependencies, runs migrations
python manage.py start    # Start all services (including web UI)
```

**Access:** http://localhost:5173

### What It Provides

- **Conversational Interface** - Chat with a ReAct agent that uses all 20 MCP tools
- **3-Column Layout** - Collections sidebar | Chat interface | Document viewer
- **Web Search Integration** - Discover and evaluate content before ingestion
- **Knowledge Graph Visualization** - See entity relationships visually
- **Streaming Responses** - Token-by-token SSE streaming

### Service Management

```bash
python manage.py status   # Check all services
python manage.py logs     # Tail all logs
python manage.py stop     # Stop all services
python manage.py restart  # Restart services
```

See WEB_INTERFACE.md for complete documentation.

## Database Access

**PostgreSQL**
```bash
# Connection string (port may vary by stack - check your .env)
postgresql://raguser:ragpassword@localhost:54320/rag_memory

# Connect via psql
psql postgresql://raguser:ragpassword@localhost:54320/rag_memory

# Or using docker exec (replace {yourstack} with your stack name)
docker exec -it rag-memory-mcp-postgres-{yourstack} psql -U raguser -d rag_memory
```

**Neo4j Browser**
- URL: http://localhost:7474 (port may vary by stack)
- Username: `neo4j`
- Password: `graphiti-password`

## Data Persistence

**Docker Volumes**
Data persists in Docker volumes even when containers are stopped:
- `postgres_data_{yourstack}` - PostgreSQL data
- `neo4j_data_{yourstack}` - Neo4j data
- `neo4j_logs_{yourstack}` - Neo4j logs

**Backup**
```bash
# Manual backup (replace {yourstack} with your stack name)
docker exec rag-memory-mcp-postgres-{yourstack} pg_dump -U raguser rag_memory > backup.sql

# Restore
docker exec -i rag-memory-mcp-postgres-{yourstack} psql -U raguser rag_memory < backup.sql
```

## Troubleshooting

See TROUBLESHOOTING.md for common issues and solutions.

**Quick Fixes:**

**Port Already in Use**
```bash
# Check what's using port 54320
lsof -i :54320

# Stop conflicting service or change RAG Memory port in config
```

**Docker Not Running**
```bash
# macOS: Start Docker Desktop app
# Linux: sudo systemctl start docker
# Windows: Start Docker Desktop
```

**Permission Denied**
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

## Claude Code Users

If you're using RAG Memory with Claude Code, additional setup steps and tools are available.

### Connect Claude Code to RAG Memory

**IMPORTANT: This requires exiting your current session.**

Claude Code only connects to MCP servers when a session STARTS. You cannot test the connection in the same session where you ran setup. You must:

1. Add the MCP server configuration
2. EXIT this Claude Code session completely
3. Start a FRESH session
4. THEN verify the connection works

**Step 1: Add the MCP server:**

```bash
claude mcp add rag-memory -s user --transport http --url http://localhost:3001/mcp
```

**Step 2: Exit Claude Code completely.** Type `exit` or press Ctrl+C.

**Step 3: Start a fresh Claude Code session.** Run `claude` again.

**Step 4: Verify connection in the NEW session.** Ask: "List RAG Memory collections"

If you see collection results, the connection is working. If you see an error about MCP tools not being available, you're still in an old session - exit and try again.

Only after completing these steps will MCP tools and slash commands work.

### Set Up Your Collections

Run the `/setup-collections` slash command to create a starter scaffold of collections organized by use case:

```
/setup-collections
```

This interactive wizard helps you create collections for:
- **knowledge-and-reference** - External documentation and reference material
- **projects** - Work-in-progress contexts and project notes
- **practices-and-procedures** - SOPs, checklists, workflows
- **people-and-relationships** - Person-centric notes and context
- **inbox-unsorted** - Temporary holding for uncategorized items

You can also create custom collections based on your specific needs.

### Available Slash Commands

RAG Memory includes 7 slash commands for common workflows:

| Command | Purpose |
|---------|---------|
| `/getting-started` | Interactive guided tour of RAG Memory |
| `/setup-collections` | Create starter collections for your use cases |
| `/capture` | Intelligently route content to the right collection |
| `/dev-onboarding` | Developer onboarding for contributors |
| `/cloud-setup` | Deploy RAG Memory to cloud infrastructure |
| `/reference-audit` | Verify documentation matches code |
| `/report-bug` | Submit a bug report |

### Ingest Approval Hook

RAG Memory includes a hook that intercepts ingest operations and requires explicit approval before proceeding. This prevents accidental ingestion into wrong collections.

See CLAUDE_CODE_PRIMITIVES.md for complete documentation of slash commands and hooks.

## Next Steps

- **Web Interface** - See WEB_INTERFACE.md for React + FastAPI setup
- **CLI Usage** - See CLI_GUIDE.md for complete command reference
- **MCP Setup** - See MCP_GUIDE.md for AI agent integration
- **Claude Code** - See CLAUDE_CODE_PRIMITIVES.md for slash commands and hooks
- **Configuration** - See CONFIGURATION.md for advanced settings
- **Cloud Deployment** - See CLOUD_SETUP.md for production deployment
