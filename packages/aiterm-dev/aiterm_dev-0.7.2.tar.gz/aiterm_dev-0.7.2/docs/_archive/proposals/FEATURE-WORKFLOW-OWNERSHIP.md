# Feature Branch Workflow - Ownership Analysis

**Generated:** 2025-12-28
**Purpose:** Determine which components belong to aiterm vs flow-cli

---

## Project Missions

### aiterm
> AI Terminal Optimizer CLI for Claude Code, OpenCode, and Gemini CLI workflows

**Characteristics:**
- Python CLI (Typer + Rich)
- Claude Code integration (settings, hooks, sessions)
- Terminal profile management
- Cross-platform (pip/brew/uv)
- Installed as `ait` command

### flow-cli
> Pure ZSH plugin for ADHD-optimized workflow management

**Characteristics:**
- Pure ZSH (no Python/Node runtime)
- Shell aliases and functions
- Dispatchers (g, mcp, obs, qu, r, cc)
- Sub-10ms response time
- ADHD-friendly design

---

## Component Ownership Analysis

### Phase 0: Quick Wins

| Component | Best Fit | Reasoning |
|-----------|----------|-----------|
| **Feature branch aliases** (`gfs`, `gfp`, `gfr`) | ⭐ **flow-cli** | Pure shell aliases, fits `g` dispatcher pattern |
| **Worktree aliases** (`wt`, `wtl`, `wtc`) | ⭐ **flow-cli** | Pure shell functions, no Python needed |
| **Pre-push hook** | **flow-cli** | Shell script, git integration |
| **GitHub branch protection** | **Neither** | Project-level config |

### Phase 1: Visibility Commands

| Component | Best Fit | Reasoning |
|-----------|----------|-----------|
| **Feature status** (rich visualization) | ⭐ **aiterm** | Rich terminal output, Python |
| **Feature list** (worktree info) | **aiterm** | Complex data formatting |
| **Feature cleanup** | **Both?** | Simple version in flow-cli, rich in aiterm |

### Phase 2: Automation Commands

| Component | Best Fit | Reasoning |
|-----------|----------|-----------|
| **Feature start** (worktree + deps) | ⭐ **aiterm** | Project detection, dep install |
| **Feature sync** (rebase) | **flow-cli** | Simple git operation |
| **Feature promote** (PR creation) | **Both** | Simple: flow-cli, Rich: aiterm |
| **Feature release** (PR to main) | **Both** | Simple: flow-cli, Rich: aiterm |

### Phase 3: Integration

| Component | Best Fit | Reasoning |
|-----------|----------|-----------|
| **`/craft:git:feature`** | **craft plugin** | Claude Code specific |
| **Mermaid diagrams** | **craft plugin** | Documentation generation |

---

## Proposed Split

### flow-cli Gets: Shell-Native Operations

```bash
# New g dispatcher commands (git workflow)
g feature start <name>    # Quick branch creation
g feature sync            # Quick rebase
g promote                 # Quick PR to dev
g release                 # Quick PR to main

# New wt dispatcher (worktrees)
wt                        # Go to worktrees folder
wt list                   # List worktrees
wt create <branch>        # Create worktree
wt clean                  # Remove merged worktrees

# Or standalone aliases
gfs / gfp / gfr           # Feature shortcuts
```

**Why flow-cli:**
- Sub-10ms response (no Python startup)
- Matches existing dispatcher pattern
- Pure shell = zero dependencies
- ADHD-friendly (instant feedback)

### aiterm Gets: Rich Operations

```bash
# Rich visualization
ait feature status        # Pipeline diagram
ait feature list          # Detailed worktree info

# Complex automation
ait feature start <name>  # Full setup: branch + worktree + deps
ait feature cleanup       # Interactive cleanup with Rich UI

# Integration
ait feature promote       # With validation, PR templates
ait feature release       # With changelog, version bump
```

**Why aiterm:**
- Rich terminal output (tables, colors, boxes)
- Project type detection (Python/Node/R)
- Dependency installation
- Integration with `ait sessions`
- Cross-platform consistency

---

## The Layered Approach ⭐

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Claude Code Integration (craft plugin)                │
│  /craft:git:feature - AI-assisted, tests, changelog             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Rich CLI (aiterm)                                     │
│  ait feature - visualization, complex automation                │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Shell Commands (flow-cli)                             │
│  g feature / wt - instant, zero overhead                        │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight:** Users can use any layer based on need:
- Quick operation → `g promote` (flow-cli)
- Need visualization → `ait feature status` (aiterm)
- Full automation → `/craft:git:feature` (craft)

---

## Detailed Breakdown

### flow-cli Additions

#### Option A: Extend `g` Dispatcher

```bash
# In flow-cli/functions/_flow_g.zsh

g feature start <name>   # git checkout dev && git pull && git checkout -b feature/$name
g feature sync           # git fetch origin && git rebase origin/dev
g promote                # git push -u origin HEAD && gh pr create --base dev
g release                # git checkout dev && gh pr create --base main
g feature list           # git branch --list 'feature/*'
```

**Pros:** Fits existing pattern, discoverable via `g help`
**Cons:** `g` already has many subcommands

#### Option B: New `wt` Dispatcher

```bash
# In flow-cli/functions/_flow_wt.zsh

wt                       # cd ~/.git-worktrees
wt list                  # git worktree list
wt create <branch>       # Create worktree with deps
wt move                  # Move current branch to worktree
wt clean                 # Remove merged worktrees
wt help                  # Show help
```

**Pros:** Focused, clear purpose
**Cons:** New dispatcher to learn

#### Option C: Standalone Aliases (Simplest) ⭐

```bash
# In flow-cli/functions/git-helpers.zsh

# Feature branch shortcuts
alias gfs='git checkout dev && git pull && git checkout -b feature/'
alias gfh='git checkout main && git pull && git checkout -b hotfix/'
alias gfp='git push -u origin HEAD && gh pr create --base dev'
alias gfr='git checkout dev && gh pr create --base main'

# Worktree shortcuts
alias wt='cd ~/.git-worktrees'
alias wtl='git worktree list'

_wt_create() { ... }
alias wtc='_wt_create'
```

**Pros:** Simplest, fastest, no dispatcher overhead
**Cons:** Less discoverable

### aiterm Additions

```python
# src/aiterm/cli/feature.py

@app.command()
def status():
    """Show feature pipeline with Rich visualization"""
    # Parse git branches
    # Show worktree locations
    # Display rich table/panel

@app.command()
def start(name: str, no_worktree: bool = False):
    """Start feature with full automation"""
    # Detect project type
    # Create branch from dev
    # Create worktree (optional)
    # Install dependencies

@app.command()
def cleanup(dry_run: bool = False):
    """Interactive cleanup of merged features"""
    # Find merged branches
    # Show in rich table
    # Prompt for each
    # Remove worktrees + branches
```

---

## Recommended Split

### flow-cli (Immediate - Phase 0)

```bash
# Add to flow-cli/functions/git-feature.zsh

# Feature branch workflow
alias gfs='git checkout dev && git pull && git checkout -b feature/'
alias gfh='git checkout main && git pull && git checkout -b hotfix/'
alias gfp='git push -u origin HEAD && gh pr create --base dev'
alias gfr='git checkout dev && gh pr create --base main'
alias gfstatus='git log --oneline dev..HEAD'

# Worktree management
alias wt='cd ~/.git-worktrees'
alias wtl='git worktree list'
_wt_create() {
    local branch="$1"
    local project=$(basename $(git rev-parse --show-toplevel))
    local folder=$(echo "$branch" | tr '/' '-')
    mkdir -p ~/.git-worktrees/$project
    git worktree add ~/.git-worktrees/$project/$folder "$branch"
    echo "✅ Created: ~/.git-worktrees/$project/$folder"
}
alias wtc='_wt_create'

# Pre-push hook (install via flow doctor)
```

### aiterm (v0.4.x)

```python
# ait feature status     - Rich pipeline visualization
# ait feature list       - Detailed feature/worktree info
# ait feature start      - Full automation (branch + worktree + deps)
# ait feature cleanup    - Interactive merged branch cleanup
# ait feature promote    - Rich PR creation with templates
# ait feature release    - Dev→main with optional changelog
```

### craft plugin (v0.5.x)

```markdown
# /craft:git:feature start <name> --with-tests
# /craft:git:feature promote --run-checks
# /craft:git:feature release --changelog --version-bump
```

---

## Decision Matrix

| Need | Use | Command |
|------|-----|---------|
| Quick branch creation | flow-cli | `gfs my-feature` |
| Quick PR to dev | flow-cli | `gfp` |
| Quick worktree | flow-cli | `wtc feature/x` |
| See pipeline status | aiterm | `ait feature status` |
| Full feature setup | aiterm | `ait feature start` |
| Clean up merged | aiterm | `ait feature cleanup` |
| AI-assisted PR | craft | `/craft:git:feature promote` |

---

## Implementation Order

### Week 1: flow-cli Quick Wins
1. Add git-feature.zsh to flow-cli
2. Document in flow-cli README
3. Test aliases work

### Week 2-3: aiterm Visibility
1. Create `src/aiterm/cli/feature.py`
2. Implement `status` and `list` commands
3. Add tests

### Week 4+: aiterm Automation
1. Implement `start`, `cleanup`, `promote`, `release`
2. Integration with `ait sessions`

### Future: craft Integration
1. `/craft:git:feature` skill
2. AI-assisted PR creation
3. Auto-changelog

---

## Summary

| Tool | Role | Commands |
|------|------|----------|
| **flow-cli** | Quick shell operations | `gfs`, `gfp`, `gfr`, `wt*` |
| **aiterm** | Rich visualization + automation | `ait feature *` |
| **craft** | AI-assisted workflows | `/craft:git:feature` |

**Key Principle:** Each layer adds value without replacing the layer below.

---

*Created: 2025-12-28*
*Status: Analysis Complete*
