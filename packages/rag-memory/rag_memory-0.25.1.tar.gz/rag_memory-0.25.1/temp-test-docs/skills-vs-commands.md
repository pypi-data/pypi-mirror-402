# Skills vs Slash Commands in Claude Code

## What's the Difference?

Both skills and slash commands are Claude Code primitives that provide reusable functionality, but they serve different purposes and have distinct invocation patterns.

## Slash Commands

**Invocation**: Manual - user types `/command-name`

**Structure**: Single markdown file in `.claude/commands/`

**Best for**:
- Explicit workflows you trigger intentionally
- Operations requiring user confirmation
- Tasks with clear start/end points

**Example Use Cases**:
- `/commit` - Create a git commit
- `/review-pr` - Review a pull request
- `/capture` - Capture content to RAG Memory

## Skills

**Invocation**: Automatic - Claude decides when relevant

**Structure**: Directory in `.claude/skills/` with supporting files

**Best for**:
- Context Claude should always have
- Patterns and templates Claude can apply
- Knowledge that enhances responses

**Example Use Cases**:
- Code review checklists
- Testing patterns
- Documentation templates
- Routing and classification logic

## Key Differences

| Aspect | Slash Commands | Skills |
|--------|---------------|--------|
| Invocation | User types `/` | Claude auto-applies |
| Complexity | Simple prompts | Can include templates, scripts |
| Discovery | Slash menu | Background knowledge |
| Files | Single .md file | Directory with assets |
| Use case | Explicit actions | Implicit enhancement |

## When to Use Which?

**Use Slash Commands when**:
- User needs explicit control
- Operation has side effects (commits, deploys)
- Requires user confirmation
- Clear entry/exit points

**Use Skills when**:
- Claude should always consider this
- Provides patterns/templates
- Enhances response quality
- No side effects (pure knowledge)

## Composition

Skills and slash commands can work together:
- Slash command invokes workflow
- Skill provides patterns/knowledge
- Hook enforces rules

Example: `/capture` command uses routing skill's logic, protected by approval hook.

## YAML Frontmatter Similarities

Both use similar YAML frontmatter:

```yaml
---
description: What this does
allowed-tools: [Tool1, Tool2]
---
```

But skills may include additional metadata:
```yaml
trigger-phrases: ["save this", "remember this"]
auto-invoke: true
```

## Best Practice

Start with slash commands (explicit). Promote to skills only when Claude should always have that knowledge/capability available.
