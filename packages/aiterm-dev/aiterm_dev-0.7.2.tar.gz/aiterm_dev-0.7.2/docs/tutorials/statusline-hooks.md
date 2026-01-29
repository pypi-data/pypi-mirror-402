# StatusLine Hooks Tutorial (v2.1+)

**Duration:** 10 minutes • **Level:** Beginner-friendly • **What You'll Learn:** How to use pre-built hooks for automatic StatusLine updates

---

## TL;DR - Quick Start

```bash
# List available hooks
ait statusline hooks list

# Enable auto-theme-change (most popular)
ait statusline hooks add on-theme-change

# Enable remote session indicator
ait statusline hooks add on-remote-session

# Done! StatusLine now updates automatically
```

---

## What Are Hooks?

**Hooks** are small scripts that automatically run when specific events happen in Claude Code v2.1+.

**StatusLine Hooks** specifically respond to terminal and session events:

| Event | Hook | What It Does |
|-------|------|------------|
| Terminal theme changes | `on-theme-change` | Auto-swaps light/dark colors |
| Remote session starts | `on-remote-session` | Shows `[🌐 REMOTE]` indicator |
| Rendering error occurs | `on-error` | Displays ⚠️ alert |

### How They Work

```
Terminal Theme Changes (light → dark)
           ↓
on-theme-change hook runs
           ↓
StatusLine colors automatically update
           ↓
No action needed from you!
```

---

## Available Hooks

### 1. on-theme-change 🎨

**Auto-update StatusLine colors when terminal theme switches**

#### When It Runs
- When you change your iTerm2/terminal theme from light to dark (or vice versa)
- Automatically, without user action

#### What It Does
- Detects new terminal theme
- Picks matching light or dark color palette
- Updates StatusLine colors for readability
- Works silently in background

#### Use This Hook If
- ✅ You switch between light/dark terminal themes
- ✅ Colors look wrong after changing theme
- ✅ You want StatusLine to match your theme automatically
- ✅ You use iTerm2 with multiple color schemes

#### Install It
```bash
ait statusline hooks add on-theme-change
```

#### Test It
```bash
# Verify hook installed
ait statusline hooks validate

# Test the hook
ait statusline hooks test on-theme-change
```

#### What To Expect
After installation, the hook runs silently. If you change your terminal theme:
- StatusLine colors automatically update
- No restart needed
- No confirmation prompts

---

### 2. on-remote-session 🌐

**Show a remote indicator when using Claude Code's /teleport feature**

#### When It Runs
- When you activate a `/teleport` remote session
- When you exit remote mode

#### What It Does
- Detects that you're in a remote Claude Code session
- Adds `[🌐 REMOTE]` indicator to StatusLine
- Disappears when you exit remote mode
- Helps you always know if you're remote

#### Use This Hook If
- ✅ You use Claude Code's `/teleport` for remote development
- ✅ You SSH into remote machines and want visual confirmation
- ✅ You need to know at a glance if you're local or remote
- ✅ You frequently switch between local and remote sessions

#### Install It
```bash
ait statusline hooks add on-remote-session
```

#### Test It
```bash
# Verify hook installed
ait statusline hooks list --installed

# Test the hook
ait statusline hooks test on-remote-session
```

#### What To Expect
StatusLine will show `[🌐 REMOTE]` marker when:
- You're in a `/teleport` session
- You're working on a remote machine via Claude Code
- The marker automatically appears/disappears with session

#### Example Output
```
Local Session:
╭─ ░▒▓ 🐍 aiterm  main* ▓▒░
╰─ Sonnet 4.5 │ 🌅 10:30 │ ⏱ 5m

Remote Session:
╭─ ░▒▓ 🐍 aiterm  main* [🌐 REMOTE] ▓▒░
╰─ Sonnet 4.5 │ 🌅 10:30 │ ⏱ 5m
```

---

### 3. on-error ⚠️

**Alert when StatusLine rendering fails (opt-in safety monitoring)**

#### When It Runs
- When StatusLine encounters a rendering error
- Only alerts you (won't interfere with work)
- Throttled to avoid spam (max 1 alert per minute)

#### What It Does
- Monitors StatusLine rendering
- Shows ⚠️ alert if something goes wrong
- Provides error details for debugging
- Automatically throttles repeated errors

#### Use This Hook If
- ✅ You want safety monitoring (optional, not required)
- ✅ You're troubleshooting StatusLine issues
- ✅ You want to know if something breaks
- ✅ Recommended: Leave disabled unless you need it

#### Install It
```bash
ait statusline hooks add on-error
```

#### Enable It
By default, this hook is installed but **disabled** (opt-in safety):

```bash
# To enable error monitoring
ait statusline hooks enable on-error

# To disable it later
ait statusline hooks disable on-error
```

#### Test It
```bash
# Test the hook
ait statusline hooks test on-error

# Check if enabled
ait statusline hooks list --installed | grep on-error
```

#### What To Expect
If StatusLine rendering fails:
- You'll see ⚠️ alert in your terminal
- Alert includes error details
- Alert throttles after 1 per minute (avoids spam)
- StatusLine continues to work with fallback display

---

## Installation Workflow

### Step 1: Check Available Hooks

```bash
ait statusline hooks list
```

This shows all available StatusLine hook templates.

**Output Example:**
```
Available StatusLine Hooks (v2.1+):
  ✓ on-theme-change  - Auto-update colors on theme changes
  ✓ on-remote-session - Enable remote session indicator
  ✓ on-error         - Alert on rendering errors (opt-in)

Run: ait statusline hooks add <name> to install
```

### Step 2: Check What's Currently Installed

```bash
ait statusline hooks list --installed
```

This shows which hooks you already have.

**Output Example:**
```
Installed StatusLine Hooks:
  ✓ on-theme-change  (enabled)
  ✓ on-remote-session (enabled)
  ✗ on-error         (disabled)
```

### Step 3: Install a Hook

```bash
# Install theme-change hook
ait statusline hooks add on-theme-change

# Install remote-session hook
ait statusline hooks add on-remote-session

# Install error-monitoring hook
ait statusline hooks add on-error
```

### Step 4: Verify Installation

```bash
# Check all hooks are valid
ait statusline hooks validate

# Should see: ✓ All hooks are valid
```

### Step 5: Test Individual Hooks

```bash
# Test theme-change hook
ait statusline hooks test on-theme-change

# Test remote-session hook
ait statusline hooks test on-remote-session

# Test error monitoring
ait statusline hooks test on-error
```

---

## Managing Hooks

### List All Available Hooks

```bash
ait statusline hooks list
```

### List Installed Hooks

```bash
ait statusline hooks list --installed
```

Shows which hooks are installed and if they're enabled/disabled.

### Enable/Disable Hooks

```bash
# Enable a hook (allows it to run)
ait statusline hooks enable on-theme-change

# Disable a hook (installs but doesn't run)
ait statusline hooks disable on-error
```

### Remove a Hook

```bash
# Uninstall a hook completely
ait statusline hooks remove on-theme-change
```

### Validate All Hooks

```bash
# Check all hooks are working properly
ait statusline hooks validate

# Verbose check with details
ait statusline hooks validate --verbose
```

### Test Specific Hook

```bash
# Run hook and show output
ait statusline hooks test on-theme-change

# Verbose test with timing
ait statusline hooks test on-remote-session --verbose
```

---

## Common Workflows

### Setup: New User (Just Getting Started)

```bash
# 1. See what's available
ait statusline hooks list

# 2. Install the most popular one
ait statusline hooks add on-theme-change

# 3. That's it! Hook runs automatically
```

### Setup: Power User (Want Everything)

```bash
# Install all hooks
ait statusline hooks add on-theme-change
ait statusline hooks add on-remote-session
ait statusline hooks add on-error

# Verify they're working
ait statusline hooks validate

# Test each one
ait statusline hooks test on-theme-change
ait statusline hooks test on-remote-session
ait statusline hooks test on-error
```

### Troubleshooting: Hook Not Working

```bash
# 1. Verify installation
ait statusline hooks list --installed

# 2. Check if enabled
ait statusline hooks list --installed | grep on-theme-change

# 3. Test the hook
ait statusline hooks test on-theme-change

# 4. Check validation
ait statusline hooks validate

# 5. Check logs
cat ~/.claude/logs/claude-code.log | grep "statusline\|hook"
```

### Troubleshooting: Error Alerts Too Frequent

```bash
# Disable error monitoring hook
ait statusline hooks disable on-error

# Or remove it
ait statusline hooks remove on-error
```

### Cleanup: Remove All Hooks

```bash
ait statusline hooks remove on-theme-change
ait statusline hooks remove on-remote-session
ait statusline hooks remove on-error
```

---

## Hook File Locations

### Where Hooks Are Installed

```bash
~/.claude/hooks/statusline-*.sh
```

Example:
```bash
~/.claude/hooks/statusline-on-theme-change.sh
~/.claude/hooks/statusline-on-remote-session.sh
~/.claude/hooks/statusline-on-error.sh
```

### View Hook Script

```bash
# See what on-theme-change hook does
cat ~/.claude/hooks/statusline-on-theme-change.sh

# Edit hook (advanced)
vim ~/.claude/hooks/statusline-on-theme-change.sh
```

### Hook Index

```bash
# List of all hooks
cat ~/.claude/hooks/index.json
```

---

## Advanced: Understanding Hooks

### How Hooks Work Under the Hood

1. **Event Trigger** - Something happens (theme changes, session starts, etc.)
2. **Hook Activation** - Claude Code v2.1+ calls the matching hook script
3. **Execution** - Bash script runs with environment variables
4. **Result** - StatusLine updates or action taken
5. **Return** - Hook returns control to Claude Code

### Environment Variables Available to Hooks

When hooks run, they have access to:

```bash
$CLAUDE_CODE_VERSION     # Claude Code version
$CLAUDE_SESSION_ID       # Current session ID
$CLAUDE_THEME           # Current terminal theme
$CLAUDE_CWD             # Current working directory
$CLAUDE_PROJECT_TYPE    # Detected project type (py, node, r, etc.)
```

### Hook Script Format

All StatusLine hooks follow this structure:

```bash
#!/bin/bash
# Hook: [name]
# Description: What this hook does
# Requires: Claude Code v2.1+

# Safety check: Don't run if StatusLine not installed
[[ -f ~/.config/aiterm/statusline.json ]] || exit 1

# Get current settings
source ~/.config/aiterm/statusline.json

# Do the work
case "$1" in
    "enable")
        # Enable behavior
        ;;
    "disable")
        # Disable behavior
        ;;
    *)
        # Default action
        ;;
esac

# Exit codes:
# 0 = success (continue)
# 1 = error (log warning)
```

---

## Recommended Setup

### Minimal Setup (Start Here)

Install just the most popular hook:

```bash
ait statusline hooks add on-theme-change
```

This gives you auto-updating colors with zero maintenance.

### Standard Setup (Balanced)

Install two complementary hooks:

```bash
ait statusline hooks add on-theme-change
ait statusline hooks add on-remote-session
```

This covers most common use cases.

### Full Setup (Complete Feature Set)

Install all available hooks:

```bash
ait statusline hooks add on-theme-change
ait statusline hooks add on-remote-session
ait statusline hooks add on-error
```

This enables all functionality including error monitoring.

---

## Frequently Asked Questions

### Q: Do I need hooks to use StatusLine?

**A:** No. Hooks are completely optional. StatusLine works perfectly without any hooks. Hooks just add extra automatic behavior.

### Q: Will hooks slow down StatusLine?

**A:** No. Hooks run separately from StatusLine rendering (asynchronously). They don't affect performance.

### Q: Can I create my own hooks?

**A:** Yes! You can write custom hooks using bash. See the CLAUDE.md advanced section for details.

### Q: What if a hook has an error?

**A:** Most hooks gracefully fail and log errors. StatusLine continues working even if a hook breaks.

### Q: How do I know if a hook is running?

**A:** Run `ait statusline hooks test <name>` to test any hook manually.

### Q: Can I disable a hook temporarily?

**A:** Yes: `ait statusline hooks disable <name>`

Then re-enable: `ait statusline hooks enable <name>`

### Q: Will hooks work on all terminals?

**A:** Hooks are terminal-agnostic. They work on iTerm2, Terminal.app, Ghostty, and other terminals.

---

## Next Steps

### Learn More

- **Full Guide:** `docs/guide/statusline.md`
- **Quick Start:** `docs/guides/GETTING-STARTED-STATUSLINE.md`
- **Setup Gateway:** `docs/guides/STATUSLINE-PHASE1-TUTORIAL.md`
- **Features Overview:** `docs/guides/FEATURES-OVERVIEW-V0.7.0.md`
- **StatusLine Refcard:** `docs/reference/REFCARD-STATUSLINE.md`

### Explore Hooks

```bash
# List all available hooks
ait statusline hooks list

# Install and test one
ait statusline hooks add on-theme-change
ait statusline hooks test on-theme-change

# View hook source
cat ~/.claude/hooks/statusline-on-theme-change.sh
```

### Get Help

```bash
# Quick reference
ait statusline hooks --help

# Self-check
ait statusline doctor

# Validate hooks
ait statusline hooks validate
```

---

## Key Takeaways ✅

1. **Hooks are optional** - Use only what you need
2. **Most popular:** `on-theme-change` for auto color updates
3. **Good addition:** `on-remote-session` for visual confirmation
4. **Safety opt-in:** `on-error` for error monitoring
5. **Easy to manage** - Add, test, and remove as needed
6. **No performance impact** - Runs in background

---

**Ready to use hooks?** Run `ait statusline hooks list` to see what's available!

**Questions?** Check the FAQ above or run `ait statusline doctor` for diagnostics.

---

**Happy status lining! 🎉**
