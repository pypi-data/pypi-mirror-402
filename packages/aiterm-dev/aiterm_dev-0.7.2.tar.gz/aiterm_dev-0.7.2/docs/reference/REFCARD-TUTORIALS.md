# Tutorial Commands Reference

Quick reference for aiterm interactive tutorial system.

## Commands

| Command | Description |
|---------|-------------|
| `ait learn` | List all available tutorials |
| `ait learn list` | List tutorials (alias) |
| `ait learn start <level>` | Start a tutorial |
| `ait learn start <level> -s N` | Resume from step N |
| `ait learn info <level>` | Show tutorial details without starting |

## Tutorial Levels

| Level | Steps | Duration | Focus |
|-------|-------|----------|-------|
| `getting-started` | 7 | ~10 min | Essential commands, basic setup |
| `intermediate` | 11 | ~20 min | Claude Code, workflows, sessions |
| `advanced` | 13 | ~35 min | Release automation, craft, integrations |

## Quick Start

```bash
# List available tutorials
ait learn

# Start the beginner tutorial
ait learn start getting-started

# Resume from step 5
ait learn start getting-started -s 5

# Preview tutorial content
ait learn info intermediate
```

## Getting Started Tutorial (7 Steps)

1. **What is aiterm?** - Overview and concepts
2. **Check Installation** - `ait doctor`
3. **View Configuration** - `ait config show`
4. **Detect Context** - `ait detect`
5. **Switch Profile** - `ait switch`
6. **Explore Commands** - `ait --help`
7. **Next Steps** - Where to go next

![Getting Started Demo](../demos/tutorials/getting-started-01-doctor.gif)

## Intermediate Tutorial (11 Steps)

1. **Claude Settings** - `ait claude settings`
2. **Backup Settings** - `ait claude backup`
3. **Approval Presets** - `ait claude approvals list`
4. **Add Approvals** - `ait claude approvals add safe`
5. **Workflow Basics** - `ait workflows list`
6. **Feature Workflow** - `ait feature status`
7. **Session Management** - `ait sessions live`
8. **Terminal Overview** - `ait terminal list`
9. **Detect Terminal** - `ait terminal detect`
10. **Ghostty Themes** - `ait ghostty themes`
11. **Status Bar** - `ait status-bar show`

![Intermediate Demo](../demos/tutorials/intermediate-01-claude.gif)

## Advanced Tutorial (13 Steps)

1. **Release Overview** - `ait release --help`
2. **Pre-Release Check** - `ait release check`
3. **Release Status** - `ait release status`
4. **Full Release** - `ait release full --help`
5. **Custom Workflows** - `ait workflows custom create`
6. **Workflow Chaining** - `lint+test+build`
7. **Craft Integration** - `ait craft status`
8. **Git Worktrees** - `/craft:git:worktree`
9. **MCP Servers** - `ait mcp list`
10. **IDE Integrations** - `ait ide list`
11. **Advanced Debug** - `ait info --json`
12. **Custom Config** - `ait config edit`
13. **Resources** - Next steps and links

![Advanced Demo](../demos/tutorials/advanced-01-release.gif)

## Visual Assets

### GIF Demos

All tutorials include animated GIF demonstrations:

| Tutorial | GIFs |
|----------|------|
| Getting Started | doctor, detect, switch |
| Intermediate | claude, workflows, sessions |
| Advanced | release, worktrees, craft |

Location: `docs/demos/tutorials/`

### Mermaid Diagrams

Visual diagrams explain key workflows:

| Diagram | Purpose |
|---------|---------|
| [Tutorial Flow](../diagrams/tutorial-flow.md) | 3-level progression |
| [Context Detection](../diagrams/context-detection.md) | How detection works |
| [Session Lifecycle](../diagrams/session-lifecycle.md) | Session start/stop |
| [Release Workflow](../diagrams/release-workflow.md) | Release automation |
| [Craft Integration](../diagrams/craft-integration.md) | Plugin integration |
| [Git Worktrees](../diagrams/worktree-flow.md) | Parallel development |

## Tips

### Resuming Tutorials

If you exit mid-tutorial, resume with:

```bash
ait learn start intermediate -s 5
```

### Navigation

During a tutorial:
- **Continue** - Move to next step
- **Repeat** - Show current step again
- **Skip** - Jump to specific step
- **Exit** - Save progress and quit

### Prerequisites

| Level | Requires |
|-------|----------|
| Getting Started | aiterm installed |
| Intermediate | Completed Getting Started |
| Advanced | Completed Intermediate |

## Related

- [All Commands](commands.md) - Complete command reference
- [REFCARD](../REFCARD.md) - Main quick reference
- [Craft Plugin](REFCARD-CRAFT.md) - AI workflow automation
