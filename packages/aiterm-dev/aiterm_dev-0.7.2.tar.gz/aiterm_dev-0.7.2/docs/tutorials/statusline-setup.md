# Claude Code StatusLine Tutorial

Learn how to set up and customize the StatusLine for Claude Code CLI sessions.

## What You'll Learn

- Install and configure StatusLine
- Understand the 2-line display
- Customize themes and settings
- Use Ghostty progress bars (1.2.x)
- Troubleshoot common issues

## Prerequisites

- Claude Code installed
- aiterm installed (`brew install data-wise/tap/aiterm`)
- Basic terminal knowledge

## Part 1: Installation (5 min)

### Step 1: Install StatusLine

```bash
ait statusline install
```

This updates `~/.claude/settings.json` to use `ait statusline render`.

**Expected output:**

```
✓ StatusLine installed successfully

  Config: ~/.claude/settings.json
  Command: ait statusline render

Next: Start a new Claude Code session to see StatusLine!
```

### Step 2: Test the Installation

```bash
ait statusline test
```

You should see a 2-line status display with mock data.

### Step 3: Start Claude Code

Open a new Claude Code session. You should now see the StatusLine at the top!

## Part 2: Understanding the Display (10 min)

### Line 1: Project Context

```
╭─ ░▒▓ 🐍 aiterm (venv: py3.11)  main* ⇣2 ⇡1 ?3 📦5 🌳4 ▓▒░
```

**What each part means:**

- `🐍` - Project type (Python in this case)
- `aiterm` - Project name
- `(venv: py3.11)` - Python environment
- `main*` - Git branch (* = uncommitted changes)
- `⇣2` - 2 commits behind remote
- `⇡1` - 1 commit ahead of remote
- `?3` - 3 untracked files
- `📦5` - 5 stashed changes
- `🌳4` - 4 total worktrees

### Line 2: Session Info

```
╰─ Sonnet 4.5  │  🌅 10:30  │  ⏱ 5m 🟢  │  🤖2  │  +123/-45
```

**What each part means:**

- `Sonnet 4.5` - Current AI model
- `🌅 10:30` - Time of day + current time
- `⏱ 5m 🟢` - Session duration + activity level
- `🤖2` - 2 background agents running
- `+123/-45` - Lines added/removed

## Part 3: Customization (15 min)

### Step 4: Choose a Theme

List available themes:

```bash
ait statusline theme list
```

**Available themes:**

- `purple-charcoal` (default) - Purple + dark gray
- `cool-blues` - Blue tones
- `forest-greens` - Green tones

Apply a theme:

```bash
ait statusline theme set cool-blues
```

### Step 5: Adjust Spacing

Control the spacing between segments:

```bash
# Minimal spacing (compact)
ait statusline config spacing minimal

# Standard spacing (balanced) - default
ait statusline config spacing standard

# Spacious (wide)
ait statusline config spacing spacious
```

**Visual comparison:**

```
Minimal:  Sonnet 4.5 │ 11:46 │ ⏱ 5m │ +123/-45
Standard: Sonnet 4.5  │  11:46  │  ⏱ 5m  │  +123/-45
Spacious: Sonnet 4.5   │   11:46   │   ⏱ 5m   │   +123/-45
```

### Step 6: Configure Display Options

View all settings:

```bash
ait statusline config list
```

Toggle specific features:

```bash
# Hide lines changed
ait statusline config set display.show_lines_changed false

# Show output style always
ait statusline config set display.show_output_style always

# Hide Python environment
ait statusline config set project.detect_python_env false
```

## Part 4: Ghostty Features (10 min)

### Step 7: Enable Progress Bars (Ghostty 1.2.x)

If you're using Ghostty terminal, StatusLine automatically shows native progress bars!

**How it works:**

- **Lines added > removed**: Green progress bar (success)
- **Lines removed > added**: Red progress bar (error)
- **Percentage**: Based on ratio of changes

**No configuration needed** - automatically enabled when Ghostty is detected.

### Step 8: Verify Ghostty Integration

Check if you're running in Ghostty:

```bash
echo $TERM_PROGRAM
# Should output: ghostty
```

Test StatusLine with Ghostty features:

```bash
ait statusline test
```

Look for the progress bar visualization in the output!

## Part 5: Git Worktrees (10 min)

### Step 9: Understanding Worktree Display

If you use git worktrees for multi-branch workflows:

**In main directory:**

```
╭─ ░▒▓ 🐍 aiterm  main 🌳4 ▓▒░
```

Shows total worktree count (🌳4)

**In worktree directory:**

```
╭─ ░▒▓ 🐍 aiterm-feature (wt)  feature-auth 🌳4 ▓▒░
```

Shows `(wt)` marker + total count

### Step 10: Configure Worktree Display

```bash
# Enable (default)
ait statusline config set git.show_worktrees true

# Disable if you don't use worktrees
ait statusline config set git.show_worktrees false
```

## Part 6: Advanced Configuration (15 min)

### Step 11: Minimal Display

Create a clean, minimal status line:

```bash
ait statusline config set display.show_lines_changed false
ait statusline config set display.show_output_style never
ait statusline config set time.show_productivity_indicator false
ait statusline config set project.detect_python_env false
```

**Result:**

```
╭─ ░▒▓ 🐍 aiterm  main ▓▒░
╰─ Sonnet 4.5 │ 10:30 │ ⏱ 5m
```

### Step 12: Maximum Detail

Show everything available:

```bash
ait statusline config set git.show_stash_count true
ait statusline config set git.show_remote_status true
ait statusline config set project.detect_python_env true
ait statusline config set time.show_productivity_indicator true
ait statusline config set display.show_output_style always
```

**Result:**

```
╭─ ░▒▓ 🐍 aiterm (venv: py3.11)  main* ⇣2 ⇡1 ?3 📦5 🔗origin/main 🌳4 ▓▒░
╰─ Sonnet 4.5 │ 🧠 │ 🌅 10:30 │ ⏱ 5m 🟢 │ 🤖2 │ +123/-45 │ 📘learning
```

### Step 13: Edit Config Directly

For advanced customization:

```bash
ait statusline config edit
```

This opens `~/.config/aiterm/statusline.json` in your editor.

## Part 7: Troubleshooting (10 min)

### Step 14: StatusLine Not Showing

Check installation:

```bash
cat ~/.claude/settings.json | grep -A 3 statusLine
```

Should show:

```json
"statusLine": {
  "type": "command",
  "command": "ait statusline render"
}
```

Fix:

```bash
ait statusline install
```

### Step 15: Wrong Theme/Colors

Check current theme:

```bash
ait statusline theme show
```

Change theme:

```bash
ait statusline theme set purple-charcoal
```

### Step 16: Missing Git Info

Enable git features:

```bash
ait statusline config set git.show_ahead_behind true
ait statusline config set git.show_stash_count true
ait statusline config set git.show_worktrees true
```

## Quick Reference

### Essential Commands

```bash
# Installation
ait statusline install
ait statusline test

# Themes
ait statusline theme list
ait statusline theme set <name>

# Spacing
ait statusline config spacing minimal|standard|spacious

# Configuration
ait statusline config list
ait statusline config get <key>
ait statusline config set <key> <value>
ait statusline config reset [key]

# Advanced
ait statusline config edit
ait statusline uninstall
```

### Common Settings

```bash
# Display
display.show_git = true|false
display.show_lines_changed = true|false
display.show_session_duration = true|false
display.separator_spacing = minimal|standard|spacious

# Git
git.show_ahead_behind = true|false
git.show_stash_count = true|false
git.show_worktrees = true|false

# Project
project.detect_python_env = true|false

# Time
time.show_productivity_indicator = true|false
time.time_format = 24h|12h
```

## Next Steps

- Explore [StatusLine Guide](../guide/statusline.md) for complete documentation
- Check [StatusLine Flow Diagram](../diagrams/statusline-flow.md) for technical details
- Try different themes and spacing options
- Customize for your workflow

## Summary

You've learned how to:

- ✅ Install and configure StatusLine
- ✅ Understand the 2-line display
- ✅ Customize themes and spacing
- ✅ Use Ghostty progress bars
- ✅ Configure git worktree display
- ✅ Troubleshoot common issues

Enjoy your enhanced Claude Code experience! 🎨
