# .roadmap/

Local storage for product planning drafts before they're ready for Confluence.

## Structure

```
.roadmap/
├── README.md           # This file
└── drafts/             # Draft ideas, roadmap items, decisions
    └── *.md            # Individual draft files
```

## Draft Format

Each draft file uses YAML frontmatter:

```markdown
---
type: idea | roadmap-item | decision
category: Collections | Graph | Search | Quality | Agent | UI | Integrations | Analytics | Admin
status: draft
created: YYYY-MM-DD
confluence_section: [target section name in Confluence]
---

# Title

[Structured content based on type]
```

## Workflow

1. **Create draft:** Use `/roadmap idea` or `/roadmap refine`, choose "Save as local draft"
2. **Review drafts:** Use `/roadmap review drafts` to list all local drafts
3. **Promote to Confluence:** (v2 feature) - for now, copy content manually or re-run the command

## Why Local Drafts?

- Capture fleeting thoughts without cluttering Confluence
- Refine ideas over multiple sessions before publishing
- Keep work-in-progress separate from official planning docs
