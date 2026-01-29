# flow-cli Integration

aiterm and flow-cli work together in a layered architecture for developer workflows.

---

## The 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: craft plugin (Claude Code)                            │
│  /craft:git:feature - AI-assisted, tests, changelog             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: aiterm (Python CLI)                                   │
│  ait feature - rich visualization, complex automation           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: flow-cli (Pure ZSH)                                   │
│  g, wt, cc - instant (<10ms), zero overhead, ADHD-friendly      │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight:** Each layer adds value without replacing the layer below.

---

## When to Use Which

### Git Feature Branches

| Need | Tool | Command |
|------|------|---------|
| Quick branch creation | flow-cli | `g feature start <name>` |
| Quick PR to dev | flow-cli | `g promote` |
| Quick PR to main | flow-cli | `g release` |
| Quick cleanup | flow-cli | `g feature prune` |
| **Pipeline visualization** | aiterm | `ait feature status` |
| **Full setup (branch + worktree + deps)** | aiterm | `ait feature start -w` |
| **Interactive cleanup** | aiterm | `ait feature cleanup` |

### Git Worktrees

| Need | Tool | Command |
|------|------|---------|
| Navigate to worktrees | flow-cli | `wt` |
| Quick list | flow-cli | `wt list` |
| Quick create | flow-cli | `wt create <branch>` |
| Quick cleanup | flow-cli | `wt prune` |
| **Rich status view** | aiterm | `ait feature status` |
| **Full automation** | aiterm | `ait feature start -w` |

### MCP Servers

| Need | Tool | Command |
|------|------|---------|
| Quick list | flow-cli | `mcp` or `mcp list` |
| Quick test | flow-cli | `mcp test <name>` |
| Navigate to server | flow-cli | `mcp cd <name>` |
| Interactive picker | flow-cli | `mcp pick` |
| **Rich table view** | aiterm | `ait mcp list` |
| **Full validation** | aiterm | `ait mcp validate` |
| **Server info** | aiterm | `ait mcp info <name>` |

### Terminal Management

| Need | Tool | Command |
|------|------|---------|
| Set tab title | flow-cli | `tm title <text>` |
| Switch profile (instant) | flow-cli | `tm profile <name>` |
| Which terminal? | flow-cli | `tm which` |
| **Context detection** | aiterm (via tm) | `tm detect` → `ait detect` |
| **Apply context** | aiterm (via tm) | `tm switch` → `ait switch` |
| **Ghostty status** | aiterm (via tm) | `tm ghost` → `ait ghost` |

### Claude Code

| Need | Tool | Command |
|------|------|---------|
| Launch Claude | flow-cli | `cc` |
| YOLO mode | flow-cli | `cc yolo` |
| With Opus | flow-cli | `cc opus` |
| Pick project | flow-cli | `cc pick` |
| In worktree | flow-cli | `cc wt <branch>` |
| **Settings management** | aiterm | `ait claude settings` |
| **Backup settings** | aiterm | `ait claude backup` |
| **Auto-approvals** | aiterm | `ait claude approvals` |
| **Hook management** | aiterm | `ait hooks install` |

### Sessions

| Need | Tool | Command |
|------|------|---------|
| Start session | flow-cli | `work <project>` |
| End session | flow-cli | `finish` |
| Quick switch | flow-cli | `hop <project>` |
| Log win | flow-cli | `win <text>` |
| **Live sessions** | aiterm | `ait sessions live` |
| **Session conflicts** | aiterm | `ait sessions conflicts` |
| **Session history** | aiterm | `ait sessions history` |

---

## Delegation Pattern

flow-cli's `tm` dispatcher delegates to aiterm for rich operations:

```bash
tm ghost   →  ait ghost      # Ghostty terminal status
tm detect  →  ait detect     # Project context detection
tm switch  →  ait switch     # Apply context to terminal
```

This keeps `tm` instant for simple operations while leveraging aiterm's Rich output for detailed views.

---

## Design Principles

### flow-cli Owns:
1. **Instant operations** (<10ms response, pure ZSH)
2. **Session management** (work/finish/hop)
3. **ADHD motivation** (win/yay/streaks/goals)
4. **Quick navigation** (pick/dash)
5. **Simple dispatchers** (g/cc/mcp/r/qu/obs/wt/tm)

### aiterm Owns:
1. **Rich visualization** (tables, panels, trees via Rich)
2. **Complex automation** (deps install, multi-step workflows)
3. **Claude Code integration** (settings, hooks, approvals, MCP)
4. **Terminal configuration** (profiles, themes, fonts)
5. **Session tracking** (live sessions, conflicts, history)
6. **Workflow templates** (full workflow management)
7. **IDE integrations** (VS Code, Cursor, Zed, Positron, Windsurf)

---

## Installation

### flow-cli

```bash
# Via plugin manager (antidote, zinit, oh-my-zsh)
# Add to ~/.zsh_plugins.txt:
Data-Wise/flow-cli
```

### aiterm

```bash
# Homebrew (macOS)
brew install data-wise/tap/aiterm

# Or cross-platform
pip install aiterm-dev
```

---

## Example Workflows

### Feature Development (Layered)

```bash
# Layer 1: Quick start (flow-cli)
g feature start auth

# Layer 2: Full setup with worktree (aiterm)
ait feature start auth --worktree

# Layer 1: Quick commits (flow-cli)
g commit "feat: add auth"
g push

# Layer 2: Check pipeline (aiterm)
ait feature status

# Layer 1: Quick PR (flow-cli)
g promote

# Layer 2: Cleanup (aiterm)
ait feature cleanup
```

### MCP Server Check (Layered)

```bash
# Layer 1: Quick check (flow-cli)
mcp test filesystem

# Layer 2: Full validation (aiterm)
ait mcp validate

# Layer 1: Navigate to fix (flow-cli)
mcp cd filesystem
```

---

## Links

### flow-cli Resources
- **Repository:** [github.com/Data-Wise/flow-cli](https://github.com/Data-Wise/flow-cli)
- **Documentation:** [data-wise.github.io/flow-cli](https://data-wise.github.io/flow-cli/)

### Dispatcher Reference Pages
| Dispatcher | Reference |
|------------|-----------|
| `g` (Git) | [G-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/G-DISPATCHER-REFERENCE/) |
| `mcp` | [MCP-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/MCP-DISPATCHER-REFERENCE/) |
| `cc` (Claude) | [CC-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/CC-DISPATCHER-REFERENCE/) |
| `wt` (Worktree) | [WT-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/WT-DISPATCHER-REFERENCE/) |
| `tm` (Terminal) | [TM-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/TM-DISPATCHER-REFERENCE/) |
| `r` (R Package) | [R-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/R-DISPATCHER-REFERENCE/) |
| `qu` (Quarto) | [QU-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/QU-DISPATCHER-REFERENCE/) |
| `obs` (Obsidian) | [OBS-DISPATCHER-REFERENCE.md](https://data-wise.github.io/flow-cli/reference/OBS-DISPATCHER-REFERENCE/) |

### aiterm Resources
- **Repository:** [github.com/Data-Wise/aiterm](https://github.com/Data-Wise/aiterm)
- **craft plugin:** Claude Code plugin for AI-assisted workflows
