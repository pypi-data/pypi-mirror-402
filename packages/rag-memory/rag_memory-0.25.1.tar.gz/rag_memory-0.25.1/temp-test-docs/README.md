# Claude Code Test Documentation Collection

This directory contains documentation about various Claude Code features and primitives. These documents are for testing the RAG Memory ingestion system.

## Contents

### 1. Cowork Overview (`cowork-overview.md`)
Documentation about Claude Desktop's Cowork feature - an agentic system for complex knowledge work tasks.

**Topics**: Direct file access, task coordination, professional outputs, extended execution

### 2. Slash Commands Guide (`slash-commands-guide.md`)
Comprehensive guide to creating and using slash commands in Claude Code.

**Topics**: Command structure, YAML frontmatter, best practices, argument handling

### 3. Hooks Explained (`hooks-explained.md`)
Deep dive into Claude Code's hook system for deterministic control over agent behavior.

**Topics**: Hook types, events, configuration, PreToolUse/PostToolUse, real examples

### 4. MCP Servers Introduction (`mcp-servers-intro.txt`)
Overview of Model Context Protocol and how MCP servers extend Claude Code capabilities.

**Topics**: Protocol basics, tool naming, configuration, popular servers, creating custom servers

### 5. Skills vs Commands (`skills-vs-commands.md`)
Comparison of two Claude Code primitives - when to use which and how they differ.

**Topics**: Invocation patterns, use cases, composition, best practices

## Purpose

These documents serve as test data for:
- Directory ingestion via `/capture`
- Hook approval workflow testing
- Collection routing verification
- Multi-file batch processing

## Metadata

- **Created**: 2026-01-14
- **Format**: Markdown (.md) and Text (.txt)
- **Total Files**: 6
- **Purpose**: Testing and documentation
- **Topic**: Claude Code primitives and features

## Usage

To ingest this collection:
```
/capture /tmp/claude-code-test-docs
```

Recommended collection: **Knowledge & Reference** (external documentation about Claude Code)
