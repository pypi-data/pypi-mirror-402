# Advanced Tutorial

**Duration:** ~35 minutes
**Steps:** 13
**Prerequisites:** Completed Intermediate tutorial, familiarity with git

---

## Overview

Master release automation, craft integration, and power user techniques.

**What you'll learn:**

- Release workflow automation
- Custom workflow creation
- Craft plugin integration
- Git worktrees for parallel development
- MCP server management
- IDE integrations

## Quick Start

```bash
ait learn start advanced
```

---

## Step 1: Release Automation Overview

aiterm includes 7 release commands:

```bash
ait release --help
```

![Release Overview](../../demos/tutorials/advanced-01-release.gif)

**Commands:**
| Command | Purpose |
|---------|---------|
| `check` | Pre-release validation |
| `status` | Version & pending commits |
| `notes` | Generate release notes |
| `tag` | Create git tag |
| `pypi` | Publish to PyPI |
| `homebrew` | Update Homebrew formula |
| `full` | Complete release workflow |

---

## Step 2: Pre-Release Validation

Before releasing, validate everything:

```bash
ait release check
```

This verifies:
- Version consistency across files
- Tests pass
- Changelog updated
- Git status clean

---

## Step 3: Release Status & Notes

Check current status:

```bash
ait release status
```

Generate release notes:

```bash
ait release notes
```

---

## Step 4: Full Release Workflow

Understand the complete workflow:

```bash
ait release full --help
```

!!! tip "Always use --dry-run first"
    ```bash
    ait release full 0.6.0 --dry-run
    ```

---

## Step 5: Custom Workflow Creation

Create your own workflows:

```bash
ait workflows custom create my-workflow
```

Workflows are stored in `~/.config/aiterm/workflows/` as YAML files.

**Example workflow:**
```yaml
name: my-workflow
description: My custom workflow
steps:
  - name: lint
    command: ruff check .
  - name: test
    command: pytest
```

---

## Step 6: Workflow Chaining

Chain multiple workflows with `+`:

```bash
ait workflows run lint+test+build --dry-run
```

Chaining:
- Runs workflows in sequence
- Stops on first failure
- Great for pre-commit checks

---

## Step 7: Craft Integration Overview

Craft extends aiterm with 68 commands:

```bash
ait craft status
```

![Craft Integration](../../demos/tutorials/advanced-03-craft.gif)

**Key craft commands:**
- `/craft:docs:guide` - Generate documentation
- `/craft:docs:demo` - Create GIF demos
- `/craft:check release` - Pre-release audit
- `/craft:orchestrate` - Multi-agent workflows

---

## Step 8: Craft Git Worktrees

Work on multiple branches simultaneously:

```bash
# One-time setup
/craft:git:worktree setup

# Create a worktree
/craft:git:worktree create feature/new-feature

# List all worktrees
/craft:git:worktree list

# Complete and clean up
/craft:git:worktree finish
```

![Git Worktrees](../../demos/tutorials/advanced-02-worktrees.gif)

---

## Step 9: MCP Server Management

View configured MCP servers:

```bash
ait mcp list
```

**MCP commands:**
```bash
ait mcp status     # Check server health
ait mcp test NAME  # Test specific server
ait mcp validate   # Validate configuration
```

---

## Step 10: IDE Integrations

See supported IDEs:

```bash
ait ide list
```

**Supported IDEs:**
- VS Code
- Cursor
- Zed
- Positron
- Windsurf

Configure integration:
```bash
ait ide configure vscode
```

---

## Step 11: Advanced Debugging

Get detailed diagnostics:

```bash
ait info --json
```

This outputs:
- System information
- Dependency versions
- Tool availability
- Path configurations

---

## Step 12: Custom Configurations

Edit configuration directly:

```bash
ait config edit
```

**Configuration options:**
- Default terminal
- Profile mappings
- Status bar customization
- Workflow defaults

See [Configuration Reference](../../reference/configuration.md) for all options.

---

## Step 13: Next Steps & Resources

Congratulations! You're now a power user.

**Resources:**
- [GitHub](https://github.com/Data-Wise/aiterm)
- [Documentation](https://data-wise.github.io/aiterm)
- [Craft Plugin Reference](../../reference/REFCARD-CRAFT.md)

**Keep learning:**
- Check `ait --help` regularly for new features
- Explore `/craft:hub` for all craft commands
- Join discussions on GitHub

---

## Summary

| Command | Purpose |
|---------|---------|
| `ait release check` | Pre-release validation |
| `ait release full` | Complete release |
| `ait workflows custom create` | Custom workflows |
| `ait craft status` | Craft integration |
| `ait mcp list` | MCP servers |

---

[← Back to Intermediate](../intermediate/index.md){ .md-button }
[View All Tutorials](../index.md){ .md-button .md-button--primary }
