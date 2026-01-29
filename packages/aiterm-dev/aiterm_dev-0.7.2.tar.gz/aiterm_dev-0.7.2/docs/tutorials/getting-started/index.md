# Getting Started Tutorial

⏱️ **10 minutes** • 🟢 Beginner • ✓ 7 steps

> **TL;DR** (30 seconds)
> - **What:** Complete walkthrough of aiterm from installation to advanced features
> - **Why:** Master the basics in 10 minutes and start optimizing your workflow
> - **How:** Follow the 7-step tutorial with hands-on examples
> - **Next:** Move to [Intermediate Tutorial](../intermediate/index.md) for workflows and craft integration

**Prerequisites:** aiterm installed

---

## Overview

Learn the essential aiterm commands to optimize your terminal for AI-assisted development.

**What you'll learn:**

- What aiterm does and why it's useful
- How to verify your installation
- Project context detection
- Terminal profile switching
- Where to find help

## Quick Start

```bash
ait learn start getting-started
```

---

## Step 1: What is aiterm?

aiterm is a terminal optimizer for AI-assisted development. It:

- **Manages terminal profiles** - Visual context for different project types
- **Detects project context** - Automatically identifies R, Python, Node, etc.
- **Integrates with Claude Code** - Settings, hooks, auto-approvals
- **Supports multiple terminals** - iTerm2, Ghostty, and more

![aiterm Overview](../../demos/tutorials/getting-started-01-doctor.gif)

---

## Step 2: Check Your Installation

Verify aiterm is correctly installed:

```bash
ait doctor
```

**Expected output:**
- Terminal type detected
- Shell identified
- Python version shown
- aiterm version confirmed

!!! tip "All checks should pass"
    If any check fails, follow the suggestions in the output.

---

## Step 3: View Configuration

See your current aiterm settings:

```bash
ait config show
```

**Configuration locations:**
- Global: `~/.config/aiterm/config.toml`
- Project: `.aiterm.toml` (optional)

---

## Step 4: Detect Project Context

aiterm automatically detects your project type:

```bash
ait detect
```

![Context Detection](../../demos/tutorials/getting-started-02-detect.gif)

**Detection sources:**
| File | Project Type |
|------|--------------|
| `DESCRIPTION` | R package |
| `pyproject.toml` | Python |
| `package.json` | Node.js |
| `_quarto.yml` | Quarto |
| `go.mod` | Go |

---

## Step 5: Switch Terminal Profile

Apply the detected context to your terminal:

```bash
ait switch
```

![Profile Switch](../../demos/tutorials/getting-started-03-switch.gif)

This changes:
- Terminal colors/theme
- Tab title
- Status bar variables

---

## Step 6: Explore Commands

See all available commands:

```bash
ait --help
```

**Key command groups:**
- `ait claude` - Claude Code integration
- `ait sessions` - Session management
- `ait workflows` - Workflow automation
- `ait release` - Release commands

Each command has its own `--help`:
```bash
ait claude --help
```

---

## Step 7: Next Steps

Congratulations! You've learned the basics.

**Continue learning:**
```bash
ait learn start intermediate
```

**Explore on your own:**
- `ait claude settings` - View Claude Code config
- `ait sessions live` - See active sessions
- `ait workflows list` - Available workflows

---

## Summary

| Command | Purpose |
|---------|---------|
| `ait doctor` | Check installation |
| `ait config show` | View settings |
| `ait detect` | Detect project context |
| `ait switch` | Apply context to terminal |
| `ait --help` | List all commands |

---

[Continue to Intermediate →](../intermediate/index.md){ .md-button .md-button--primary }
