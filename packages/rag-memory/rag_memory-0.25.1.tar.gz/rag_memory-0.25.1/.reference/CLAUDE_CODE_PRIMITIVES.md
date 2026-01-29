# Claude Code Primitives

RAG Memory includes slash commands and hooks for Claude Code users.

## Slash Commands

Located in `.claude/commands/`:

### /getting-started

Interactive guided tour of RAG Memory - learn concepts, capabilities, and setup step by step.

**Use when:** New to RAG Memory and want to understand what it does and how to use it.

### /setup-collections

Interactive wizard to scaffold RAG Memory collections based on your use cases.

**Use when:** Setting up collections for a new project or use case.

### /capture

Capture content into RAG Memory with intelligent routing.

**Use when:** You want to ingest content and need help determining the right collection and parameters.

### /dev-onboarding

Developer onboarding for contributors - architecture, code organization, and development workflow.

**Use when:** You want to contribute to RAG Memory and need to understand how the codebase works.

### /cloud-setup

Deploy RAG Memory to Render using automated deployment script.

**Use when:** Ready to deploy RAG Memory to cloud infrastructure.

### /reference-audit

Audit documentation directories to ensure all claims match actual source code.

**Arguments:**
- No argument → Audit both `.reference/` and `docs/`
- `reference` → Only `.reference/`
- `docs` → Only `docs/`

**Use when:** Documentation may be out of sync with code. Performs bidirectional verification (docs→code and code→docs).

### /report-bug

Submit a bug report to the RAG Memory GitHub repository.

**Use when:** You've found a bug and want to report it properly.

## Hooks

Located in `.claude/hooks/`:

### rag-approval.py

PreToolUse hook that intercepts RAG Memory ingest operations and requires explicit user approval.

**What it does:**
- Intercepts all `mcp__rag-memory__ingest_*` tool calls
- Displays ingest details (collection, content preview, mode, topic)
- Prompts user for approval before proceeding

**Why it exists:** Prevents accidental ingestion of content into the wrong collection or with wrong parameters.

## Installation

These primitives are part of the RAG Memory repository. When you open the project in Claude Code, they are automatically available.

To use a slash command, type `/` followed by the command name (e.g., `/getting-started`).

Hooks are automatically active when configured in `.claude/settings.json`.
