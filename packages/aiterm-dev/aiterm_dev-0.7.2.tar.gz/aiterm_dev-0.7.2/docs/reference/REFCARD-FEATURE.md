# Feature Workflow Quick Reference

Fast reference for `ait feature` commands.

---

## Commands

```bash
# Viewing
ait feature status              # Pipeline visualization
ait feature list                # List features (active only)
ait feature list --all          # List all (including merged)

# Creating
ait feature start <name>        # Create feature/<name> from dev
ait feature start <name> -w     # Create with worktree

# PR Workflow (v0.6.2+)
ait feature promote             # Create PR to dev
ait feature promote --draft     # Create as draft PR
ait feature release             # Create PR from dev to main
ait feature release --title "v1.0.0"

# Cleanup
ait feature cleanup             # Remove merged branches
ait feature cleanup -n          # Dry run (preview)
```

---

## Quick Start

```bash
# Start new feature with worktree
ait feature start auth-v2 --worktree
cd ~/.git-worktrees/myproject/auth-v2

# Work on feature... then create PR to dev
ait feature promote

# Check what's active
ait feature status

# When ready to release dev to main
git checkout dev
ait feature release

# After PR merged, cleanup
ait feature cleanup
```

---

## Options

### `ait feature start`

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--worktree` | `-w` | off | Create in worktree |
| `--no-install` | | off | Skip dep install |
| `--base` | `-b` | `dev` | Base branch |

### `ait feature promote` (v0.6.2+)

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--draft` | `-d` | off | Create as draft PR |
| `--title` | `-t` | branch name | Custom PR title |
| `--base` | `-b` | `dev` | Target branch |
| `--web` | `-w` | off | Open in browser |

### `ait feature release` (v0.6.2+)

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--draft` | `-d` | off | Create as draft PR |
| `--title` | `-t` | auto | PR title |
| `--body` | `-b` | auto | Custom PR body |
| `--web` | `-w` | off | Open in browser |

### `ait feature cleanup`

| Option | Short | Description |
|--------|-------|-------------|
| `--dry-run` | `-n` | Preview only |
| `--force` | `-f` | No confirmation |

---

## Branch States

| State | Symbol | Meaning |
|-------|--------|---------|
| **active** | `+N` | Has N commits ahead of dev |
| **new** | `(new)` | Just created, 0 commits |
| **merged** | `(merged)` | Ready for cleanup |

**Icons:** `●` current, `○` other, `📁` has worktree

---

## Worktree Paths

```
~/.git-worktrees/
└── <project>/
    └── <feature-name>/
```

---

## flow-cli Comparison

| Task | flow-cli | aiterm |
|------|----------|--------|
| Quick branch | `gfs name` | `ait feature start name` |
| Quick PR | `gfp` | `ait feature promote` |
| Release PR | - | `ait feature release` |
| Pipeline | - | `ait feature status` |
| Full setup | - | `ait feature start -w` |
| Cleanup | - | `ait feature cleanup` |

---

## See Also

- [Full Guide](../guide/feature-workflow.md)
- [Git Worktrees](../guides/GIT-WORKTREES-GUIDE.md)
- [Sessions](REFCARD-SESSIONS.md)
