# Claude Code Slash Commands Guide

## What are Slash Commands?

Slash commands are custom prompt templates stored in the `.claude/commands/` directory. They appear in the slash menu (type `/`) and provide reusable workflows for common tasks.

## Creating a Slash Command

### File Structure
```
.claude/commands/
└── my-command.md
```

### YAML Frontmatter Format
```yaml
---
description: Brief description of what this command does
argument-hint: "[optional args]"
allowed-tools:
  - Read
  - Write
  - Bash
---

# Command Instructions

Your command instructions go here in markdown format.
```

## Best Practices

1. **Keep it focused** - Each command should do one thing well
2. **Use clear descriptions** - Users see this in the slash menu
3. **Specify allowed tools** - Restricts what the command can do
4. **Provide examples** - Show users how to use the command
5. **Handle errors gracefully** - Account for common failure modes

## Common Use Cases

- Code review workflows
- Automated testing routines
- Documentation generation
- File organization tasks
- Commit message generation
- Bug report creation

## Argument Handling

Use `$ARGUMENTS` keyword to accept parameters from invocation:

```bash
/my-command arg1 arg2
```

The command can then parse and use these arguments.
