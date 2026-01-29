# Intermediate Tutorial

**Duration:** ~20 minutes
**Steps:** 11
**Prerequisites:** Completed Getting Started tutorial

---

## Overview

Master Claude Code integration, workflow automation, and session management.

**What you'll learn:**

- Claude Code settings and backups
- Auto-approval presets
- Workflow automation
- Session coordination
- Terminal management

## Quick Start

```bash
ait learn start intermediate
```

---

## Step 1: Claude Code Settings

View your Claude Code configuration:

```bash
ait claude settings
```

![Claude Settings](../../demos/tutorials/intermediate-01-claude.gif)

**Settings location:** `~/.claude/settings.json`

---

## Step 2: Backup Your Settings

Before making changes, create a backup:

```bash
ait claude backup
```

Backups are timestamped and stored in `~/.claude/backups/`.

---

## Step 3: Auto-Approval Presets

View available presets:

```bash
ait claude approvals list
```

**Preset levels:**
| Preset | Risk Level | Commands |
|--------|------------|----------|
| `minimal` | Lowest | Read-only commands |
| `safe` | Low | Common dev tools |
| `moderate` | Medium | Build & test tools |
| `full` | Highest | Most commands |

---

## Step 4: Add Safe Approvals

Apply the safe preset:

```bash
ait claude approvals add safe
```

This enables auto-approval for:
- `git status`, `git diff`, `git log`
- `npm test`, `npm run`
- `pytest`, `ruff`
- And more...

---

## Step 5: Workflow Basics

See built-in workflows:

```bash
ait workflows list
```

![Workflows](../../demos/tutorials/intermediate-02-workflows.gif)

**Built-in workflows:**
- `test` - Run project tests
- `lint` - Check code style
- `build` - Build project
- `docs` - Build documentation

---

## Step 6: Feature Branch Workflow

Check feature workflow status:

```bash
ait feature status
```

**Feature workflow helps with:**
- Branch naming conventions
- Progress tracking
- Clean merges

---

## Step 7: Session Management

View active Claude Code sessions:

```bash
ait sessions live
```

![Sessions](../../demos/tutorials/intermediate-03-sessions.gif)

**Session commands:**
```bash
ait sessions current      # Current session
ait sessions task "desc"  # Set task description
ait sessions conflicts    # Check for conflicts
```

---

## Step 8: Terminal Management

See supported terminals:

```bash
ait terminal list
```

**Supported terminals:**
- iTerm2 (full support)
- Ghostty (full support)
- Terminal.app (basic)
- VS Code terminal (basic)

---

## Step 9: Detect Your Terminal

Identify your current terminal:

```bash
ait terminal detect
```

---

## Step 10: Ghostty Quick Themes

If using Ghostty, explore themes:

```bash
ait ghostty themes
```

Apply a theme:
```bash
ait ghost theme Dracula
```

---

## Step 11: Status Bar Customization

View status bar configuration:

```bash
ait status-bar show
```

The status bar shows:
- Project name and type
- Git branch and status
- Session duration
- Model info

---

## Summary

| Command | Purpose |
|---------|---------|
| `ait claude settings` | View Claude config |
| `ait claude backup` | Backup settings |
| `ait claude approvals add` | Add preset |
| `ait workflows list` | Show workflows |
| `ait sessions live` | Active sessions |

---

[← Back to Getting Started](../getting-started/index.md){ .md-button }
[Continue to Advanced →](../advanced/index.md){ .md-button .md-button--primary }
