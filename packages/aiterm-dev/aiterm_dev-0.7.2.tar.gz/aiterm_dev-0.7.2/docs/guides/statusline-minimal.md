# Minimal StatusLine Guide

**Version:** v0.7.0+
**Date:** 2026-01-01

## Overview

The minimal statusLine redesign removes visual clutter while adding adaptive Powerlevel10k-style worktree display. This guide shows you how to use the new minimal preset and worktree features.

---

## What's New

### Removed (Bloat)
- ❌ Session duration (`⏱ 12m`)
- ❌ Current time (`14:32`)
- ❌ Lines changed (`+123/-45`)
- ❌ Battery indicator (`⚡84%`)
- ❌ Weekly usage stats (`W:11%`)

### Added (Context)
- ✅ Right-side worktree display (adaptive)
- ✅ Smart branch truncation (preserves start/end)
- ✅ Minimal preset command

---

## Quick Start

### Apply Minimal Preset

```bash
# One-command declutter
ait statusline config preset minimal

# Restart Claude Code to see changes
```

This instantly disables:
- Session duration
- Current time
- Lines changed
- Session usage
- Weekly usage
- Usage reset timer

---

## Visual Examples

### Main Branch (Minimal)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░
╰─ Sonnet 4.5
```

**Character count:** ~40 chars (down from ~80)
**Metrics:** 3 essential (model, project, git) instead of 8

---

### Worktree (Adaptive)
```
╭─ ░▒▓ 📁 aiterm  feature-auth ▓▒░                  ░▒▓ (wt) feature-auth ▓▒░
╰─ Sonnet 4.5
```

**Right-side display:** Worktree name + marker
**Adaptive:** Only shows when in a worktree
**Style:** Powerlevel10k reversed segments (`░▒▓ content ▓▒░`)

---

### Main with Worktrees (Optional)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░                               ░▒▓ 🌳 3 worktrees ▓▒░
╰─ Sonnet 4.5
```

**Right-side display:** Worktree count (when > 1)
**Use case:** Reminder that worktrees exist

---

## Smart Branch Truncation

### Before (Simple)
```
feature/authentication-sy...
```

**Problem:** Lost context (what does "sy" mean?)

### After (Smart)
```
feature/...stem-oauth2
```

**Better:** Preserves both "feature/" prefix AND "oauth2" suffix

### How It Works

```python
# Keeps first 10 chars + "..." + last 19 chars (for max_len=32)
"feature/authentication-system-oauth2-integration"
→ "feature/...stem-oauth2-integration"
```

**Config:**
```bash
# Adjust max length (default: 32)
ait statusline config set git.truncate_branch_length 40
```

---

## Configuration

### Presets

| Preset | Description |
|--------|-------------|
| `minimal` | Clean statusLine (no time-tracking bloat) |
| `default` | Restore all default settings |

```bash
# Apply preset
ait statusline config preset minimal

# Restore defaults
ait statusline config preset default
```

---

### Individual Settings

**Disable specific features:**
```bash
# Turn off session duration
ait statusline config set display.show_session_duration false

# Turn off current time
ait statusline config set display.show_current_time false

# Turn off lines changed
ait statusline config set display.show_lines_changed false
```

**Worktree settings:**
```bash
# Show worktree count/name (default: true)
ait statusline config set git.show_worktrees true

# Branch truncation length (default: 32)
ait statusline config set git.truncate_branch_length 40
```

---

## Worktree Workflow

### Creating Worktrees

```bash
# Create worktree for feature branch
git worktree add ../aiterm-feature feature/auth-system

# Switch to worktree directory
cd ../aiterm-feature

# StatusLine automatically shows worktree context
```

**StatusLine will display:**
```
╭─ ░▒▓ 📁 aiterm  feature/auth-system ▓▒░          ░▒▓ (wt) feature-auth-system ▓▒░
╰─ Sonnet 4.5
```

---

### Returning to Main

```bash
# Go back to main working directory
cd ~/projects/dev-tools/aiterm

# StatusLine shows minimal main display
```

**StatusLine will display:**
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░
╰─ Sonnet 4.5
```

---

## Customization

### Right-Side Colors

Right-side segments use dark gray by default:
- Background: ANSI 235
- Foreground: ANSI 245

**Future:** Theme-aware colors (coming in v0.8.0)

---

### Terminal Width Detection

The statusLine auto-detects terminal width for proper alignment.

**Fallback:** 120 columns if detection fails

**Test alignment:**
```bash
# Resize terminal window
# StatusLine should adapt automatically
ait statusline test
```

---

## Before/After Comparison

### Before (Bloated)
```
╭─ ░▒▓ 📁 aiterm (wt)  feature-auth ▓▒░
╰─ Sonnet 4.5 │ 14:32 │ ⏱ 12m │ +45/-12 │ ⚡84% W:11%
```

**Issues:**
- 80+ characters
- 8 metrics (5 unnecessary)
- `(wt)` marker on left (hard to notice)
- Time/duration clutter

---

### After (Minimal)

**Main:**
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░
╰─ Sonnet 4.5
```

**Worktree:**
```
╭─ ░▒▓ 📁 aiterm  feature-auth ▓▒░          ░▒▓ (wt) feature-auth ▓▒░
╰─ Sonnet 4.5
```

**Improvements:**
- 60 chars (main), 80 chars (worktree)
- 3 metrics (all essential)
- Worktree context prominent on right
- Clean, focused

---

## Troubleshooting

### Right-Side Not Showing

**Symptom:** Worktree context not appearing on right side

**Check:**
```bash
# Is worktree display enabled?
ait statusline config get git.show_worktrees

# Enable if needed
ait statusline config set git.show_worktrees true
```

---

### Terminal Too Narrow

**Symptom:** Right side gets cut off

**Cause:** Terminal width < 100 columns

**Solution:**
- Resize terminal wider
- Or: Right side automatically hidden (fallback)

**Future:** Vertical stacking for narrow terminals (coming in v0.8.0)

---

### Branch Names Still Truncated

**Symptom:** Branch names cut off even with smart truncation

**Solution:**
```bash
# Increase max length
ait statusline config set git.truncate_branch_length 40

# Or disable truncation (not recommended)
ait statusline config set git.truncate_branch_length 999
```

---

### Preset Not Applied

**Symptom:** `ait statusline config preset minimal` doesn't work

**Check:**
```bash
# Verify config file updated
cat ~/.config/aiterm/statusline.json

# Re-apply if needed
ait statusline config preset minimal

# Restart Claude Code (required)
```

---

## Advanced

### Config File Location

```bash
# XDG-compliant location
~/.config/aiterm/statusline.json

# Edit directly (not recommended)
ait statusline config edit
```

---

### Minimal Config JSON

```json
{
  "display": {
    "show_session_duration": false,
    "show_current_time": false,
    "show_lines_changed": false,
    "show_session_usage": false,
    "show_weekly_usage": false
  },
  "usage": {
    "show_reset_timer": false
  },
  "git": {
    "show_worktrees": true,
    "truncate_branch_length": 32
  }
}
```

---

### Programmatic Usage

```python
from aiterm.statusline.config import StatusLineConfig

# Apply minimal preset
config = StatusLineConfig()
config.set('display.show_session_duration', False)
config.set('display.show_current_time', False)
config.set('display.show_lines_changed', False)

# Enable worktree display
config.set('git.show_worktrees', True)
```

---

## FAQ

### Q: Can I keep some bloat metrics?

**A:** Yes! Just re-enable specific settings:
```bash
# Keep current time, but not duration
ait statusline config set display.show_current_time true
ait statusline config set display.show_session_duration false
```

---

### Q: Can I customize right-side colors?

**A:** Not yet. Theme-aware right-side colors coming in v0.8.0.

---

### Q: Will this work in tmux/screen?

**A:** Yes! Terminal width detection works in multiplexers. Fallback to 120 cols if detection fails.

---

### Q: Can I show worktree count in main branch?

**A:** Yes, it's automatic! When you have > 1 worktree, main branch shows:
```
░▒▓ 🌳 3 worktrees ▓▒░
```

---

## Related Commands

```bash
# View all config options
ait statusline config list

# Test statusLine rendering
ait statusline test

# Validate config
ait statusline config validate

# Health check
ait statusline doctor

# View theme colors
ait statusline theme show
```

---

## Changelog

### v0.7.0 (2026-01-01)

**Added:**
- Minimal preset command (`ait statusline config preset minimal`)
- Right-side Powerlevel10k worktree display
- Smart branch truncation (preserve start/end)
- Adaptive layout (main vs worktree)
- 24 comprehensive tests

**Removed:**
- Left-side `(wt)` marker (moved to right)

**Changed:**
- Branch truncation algorithm (now preserves context)

---

## See Also

- **StatusLine Configuration Reference:** See `ait statusline config --help`
- **StatusLine Spacing Guide:** [statusline-spacing.md](statusline-spacing.md)
- **Implementation Spec:** [SPEC-statusline-redesign-2026-01-01.md](../specs/SPEC-statusline-redesign-2026-01-01.md)
