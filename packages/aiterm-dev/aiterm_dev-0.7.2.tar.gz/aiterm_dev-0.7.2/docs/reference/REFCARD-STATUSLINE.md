# StatusLine Commands Quick Reference

**Version:** v0.7.0+
**Last Updated:** 2026-01-17

---

## Quick Start

```bash
# Gateway to customization (NEW - START HERE!)
ait statusline setup

# Or jump directly to unified menu
ait statusline customize

# Preview current settings
ait statusline test
```

---

## Essential Commands

### Installation & Setup

```bash
# Install StatusLine into Claude Code
ait statusline install

# Test with mock data
ait statusline test

# System health check
ait statusline doctor

# Reset to defaults
ait statusline install --reset
```

### Configuration Gateway (v0.7.0)

```bash
# Interactive menu with 6 options
ait statusline setup
# → 1. Customize display
# → 2. Change theme
# → 3. Adjust spacing
# → 4. Apply preset
# → 5. View all settings
# → 6. Edit raw config

# All options in one place
ait statusline customize
```

### Theme Management

```bash
# List available themes
ait statusline theme list

# Set current theme
ait statusline theme set cool-blues

# Show current theme
ait statusline theme show

# Available themes: purple-charcoal, cool-blues, forest-greens
```

### Configuration (Power Users)

```bash
# List all settings
ait statusline config list

# Get specific setting value
ait statusline config get display.show_git

# Set specific value
ait statusline config set display.show_git false
ait statusline config set spacing.mode minimal

# Edit interactively with fzf
ait statusline config set --interactive

# View raw config file
cat ~/.config/aiterm/statusline.json
```

### Presets (Quick Templates)

```bash
# Apply preset configuration
ait statusline config preset minimal     # Git + Model only
ait statusline config preset standard    # Balanced (default)
ait statusline config preset full        # Everything
ait statusline config preset focused     # Time + Duration
```

---

## Hook Templates (v2.1+)

### Available Hooks

| Hook | Purpose | Default |
|------|---------|---------|
| `on-theme-change` | Auto-update colors when terminal theme changes | Enabled |
| `on-remote-session` | Show indicator during /teleport sessions | Enabled |
| `on-error` | Alert when statusline rendering fails | Disabled (opt-in) |

### Hook Commands

```bash
# List available hook templates
ait statusline hooks list

# List installed hooks
ait statusline hooks list --installed

# Install a hook template
ait statusline hooks add on-theme-change
ait statusline hooks add on-remote-session
ait statusline hooks add on-error

# Remove installed hook
ait statusline hooks remove on-theme-change

# Enable/disable hook
ait statusline hooks enable on-theme-change
ait statusline hooks disable on-error

# Validate all installed hooks
ait statusline hooks validate

# Test specific hook
ait statusline hooks test on-theme-change
```

---

## Display Settings

### Git Information

```bash
# Show/hide git branch name
ait statusline config set display.show_git true

# Show asterisk when files modified
ait statusline config set display.show_dirty true

# Show commits ahead/behind remote
ait statusline config set display.show_ahead_behind true

# Show stash count
ait statusline config set display.show_stash true

# Show git worktrees
ait statusline config set display.show_worktrees true
```

### Session Information

```bash
# Show AI model name (Sonnet, Opus, etc.)
ait statusline config set display.show_model true

# Show current time
ait statusline config set display.show_time true

# Show session duration
ait statusline config set display.show_duration true

# Show lines changed (+/-)
ait statusline config set display.show_files_changed true
```

### Environment Information

```bash
# Show Python version
ait statusline config set display.show_environment true

# Show project type icon
ait statusline config set display.show_icon true
```

### Spacing Control

```bash
# Set spacing mode
ait statusline config set spacing.mode minimal    # 1 space
ait statusline config set spacing.mode standard   # 2 spaces (default)
ait statusline config set spacing.mode spacious   # 3+ spaces
```

---

## Common Tasks

### Change Color Theme

```bash
# Interactive theme selection
ait statusline setup
# → Choose option 2: Change theme

# Or direct command
ait statusline theme set cool-blues
```

### Make It Minimal (Lean & Fast)

```bash
ait statusline config preset minimal
```

This shows only: Git branch + AI model name

### Show Maximum Information

```bash
ait statusline config preset full
```

This enables all available settings

### Hide Specific Information

```bash
# Hide time (just show other info)
ait statusline config set display.show_time false

# Hide lines changed
ait statusline config set display.show_files_changed false

# Hide session duration
ait statusline config set display.show_duration false
```

### Enable Theme Auto-Update Hook

```bash
# Automatically update colors when terminal theme changes
ait statusline hooks add on-theme-change
```

### Enable Remote Session Indicator

```bash
# Show [🌐 REMOTE] when using /teleport
ait statusline hooks add on-remote-session
```

### Test Your Settings

```bash
# Preview with mock data
ait statusline test

# Verbose output with details
ait statusline test --verbose
```

### Reset Everything to Defaults

```bash
ait statusline install --reset
```

---

## Settings Reference

### All Available Settings

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `display.show_git` | bool | true | Git branch & status |
| `display.show_dirty` | bool | true | Modified files indicator (*) |
| `display.show_ahead_behind` | bool | true | Commits ahead/behind remote |
| `display.show_stash` | bool | true | Stash count |
| `display.show_worktrees` | bool | true | Git worktree info |
| `display.show_model` | bool | true | AI model name |
| `display.show_time` | bool | true | Current time |
| `display.show_duration` | bool | true | Session duration |
| `display.show_files_changed` | bool | true | Lines changed (+/-) |
| `display.show_environment` | bool | true | Python/Node version |
| `display.show_icon` | bool | true | Project type icon |
| `theme.name` | string | `purple-charcoal` | Color theme |
| `spacing.mode` | string | `standard` | Element spacing |

### Settings by Category

#### Git Settings (display.*)
- `show_git` - Main branch display
- `show_dirty` - Dirty status indicator
- `show_ahead_behind` - Remote sync status
- `show_stash` - Stash count
- `show_worktrees` - Worktree indicators

#### Session Settings (display.*)
- `show_model` - AI model name
- `show_time` - Time of day
- `show_duration` - Session duration
- `show_files_changed` - File change statistics

#### Environment Settings (display.*)
- `show_environment` - Python/Node versions
- `show_icon` - Project type icon

#### Theme Settings (theme.*)
- `name` - Current color theme

#### Spacing Settings (spacing.*)
- `mode` - Display width (minimal/standard/spacious)

---

## Configuration Files

### Main Configuration

```bash
# Configuration file location
~/.config/aiterm/statusline.json

# View raw config
cat ~/.config/aiterm/statusline.json

# Edit config directly (advanced)
vim ~/.config/aiterm/statusline.json
```

### Hook Installation

```bash
# Hook templates directory
~/.claude/hooks/

# Installed statusline hooks
~/.claude/hooks/statusline-*.sh
```

---

## Troubleshooting

### StatusLine Not Showing

```bash
# Reinstall
ait statusline install

# Verify installation
ait statusline test

# Check health
ait statusline doctor
```

### Changes Not Taking Effect

```bash
# Reload settings
ait statusline test

# Force reinstall
ait statusline install --force

# Restart Claude Code (close all sessions and reopen)
```

### Hook Issues

```bash
# Check hook status
ait statusline hooks validate

# Test specific hook
ait statusline hooks test on-theme-change

# Check logs
cat ~/.claude/logs/claude-code.log | grep statusline
```

---

## Keyboard Shortcuts (Interactive Menus)

- **Arrow keys** - Navigate options
- **Enter** - Select option
- **1-9** - Quick number selection
- **Ctrl+C** - Exit without saving
- **Tab** - Toggle checkboxes

---

## Related Commands

```bash
# Show all commands
ait statusline --help

# Get help for specific command
ait statusline setup --help
ait statusline customize --help
ait statusline hooks --help

# System information
ait doctor
ait info
```

---

## Learn More

- **Full Guide:** `docs/guide/statusline.md`
- **Getting Started:** `docs/guides/GETTING-STARTED-STATUSLINE.md`
- **Tutorial:** `docs/guides/STATUSLINE-PHASE1-TUTORIAL.md`
- **Hook Templates:** `docs/tutorials/statusline-hooks.md`
- **Features Overview:** `docs/guides/FEATURES-OVERVIEW-V0.7.0.md`

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| **0.7.0** | Jan 17 | Gateway Pattern, Unified Menu, Hook Templates |
| 0.6.3 | Dec 31 | Feature workflows |
| 0.5.0 | Dec 30 | Release automation |

---

**Questions?** Run `ait statusline setup` to explore interactively!
