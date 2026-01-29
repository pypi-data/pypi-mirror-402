# StatusLine Phase 1 Tutorial - Gateway Pattern & Hooks

**Version:** v0.7.0
**Status:** ✅ NEW Feature (Phase 1 Complete)
**Difficulty:** Beginner to Advanced
**Time:** 10-15 minutes

---

## Overview

StatusLine Phase 1 introduces two major improvements to eliminate configuration confusion:

1. **Gateway Pattern** - Single entry point for all customization
2. **Hook Templates** - Pre-built integrations with Claude Code v2.1

### Problem It Solves

**Before v0.7.0:** Users had 7+ different ways to configure statusline, causing confusion:
- Direct config editing
- Command-line flags
- Interactive menus
- Theme switching
- And more...

**Now:** Just use `ait statusline setup` for everything!

---

## Part 1: The Gateway Pattern ✨

### What is It?

The **gateway pattern** provides a single, friendly entry point that routes you to the right tool based on what you want to do.

### Try It Now

```bash
ait statusline setup
```

**Output:**

```
╭─────────────────────────────────────────────────────╮
│  StatusLine Configuration                          │
│  Choose what you'd like to do:                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Customize display options (git, time, etc.)    │
│  2. Change color theme (purple, blue, green)       │
│  3. Adjust spacing (minimal, standard, spacious)   │
│  4. Apply a preset configuration profile           │
│  5. View all current settings                      │
│  6. Edit raw config (advanced users)               │
│                                                     │
│  What would you like to do? [1]:                   │
╰─────────────────────────────────────────────────────╯
```

### Interactive Navigation

This menu is **smart and recursive**:
- Choose an option (e.g., "2. Change color theme")
- Make your changes
- Get asked "Done, or make another change?"
- Return to main menu or exit

### Example Workflow

```bash
$ ait statusline setup

What would you like to do? [1]: 2     # Choose theme change

Current theme: purple-charcoal

Available themes:
  1. purple-charcoal (default)
  2. cool-blues
  3. forest-greens

Which theme? [1]: 2                  # Pick cool-blues

✓ Theme changed to cool-blues

Done, or make another change? [y]: n # Exit to main menu

What would you like to do? [1]: 1    # Now customize display

Choose what to show:
  - Git branch
  - Files changed count
  - Session duration
  - Model name
  ... (more options)

# You edit these interactively
```

### Key Features

✅ **Guided** - Clear prompts, no confusion
✅ **Recursive** - Make multiple changes in one session
✅ **Non-destructive** - Preview before committing
✅ **Discoverable** - See all options in one place
✅ **Backward compatible** - Old commands still work

---

## Part 2: The Unified Menu

### Explore All Options at Once

```bash
ait statusline customize
```

Opens a **unified menu** combining:
- Display options (what to show)
- Theme selection (colors)
- Spacing adjustment (how wide)
- Advanced settings (for power users)

### Example: Customize Display

```bash
$ ait statusline customize

╭─ Display Options ────────────────────────────────────╮
│ What information would you like to show?            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Git Information:                                    │
│    ☑ Branch name          (main, feature/new-api)  │
│    ☑ Dirty status         (shows * when modified)  │
│    ☑ Ahead/behind remote  (⇡1 ⇣2)                  │
│    ☑ Stash count          (📦3)                     │
│    ☑ Worktree info        (🌳4 or (wt) marker)     │
│                                                      │
│  Session Information:                                │
│    ☑ Model name           (Claude 3.5 Sonnet)      │
│    ☑ Time of day          (🌅 10:30)                │
│    ☑ Session duration     (⏱ 5m 23s)               │
│    ☑ Files changed        (+123/-45)                │
│                                                      │
│  Environment:                                        │
│    ☑ Python environment   (py3.11)                 │
│    ☑ Project type icon    (🐍 for Python)          │
│                                                      │
╰──────────────────────────────────────────────────────╯
```

### Example: Adjust Spacing

```bash
Spacing Control:
  1. Minimal (1 space between elements)
  2. Standard (2 spaces, default)
  3. Spacious (3+ spaces)

Choose: [2]: 1

✓ Spacing set to minimal
Visual preview: [🐍 aiterm main*⇣2+45/-12]
```

### Example: Select Theme

```bash
Color Themes:
  1. purple-charcoal (official, default)
  2. cool-blues (calm, professional)
  3. forest-greens (nature, peaceful)
  4. custom (define your own)

Choose: [1]: 2

✓ Theme changed to cool-blues
```

---

## Part 3: Hook Templates (Bonus!)

### What Are Hooks?

**Hooks** are pre-built integrations that automatically update StatusLine based on events in Claude Code v2.1+.

### Available Hooks

#### 1. on-theme-change 🎨

**Auto-update StatusLine colors when your terminal theme changes.**

When you switch terminal themes (light ↔ dark), StatusLine automatically adapts its colors for readability.

**How to enable:**

```bash
ait statusline hooks list           # See available hooks
ait statusline hooks add on-theme-change    # Install it
ait statusline hooks enable on-theme-change # Activate it
```

**What it does:**
- Monitors terminal theme changes
- Swaps between light/dark color palettes
- No action needed from you!

#### 2. on-remote-session 🌐

**Show a remote indicator when using Claude Code's /teleport feature.**

When you're working in a remote Claude Code session, StatusLine shows a special marker so you always know you're remote.

**How to enable:**

```bash
ait statusline hooks add on-remote-session
ait statusline hooks enable on-remote-session
```

**What it does:**
- Detects `/teleport` sessions
- Shows `[🌐 REMOTE]` indicator
- Disappears when you exit remote mode

#### 3. on-error ⚠️

**Alert you if StatusLine rendering fails (opt-in).**

Optional safety hook - if StatusLine ever has issues, you'll see a warning to investigate.

**How to enable:**

```bash
ait statusline hooks add on-error
ait statusline hooks enable on-error
```

**Note:** Disabled by default since most users don't need it.

### Managing Hooks

```bash
# List all available hooks
ait statusline hooks list

# List installed hooks
ait statusline hooks list --installed

# View installed hook details
ait statusline hooks list --installed | grep on-theme-change

# Enable/disable hooks
ait statusline hooks enable on-theme-change
ait statusline hooks disable on-error

# Remove a hook
ait statusline hooks remove on-remote-session

# See how many steps until status
ait statusline hooks status
```

---

## Tutorial: Complete Configuration Workflow

Let's configure StatusLine from scratch!

### Step 1: Install StatusLine

```bash
# Update Claude Code settings to use aiterm StatusLine
ait statusline install

# Verify it worked
ait statusline test
```

### Step 2: Access the Gateway

```bash
ait statusline setup
```

### Step 3: Choose Your Theme

```
What would you like to do? [1]: 2
```

Select a theme:
- `1` - Purple-charcoal (default, recommended)
- `2` - Cool-blues (professional, calming)
- `3` - Forest-greens (nature theme)

### Step 4: Customize Display

```
What would you like to do? [1]: 1
```

Toggle what information to show. Suggestions:

**Minimal setup** (lean, fast):
```
☑ Branch name
☑ Dirty status
☑ Model name
☑ Session duration
```

**Full setup** (maximum info):
```
☑ All Git options
☑ All Session options
☑ All Environment info
```

### Step 5: Adjust Spacing

```
What would you like to do? [1]: 3
```

Choose:
- `1` - Minimal (compact)
- `2` - Standard (recommended, balanced)
- `3` - Spacious (wide, readable)

### Step 6: Test It

```bash
ait statusline test

# You should see your customized statusline!
╭─ ░▒▓ 🐍 aiterm (venv: py3.11)  main* ⇣2 ▓▒░
╰─ Sonnet 4.5 │ 🌅 10:30 │ ⏱ 5m
```

### Step 7: Optional - Add Hooks

```bash
# Install theme-change hook
ait statusline hooks add on-theme-change

# Install remote session hook
ait statusline hooks add on-remote-session

# List your installed hooks
ait statusline hooks list --installed
```

---

## Quick Commands Reference

### Gateway (Most Users)

```bash
ait statusline setup           # 6-option menu (start here!)
ait statusline customize       # Unified menu
ait statusline test            # Show mock output
ait statusline install         # Install to Claude Code
```

### Hooks (Power Users)

```bash
ait statusline hooks list       # See all available
ait statusline hooks list --installed  # See what you have
ait statusline hooks add NAME   # Install a hook
ait statusline hooks remove NAME # Uninstall
ait statusline hooks enable NAME  # Turn on
ait statusline hooks disable NAME # Turn off
```

### Advanced Configuration (If Needed)

```bash
# Direct config commands (still available)
ait statusline config list          # All settings
ait statusline config get KEY       # Get value
ait statusline config set KEY VALUE # Set value

# Edit config file directly (advanced)
ait statusline config edit          # JSON editor
```

---

## Troubleshooting

### StatusLine not showing?

1. Did you run `ait statusline install`?
2. Restart Claude Code: Close all sessions and reopen
3. Run `ait statusline test` to verify output

### Changes not taking effect?

```bash
# Refresh settings
ait statusline test              # See current state
ait statusline install --force   # Reinstall
```

### Want to reset to defaults?

```bash
# Reset to default configuration
ait statusline config set display.reset true

# Or just reinstall
ait statusline install
```

### Hook not working?

```bash
# Check hook status
ait statusline hooks list --installed

# Try enabling again
ait statusline hooks enable HOOK_NAME

# Check Claude Code logs
cat ~/.claude/logs/claude-code.log | grep statusline
```

---

## What's Next?

### Learn More

- **Full StatusLine Guide:** `docs/guide/statusline.md`
- **All Commands:** `ait --help` then `ait statusline --help`
- **Configuration Reference:** `docs/reference/statusline-reference.md`

### Try Advanced Features

- **Multiple Profiles:** Set different StatusLine configs per project
- **Custom Themes:** Define your own color scheme
- **Hook Scripting:** Write custom hooks for your workflow

### Get Help

```bash
# Self-check
ait statusline doctor

# See all options
ait statusline --help

# Show current state
ait statusline test --verbose
```

---

## Key Takeaways ✅

1. **Use `ait statusline setup`** for 95% of config needs
2. **Hooks are optional** - only enable what you use
3. **Everything is reversible** - safe to experiment
4. **Backward compatible** - old commands still work
5. **Phase 1 is just the beginning** - Phase 2 coming soon!

---

**Happy status lining! 🎉**

Questions? Run `ait statusline setup` and explore!
