# Mermaid Diagram Library

Reusable Mermaid diagrams for aiterm documentation.

## Usage

Embed in markdown files:

```markdown
<!-- Include diagram -->
--8<-- "docs/diagrams/tutorial-flow.md"
```

Or copy the mermaid code block directly.

## Diagrams

| File | Type | Purpose |
|------|------|---------|
| `tutorial-flow.md` | flowchart | Tutorial level progression |
| `context-detection.md` | flowchart | How context detection works |
| `session-lifecycle.md` | sequence | Session start/stop flow |
| `release-workflow.md` | flowchart | Release automation steps |
| `craft-integration.md` | flowchart | Plugin integration |
| `worktree-flow.md` | flowchart | Git worktree workflow |

## Styling Guidelines

- Use subgraphs for grouping related nodes
- Keep text short (< 20 chars per node)
- Use consistent colors via CSS classes
- Test rendering in MkDocs before committing
