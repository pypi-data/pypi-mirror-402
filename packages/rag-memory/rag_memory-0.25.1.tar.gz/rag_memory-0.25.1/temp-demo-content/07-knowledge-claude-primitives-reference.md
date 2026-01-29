# Claude Code Primitives Reference Guide

## Overview

Claude Code provides 6 primitive types for extending AI capabilities. Each serves a distinct purpose in the AI-native development toolkit.

## Primitive Types

### 1. Slash Commands

**Purpose**: User-initiated, single-purpose AI actions invoked via `/command-name`.

**Location**: `.claude/commands/command-name.md`

**Structure**:
```yaml
---
description: Verb-first description of what this command does
allowed-tools: [Tool1, Tool2]
---

# Instructions for Claude

Detailed instructions for executing this command.
```

**Key Properties**:
- `description`: Shows in command palette, max 80 chars
- `allowed-tools`: Whitelist of tools the command can use

**Example Use Cases**:
- `/commit` - Generate commit messages
- `/explain` - Explain selected code
- `/test` - Generate unit tests

**Best Practices**:
- One command, one responsibility
- Minimal tool set
- Clear success criteria

---

### 2. Skills

**Purpose**: Complex, multi-step workflows that may require user interaction.

**Location**: `.claude/commands/skill-name.md` (with skill-specific structure)

**Difference from Commands**:
- Multiple phases or steps
- Can ask clarifying questions
- May branch based on context
- Manages state across steps

**Example Use Cases**:
- `/review-pr` - Full PR review with findings and suggestions
- `/onboard` - Interactive project setup
- `/debug` - Multi-step debugging workflow

---

### 3. Subagents

**Purpose**: Specialized autonomous agents for focused tasks.

**Configuration**: Defined in skill/command instructions, invoked via Task tool.

**Common Patterns**:

| Pattern | Purpose | Tools |
|---------|---------|-------|
| Explorer | Gather information | Read, Glob, Grep |
| Specialist | Domain expertise | Domain-specific |
| Validator | Check and verify | Read, Bash, Grep |

**Key Properties**:
- `subagent_type`: The type of specialized agent
- `prompt`: Task description for the agent
- `model`: Optional model override (sonnet, opus, haiku)

**Example Use Cases**:
- Code exploration before changes
- Security vulnerability scanning
- Test suite execution and analysis

---

### 4. Hooks

**Purpose**: Event-driven automation triggered by Claude Code actions.

**Location**: `.claude/settings.json` or project `.claude/settings.local.json`

**Hook Types**:
- `PreToolUse`: Before a tool executes
- `PostToolUse`: After a tool completes
- `Notification`: For specific events

**Configuration**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "command": "echo 'Editing file: $FILE_PATH'"
      }
    ]
  }
}
```

**Example Use Cases**:
- Run linter before edits
- Trigger tests after file changes
- Log tool usage for audit

---

### 5. MCP Servers

**Purpose**: Connect Claude Code to external systems and data sources.

**Protocol**: Model Context Protocol (JSON-RPC over stdio or SSE)

**Capabilities**:
- **Tools**: Functions Claude can call
- **Resources**: Data Claude can read
- **Prompts**: Pre-defined prompt templates

**Configuration**: `~/.claude/config.json` or project `mcp.json`

**Example Use Cases**:
- Database queries
- API integrations
- File system access beyond working directory
- Custom tooling

---

### 6. Plugins

**Purpose**: Deep Claude Code integration for advanced customization.

**Note**: Most use cases are better served by the other 5 primitives. Plugins are for edge cases requiring low-level integration.

---

## Primitive Selection Guide

```
Need to extend Claude Code?
│
├── User invokes explicitly?
│   ├── Simple, one-shot action → Slash Command
│   └── Multi-step with interaction → Skill
│
├── Runs autonomously on task?
│   └── Specialized focus area → Subagent
│
├── Triggered by events?
│   └── Pre/post tool execution → Hook
│
├── External system integration?
│   └── Data or API access → MCP Server
│
└── Deep platform integration?
    └── (Rare) → Plugin
```

## File Organization

```
.claude/
├── commands/           # Slash commands and skills
│   ├── commit.md
│   ├── review-pr.md
│   └── project/
│       └── setup.md
├── settings.json       # Hooks and local config
└── agents/             # Subagent definitions (optional)
```

## Security Considerations

1. **Tool Access**: Always use minimal tool sets
2. **Input Validation**: Sanitize user inputs in skills
3. **MCP Servers**: Review data exposure carefully
4. **Hooks**: Avoid secrets in hook commands
5. **Audit**: Log sensitive operations

## Version Control

- Commit `.claude/commands/` for team sharing
- Use `.claude/settings.local.json` for personal config
- Document primitive purposes in team wiki
