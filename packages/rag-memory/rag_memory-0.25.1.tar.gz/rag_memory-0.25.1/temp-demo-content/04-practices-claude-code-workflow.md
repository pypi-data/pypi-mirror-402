# Claude Code Workflow Design Playbook

## Overview

This playbook documents our recommended approach for designing Claude Code workflows. Use this when helping teams build their own AI-native development practices.

## The Primitive Selection Framework

### When to Use Each Primitive

| Primitive | Use When | Example |
|-----------|----------|---------|
| **Slash Command** | User-initiated, single-purpose action | `/commit` - Generate commit message |
| **Skill** | Complex, multi-step user workflow | `/review-pr` - Full PR review process |
| **Subagent** | Autonomous task requiring specialized focus | Code exploration, security scanning |
| **Hook** | Event-driven automation | Pre-commit checks, post-edit validation |
| **MCP Server** | External system integration | Database queries, API calls |

### Decision Tree

```
Is this user-initiated?
├── Yes → Is it a single action or multi-step?
│   ├── Single action → Slash Command
│   └── Multi-step → Skill
└── No → Is it event-driven?
    ├── Yes → Hook
    └── No → Is it external data/systems?
        ├── Yes → MCP Server
        └── No → Subagent
```

## Designing Effective Slash Commands

### Structure
```yaml
---
description: Clear, verb-first description (e.g., "Generate release notes")
allowed-tools: [Read, Glob, Grep]  # Minimal required set
---

# Command Name

## Purpose
One sentence explaining the value this command provides.

## Workflow
1. Step one
2. Step two
3. Final output

## Output Format
Describe expected output structure.
```

### Best Practices
1. **Single responsibility**: One command, one job
2. **Minimal tools**: Only request tools actually needed
3. **Clear output**: Define what success looks like
4. **Graceful failure**: Handle edge cases explicitly

## Designing Skills vs Commands

Skills are expanded slash commands with:
- Multiple phases or steps
- User interaction points
- Conditional logic
- State management

**Rule of thumb**: If it needs to ask questions or branch based on context, it's a skill.

## Subagent Design Patterns

### The Explorer Pattern
- **Purpose**: Gather information without modification
- **Tools**: Read, Glob, Grep (no Edit, Write)
- **Use case**: Understanding codebase before changes

### The Specialist Pattern
- **Purpose**: Deep expertise in narrow domain
- **Tools**: Domain-specific (e.g., test runner, security scanner)
- **Use case**: Tasks requiring specialized knowledge

### The Validator Pattern
- **Purpose**: Check work before committing
- **Tools**: Read, Bash (for tests), Grep
- **Use case**: Pre-merge validation, code review

## Workflow Composition

Complex workflows combine primitives:

```
User invokes /deploy
  → Skill orchestrates:
    → Subagent (Explorer): Check deployment readiness
    → Slash command: Generate changelog
    → Hook triggers: Run pre-deploy checks
    → MCP Server: Update deployment tracking system
    → Subagent (Validator): Verify deployment success
```

## Documentation Standards

Every primitive should have:
1. **Purpose**: Why does this exist?
2. **Trigger**: How is it invoked?
3. **Inputs**: What does it need?
4. **Outputs**: What does it produce?
5. **Dependencies**: What must be true for it to work?
6. **Failure modes**: What can go wrong and how do we handle it?

## Review Checklist

Before deploying a new primitive:
- [ ] Purpose is clear and documented
- [ ] Tools are minimal and justified
- [ ] Output format is defined
- [ ] Error handling is explicit
- [ ] Security implications considered
- [ ] Tested with realistic inputs
