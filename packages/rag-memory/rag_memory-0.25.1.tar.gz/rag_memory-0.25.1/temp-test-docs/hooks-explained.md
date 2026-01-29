# Claude Code Hooks Explained

## What are Hooks?

Hooks are user-defined shell commands that execute automatically at specific points in Claude Code's lifecycle. They provide deterministic, app-level control over Claude's behavior.

## Hook Types and Events

### PreToolUse
Fires **before** a tool call is executed. Perfect for:
- Validating commands against patterns
- Auto-approving safe operations
- Blocking dangerous operations
- Modifying tool inputs

### PostToolUse
Fires **after** a tool completes successfully. Useful for:
- Auto-formatting code files
- Logging operations
- Providing feedback to Claude

### PermissionRequest
Fires when a permission dialog is shown. Enables:
- Auto-allow/deny based on rules
- Custom permission logic

### UserPromptSubmit
Fires when user submits a prompt. Can:
- Add context automatically
- Validate prompts
- Block certain prompt patterns

## Configuration

Hooks are defined in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/hook-script.py",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## Hook Script Format

Hooks receive JSON via stdin:
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /",
    "description": "..."
  },
  "tool_use_id": "toolu_123"
}
```

Return decision via exit code or JSON:
- Exit 0 = allow
- Exit 2 = block
- JSON with `"permissionDecision": "ask"` = show UI confirmation

## Real-World Example: File Protection

```python
#!/usr/bin/env python3
import json, sys

data = json.load(sys.stdin)
path = data.get('tool_input', {}).get('file_path', '')

# Block edits to sensitive files
blocked = ['.env', 'package-lock.json', '.git/']
if any(p in path for p in blocked):
    sys.exit(2)  # Block

sys.exit(0)  # Allow
```

## Key Limitations

- Cannot create custom interactive prompts
- Cannot read stdin for user input (only JSON)
- Best option: Use `"permissionDecision": "ask"` for approval
- 60-second default timeout
- Multiple matching hooks run in parallel
