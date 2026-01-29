# Feature Branch + Worktree Workflow Proposal

**Generated:** 2025-12-28
**Context:** aiterm / craft plugin integration
**Pattern:** `feature-a → dev → main` with parallel worktrees

## Overview

A comprehensive workflow combining:
1. **Feature branch discipline** - Enforces `feature → dev → main` progression
2. **Git worktrees** - Parallel development without branch switching
3. **ADHD-friendly** - No context loss, clear status, minimal decisions

---

## The Problems Solved

| Problem | Solution |
|---------|----------|
| Accidental main merges | Enforce dev→main only |
| Context switching overhead | Worktrees (no branch switch) |
| Lost uncommitted work | Each worktree is isolated |
| "Where was I?" confusion | Clear pipeline status |
| Stash juggling | No stashing needed |
| Dev server restarts | Each worktree runs independently |

---

## The Combined Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PARALLEL WORKTREES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ~/.git-worktrees/aiterm/                                                   │
│  ├── feature-auth/     ← Working on authentication                         │
│  ├── feature-ui/       ← Working on UI redesign                            │
│  └── hotfix-urgent/    ← Emergency fix                                     │
│                                                                             │
│  ~/projects/aiterm/    ← Main repo (stays on main or dev)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BRANCH PROGRESSION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    feature/auth ──┐                                                         │
│                   │     PR/merge      ┌───────┐     PR/merge      ┌──────┐ │
│    feature/ui ────┼───────────────────► dev   ├───────────────────► main │ │
│                   │                   └───────┘                   └──────┘ │
│    hotfix/urgent ─┘                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Proposed Commands

### aiterm Commands (CLI)

```bash
# === WORKTREE MANAGEMENT ===

# Start a new feature (creates worktree + branch from dev)
ait feature start my-feature
# Creates: ~/.git-worktrees/project/feature-my-feature
# Branch: feature/my-feature (from dev)

# Start a hotfix (creates worktree + branch from main)
ait feature hotfix urgent-fix
# Creates: ~/.git-worktrees/project/hotfix-urgent-fix
# Branch: hotfix/urgent-fix (from main)

# List all features with their worktree locations
ait feature list
# Shows: all feature branches, their worktrees, and pipeline status

# === PIPELINE MANAGEMENT ===

# Check status (where is each feature in the pipeline?)
ait feature status
# Shows: features in dev, features in main, pending PRs

# Sync current feature with latest dev
ait feature sync
# Rebases/merges dev into current feature branch

# Promote feature to dev (creates PR)
ait feature promote
# PR: feature/my-feature → dev

# Release dev to main
ait feature release
# PR: dev → main

# === CLEANUP ===

# Clean up merged features (worktrees + branches)
ait feature cleanup
# Removes worktrees for merged branches, prunes branches
```

### Craft Skills (Claude Code)

```bash
# Full worktree workflow
/craft:git:worktree setup              # First-time setup
/craft:git:worktree create <branch>    # Create worktree
/craft:git:worktree move               # Move current branch to worktree
/craft:git:worktree list               # List all worktrees
/craft:git:worktree clean              # Remove merged worktrees

# Feature workflow orchestration
/craft:git:feature start <name>        # Start + worktree + deps
/craft:git:feature promote --with-tests
/craft:git:feature release --changelog
```

---

## Options

### Option A: aiterm-First (Recommended)
**Effort:** 🔧 Medium (2-3 days)

```bash
# All commands under `ait feature`
ait feature start/hotfix/list/status/sync/promote/release/cleanup
```

**Pros:**
- Unified CLI experience
- Works outside Claude Code
- Shell aliases for quick access
- Integrates with `ait sessions`

**Cons:**
- Requires aiterm
- Separate from craft ecosystem

---

### Option B: Craft-First
**Effort:** 🔧 Medium (2-3 days)

```bash
# Feature workflow as craft skill
/craft:git:feature start my-feature --worktree
/craft:git:feature promote
```

**Pros:**
- Rich Claude Code integration
- Test automation before promote
- Changelog generation
- Mermaid diagrams for visualization

**Cons:**
- Only in Claude Code
- No shell access

---

### Option C: Hybrid (Both)
**Effort:** 🏗️ Large (4-5 days)

```bash
# aiterm for quick operations
ait feature start/status/cleanup

# craft for intelligent operations
/craft:git:feature promote --with-tests --changelog
```

**Pros:**
- Best of both worlds
- Right tool for right context
- Shared worktree folder structure

**Cons:**
- More to maintain
- Learning two interfaces

---

### Option D: Shell Aliases Only
**Effort:** ⚡ Quick (1-2 hours)

```bash
# Simple aliases
alias gfs='git checkout dev && git pull && git checkout -b feature/'
alias gfp='git push -u origin HEAD && gh pr create --base dev'
alias gfr='git checkout dev && gh pr create --base main'

# Worktree aliases
alias wt='cd ~/.git-worktrees'
alias wtc='_worktree_create'  # function wrapper
```

**Pros:**
- Immediate
- No dependencies
- Familiar to git users

**Cons:**
- No status/visualization
- No guardrails
- Easy to forget

---

## Recommended: Option A + D Bridge

Start with **shell aliases (D)** for immediate use, build toward **aiterm commands (A)** for v0.4.x:

```
Week 1: Shell aliases (immediate productivity)
   ↓
Week 2-3: ait feature status/list (visibility)
   ↓
Week 4+: Full command group (ait feature start/promote/release)
   ↓
v0.5.x: Craft integration (/craft:git:feature)
```

---

## Quick Wins (< 30 min each)

1. ⚡ **Shell aliases for feature branches:**
   ```bash
   # Add to ~/.config/zsh/functions/git-helpers.zsh
   alias gfs='git checkout dev && git pull && git checkout -b feature/'
   alias gfp='git push -u origin HEAD && gh pr create --base dev'
   alias gfr='git checkout dev && gh pr create --base main'
   ```

2. ⚡ **Worktree navigation aliases:**
   ```bash
   alias wt='cd ~/.git-worktrees'
   alias wtl='git worktree list'
   alias wtc='_git_worktree_create'  # wrapper function
   ```

3. ⚡ **GitHub branch protection:**
   - Settings → Branches → Add rule for `main`
   - Require PR, require status checks

4. ⚡ **Pre-push hook warning:**
   ```bash
   # ~/.config/git/hooks/pre-push
   if [ "$(git branch --show-current)" = "main" ]; then
       echo "⚠️  Pushing directly to main. Use gfr for releases."
   fi
   ```

---

## Medium Effort (1-2 hours each)

- [ ] `ait feature status` - Show pipeline visualization
- [ ] `ait feature list` - Show all features with worktree paths
- [ ] `ait feature cleanup` - Remove merged worktrees + branches
- [ ] GitHub Actions for branch enforcement

---

## Long-term (v0.4.x+)

- [ ] `ait feature start` - Create worktree + branch + install deps
- [ ] `ait feature sync` - Rebase with dev
- [ ] `ait feature promote` - Smart PR creation
- [ ] `ait feature release` - Dev → main with checks
- [ ] `/craft:git:feature` - Full Claude Code integration
- [ ] Auto-changelog generation
- [ ] Mermaid diagram of feature pipeline

---

## Folder Structure

```
~/.git-worktrees/                    # All worktrees here
├── aiterm/                          # Project folder
│   ├── feature-auth/                # feature/auth branch
│   ├── feature-ui/                  # feature/ui branch
│   └── hotfix-urgent/               # hotfix/urgent branch
├── scribe/
│   ├── feature-hud/
│   └── wonderful-wilson/
└── atlas/
    └── feature-api-v2/

~/projects/dev-tools/                # Original repos
├── aiterm/                          # Main repo (stays on main/dev)
├── scribe/
└── atlas/
```

---

## Example Complete Workflow

```bash
# 1. Start new feature with worktree
$ ait feature start user-auth
✓ Created worktree: ~/.git-worktrees/aiterm/feature-user-auth
✓ Created branch: feature/user-auth (from dev)
✓ Installed dependencies (npm install)
✓ Opened in new terminal tab

# 2. Work on feature in its worktree
$ cd ~/.git-worktrees/aiterm/feature-user-auth
$ claude  # Start Claude Code in worktree

# 3. Meanwhile, start another feature (parallel!)
$ ait feature start api-refactor
✓ Created worktree: ~/.git-worktrees/aiterm/feature-api-refactor
# Now you have TWO features in progress!

# 4. Check overall status
$ ait feature status
┌─ Feature Pipeline ────────────────────────────────────┐
│                                                       │
│  IN PROGRESS                                          │
│  ├── feature/user-auth (worktree)                    │
│  │   └── 5 commits ahead of dev                      │
│  └── feature/api-refactor (worktree)                 │
│      └── 2 commits ahead of dev                      │
│                                                       │
│  IN DEV (ready for release)                          │
│  ├── feature/logging (merged 2 days ago)             │
│  └── feature/config (merged 1 week ago)              │
│                                                       │
│  IN MAIN                                              │
│  └── v0.3.9 (released 1 day ago)                     │
│                                                       │
└───────────────────────────────────────────────────────┘

# 5. Promote user-auth to dev
$ cd ~/.git-worktrees/aiterm/feature-user-auth
$ ait feature promote
✓ Pushed to origin/feature/user-auth
✓ Created PR #42: feature/user-auth → dev
→ https://github.com/Data-Wise/aiterm/pull/42

# 6. After PR merged, release dev to main
$ ait feature release
✓ Created PR #43: dev → main
→ https://github.com/Data-Wise/aiterm/pull/43

# 7. Clean up merged features
$ ait feature cleanup
Merged worktrees found:
  - feature-user-auth (merged to dev)
Remove? [y/n] y
✓ Removed worktree: ~/.git-worktrees/aiterm/feature-user-auth
✓ Deleted branch: feature/user-auth
```

---

## Integration Points

### With aiterm

| aiterm Command | Feature Workflow Integration |
|----------------|------------------------------|
| `ait detect` | Detects worktree context |
| `ait sessions` | Tracks sessions per worktree |
| `ait switch` | Applies terminal profile for worktree |

### With Craft

| Craft Skill | Feature Workflow Integration |
|-------------|------------------------------|
| `/craft:git:worktree` | Foundation for worktree ops |
| `/craft:check commit` | Validate before promote |
| `/craft:git:sync` | Sync with upstream |

### With GitHub

| GitHub Feature | Configuration |
|----------------|---------------|
| Branch protection | Require dev→main only |
| Required checks | Tests must pass |
| CODEOWNERS | Review requirements |
| Actions | Enforce branch rules |

---

## Decision Matrix

| Scenario | Use Worktree? | Why |
|----------|---------------|-----|
| Quick typo fix | No | Too fast, just branch |
| Feature > 1 hour | **Yes** | Preserves context |
| Running dev server | **Yes** | Keeps server running |
| Parallel Claude Code sessions | **Yes** | Each session isolated |
| Hotfix during feature work | **Yes** | Don't interrupt feature |
| Not sure | **Yes** | Safer default |

---

## Related Resources

- **Existing:** `/craft:git:worktree` command
- **Guide:** `docs/guides/git-worktrees.md` (to create)
- **Shell:** `~/.config/zsh/functions/git-helpers.zsh`

---

## Next Steps

→ **Immediate:** Add shell aliases (Quick Win #1-2)
→ **This Week:** `ait feature status` command
→ **v0.4.x:** Full command group
→ **v0.5.x:** Craft integration

---

*Created: 2025-12-28*
*Status: Proposal*
*Integration: Feature branches + Worktrees*
