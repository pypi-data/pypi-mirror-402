# Claude Code StatusLine

**Powerlevel10k-style status line for Claude Code CLI.**

---

## Overview

The **StatusLine** feature provides a beautiful, informative 2-line status display for Claude Code CLI sessions. It shows project context, git status, session metrics, and more—all automatically updated every 300ms.

**What it shows:**

- **Line 1:** Project icon, name, worktree indicator, Python environment, git branch, stash count, remote tracking, worktree count
- **Line 2:** Model name, time of day, session duration, background agents, lines changed, output style

**Key benefits:**

- 🎯 **At-a-glance context** - See project type, git status, session info instantly
- 🎨 **3 color themes** - Purple-charcoal (default), cool-blues, forest-greens
- ⚙️ **32 config options** - Toggle features, customize display
- 🌳 **Worktree awareness** - Shows worktree count and marker for multi-branch workflows
- 📊 **Background agents** - See when Task agents are running
- ⏱️ **Time tracking** - Session duration, time-of-day indicators

---

## Quick Start

### 1. Install StatusLine

```bash
# Install StatusLine into Claude Code settings
ait statusline install

# Verify installation
ait statusline test
```

This updates `~/.claude/settings.json` to use `ait statusline render` as the statusLine command.

### 2. Test It

```bash
# Show StatusLine with mock data
ait statusline test
```

**Expected output:**

```
╭─ ░▒▓ 🐍 aiterm (venv: py3.11)  main* ⇣2 ⇡1 ?3 📦5 ▓▒░
╰─ Sonnet 4.5 │ 🌅 10:30 │ ⏱ 5m 🟢 │ +123/-45
```

### 3. Start Claude Code

Open a new Claude Code session and you'll see the StatusLine at the top of your terminal!

---

## Display Breakdown

### Line 1: Project Context

```
╭─ ░▒▓ 🐍 aiterm (venv: py3.11)  main* ⇣2 ⇡1 ?3 📦5 ▓▒░
```

| Element | Meaning |
|---------|---------|
| `🐍` | Project type icon (Python/R/Node/Quarto/etc.) |
| `aiterm` | Project name (directory basename) |
| `(wt)` | Worktree indicator (shown when in a worktree) |
| `(venv: py3.11)` | Python environment (if detected) |
| `main*` | Git branch with dirty indicator (*) |
| `⇣2` | 2 commits behind remote |
| `⇡1` | 1 commit ahead of remote |
| `?3` | 3 untracked files |
| `📦5` | 5 stashed changes |
| `🌳4` | 4 total worktrees (including main) |

**Project icons:**

| Icon | Project Type | Detected From |
|------|--------------|---------------|
| 🐍 | Python | `pyproject.toml` |
| 📦 | R Package | `DESCRIPTION` file |
| 📦 | Node.js | `package.json` |
| 📊 | Quarto | `_quarto.yml` |
| 🛠️ | MCP Server | `mcp-server/` directory |
| 🔧 | Spacemacs | `.spacemacs` file |
| 🗂️ | Dev Tools | `.git` + `scripts/` |
| 📁 | Generic | Default fallback |

### Line 2: Session Info

```
╰─ Sonnet 4.5 │ 🌅 10:30 │ ⏱ 5m 🟢 │ 🤖2 │ +123/-45 │ [learning]
```

| Element | Meaning |
|---------|---------|
| `Sonnet 4.5` | Current model (shortened from "Claude Sonnet 4.5") |
| `🌅 10:30` | Time of day icon + current time (24h format) |
| `⏱ 5m 🟢` | Session duration + productivity indicator |
| `🤖2` | 2 background agents running (Task tool) |
| `+123/-45` | Lines added/removed in this session |
| `[learning]` | Output style (if not "default") |

**Time-of-day icons:**

| Icon | Time Range |
|------|------------|
| 🌅 | 6am - 12pm (Morning) |
| ☀️ | 12pm - 6pm (Afternoon) |
| 🌙 | 6pm - 12am (Evening) |
| 🌃 | 12am - 6am (Night) |

**Productivity indicators:**

| Icon | Status | Idle Time |
|------|--------|-----------|
| 🟢 | Active | < 5 minutes |
| 🟡 | Idle | 5-15 minutes |
| 🔴 | Long idle | > 15 minutes |

---

## Ghostty Native Progress Bars (v0.7.2)

**Ghostty 1.2.x users get native graphical progress bars!**

When running in Ghostty terminal, StatusLine automatically emits OSC 9;4 escape sequences to display native progress bars for:

### Lines Changed Progress

Visualizes code changes as a progress bar:

- **Green bar (success)**: More lines added than removed
- **Red bar (error)**: More lines removed than added
- **Percentage**: Ratio of lines added to total changes

**Example:**

- `+100/-20` → Green bar at 83% (100/120)
- `+20/-100` → Red bar at 17% (20/120)

### Usage Tracking Progress

Displays API usage as a progress bar:

- **Normal (blue)**: Usage below warning threshold
- **Warning (red)**: Usage at or above threshold (default: 80%)

**Note:** Usage tracking is currently disabled as Claude Code doesn't expose this data programmatically.

### How It Works

1. **Automatic Detection**: Enabled when `TERM_PROGRAM=ghostty`
2. **No Configuration**: Works out of the box
3. **Native Integration**: Uses Ghostty's built-in progress bar feature
4. **Visual Feedback**: Instant visual indication of session activity

**To verify Ghostty is detected:**

```bash
echo $TERM_PROGRAM
# Should output: ghostty
```

---

## Configuration

### Quick Setup (Recommended for New Users)

**Use `ait statusline setup` to configure everything in one place!**

```bash
ait statusline setup
```

This shows a friendly menu:

```
┌────────────────────────────────┐
│  StatusLine Configuration      │
└────────────────────────────────┘

  1. Customize display options
     git, time, session, lines changed, etc.

  2. Change color theme
     select from available themes

  3. Adjust spacing
     minimal, standard, spacious

  4. Apply a preset
     pre-configured profiles

  5. View all settings
     see current configuration

  6. Edit raw config
     advanced JSON editing

What would you like to do? [1]:
```

**New in v0.7.0:** All configuration in one gateway command!

---

### Unified Menu (Explore All Options)

**Use `ait statusline customize` to see everything at once:**

```bash
ait statusline customize
```

This opens a unified menu with all display, theme, and spacing options in one place—no command jumping needed!

---

### Advanced Configuration

For power users who prefer direct CLI control, the advanced commands still work:

#### View Current Config

```bash
# Interactive menu (category filter)
ait statusline config

# List all settings
ait statusline config list

# Filter by category
ait statusline config list --category display
```

#### Get/Set Values

```bash
# Get a value
ait statusline config get display.show_git

# Set a value
ait statusline config set display.show_git false

# Reset to defaults
ait statusline config reset
ait statusline config reset display.show_git  # Reset single key
```

### All 32 Configuration Options

**Display Settings (12 options):**

| Setting | Default | Description |
|---------|---------|-------------|
| `display.directory_mode` | `smart` | Directory display: smart/basename/full |
| `display.show_git` | `true` | Show git information |
| `display.show_thinking_indicator` | `true` | Show 🧠 when thinking mode enabled |
| `display.show_output_style` | `auto` | Show output style: auto/always/never |
| `display.show_session_duration` | `true` | Show ⏱ session duration |
| `display.show_current_time` | `true` | Show current time |
| `display.show_lines_changed` | `true` | Show +N/-M lines changed |
| `display.show_r_version` | `true` | Show R package version |
| `display.show_background_agents` | `true` | Show 🤖N background agents |
| `display.show_mcp_status` | `false` | Show MCP server count (future) |
| `display.show_session_usage` | `false` | Session usage (not available) |
| `display.show_weekly_usage` | `false` | Weekly usage (not available) |
| `display.max_directory_length` | `50` | Max directory name length |
| `display.separator_spacing` | `standard` | Spacing around separators: minimal/standard/relaxed |

**Git Settings (6 options):**

| Setting | Default | Description |
|---------|---------|-------------|
| `git.show_ahead_behind` | `true` | Show ⇣N ⇡N indicators |
| `git.show_untracked_count` | `true` | Show ?N untracked files |
| `git.show_stash_count` | `true` | Show 📦N stashed changes |
| `git.show_remote_status` | `true` | Show remote tracking info |
| `git.show_worktrees` | `true` | Show 🌳N worktree count and (wt) marker |
| `git.truncate_branch_length` | `32` | Max branch name length |

**Project Settings (4 options):**

| Setting | Default | Description |
|---------|---------|-------------|
| `project.detect_python_env` | `true` | Show Python venv/conda/pyenv |
| `project.detect_node_version` | `false` | Show Node.js version |
| `project.detect_r_package_health` | `false` | R package status (future) |
| `project.show_dependency_warnings` | `false` | Outdated deps (future) |

**Time Settings (3 options):**

| Setting | Default | Description |
|---------|---------|-------------|
| `time.session_duration_format` | `compact` | Duration format: compact/verbose |
| `time.show_productivity_indicator` | `true` | Show 🟢/🟡/🔴 activity level |
| `time.time_format` | `24h` | Time format: 24h/12h |

**Theme Settings (2 options):**

| Setting | Default | Description |
|---------|---------|-------------|
| `theme.name` | `purple-charcoal` | Active theme name |
| `theme.custom_colors` | `{}` | Override specific colors |

**Usage Settings (3 options) - Currently Disabled:**

| Setting | Default | Description |
|---------|---------|-------------|
| `usage.show_reset_timer` | `true` | Show time until reset |
| `usage.warning_threshold` | `80` | Color warning at N% |
| `usage.compact_format` | `true` | Use compact format |

**Other Settings (2 options):**

| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | `true` | Enable/disable StatusLine |
| `update_interval_ms` | `300` | Update interval (Claude Code controls) |

---

## Theme Management

### List Available Themes

```bash
ait statusline theme list
```

**Available themes:**

| Theme | Colors | Best For |
|-------|--------|----------|
| `purple-charcoal` | Purple + dark gray | Default, balanced contrast |
| `cool-blues` | Blue tones | Calm, professional |
| `forest-greens` | Green tones | Natural, easy on eyes |

### Switch Themes

```bash
# Switch to cool-blues
ait statusline theme set cool-blues

# View current theme
ait statusline theme show
```

### Custom Theme Colors

Create custom color overrides in config:

```bash
# Edit config
ait statusline config edit

# Add custom_colors section
{
  "theme": {
    "name": "purple-charcoal",
    "custom_colors": {
      "project_fg": "38;5;141",
      "git_fg": "38;5;75"
    }
  }
}
```

**Available color keys:**

- `project_fg` - Project name color
- `project_bg` - Project background
- `git_fg` - Git information color
- `git_bg` - Git background
- `model_fg` - Model name color
- `separator_fg` - Separator (│) color
- `time_fg` - Time display color
- `lines_added_fg` - Lines added color
- `lines_removed_fg` - Lines removed color
- `style_fg` - Output style color

**Color format:** ANSI codes like `38;5;N` (foreground) or `48;5;N` (background) where N is 0-255.

---

## Hook Templates (Claude Code v2.1+)

StatusLine includes pre-built hooks that can automatically adapt to your environment.

### Available Hooks

```bash
# List all available hook templates
ait statusline hooks list
```

**Pre-built hooks:**

| Hook | Type | Purpose |
|------|------|---------|
| `on-theme-change` | PostToolUse | Auto-update colors when terminal theme changes |
| `on-remote-session` | PreToolUse | Enable remote indicator when using /teleport |
| `on-error` | PostToolUse | Alert when statusLine rendering fails |

### Installing Hooks

```bash
# Install a hook template
ait statusline hooks add on-theme-change

# View installed hooks
ait statusline hooks list --installed
```

### Managing Hooks

```bash
# Enable a hook
ait statusline hooks enable on-error

# Disable a hook
ait statusline hooks disable on-error

# Remove a hook
ait statusline hooks remove on-theme-change
```

**Benefits:**
- Automatic environment detection
- No manual configuration needed
- Auto-validated for compatibility
- Works with Claude Code v2.1+ features

---

## Commands Reference

### 🎯 Recommended (v0.7.0+)

```bash
# Gateway to all customization options
ait statusline setup

# Unified menu combining display/theme/spacing
ait statusline customize

# Manage hook templates
ait statusline hooks list              # Show available hooks
ait statusline hooks add <name>        # Install a hook
ait statusline hooks list --installed  # Show installed hooks
ait statusline hooks enable <name>     # Enable a hook
ait statusline hooks disable <name>    # Disable a hook
ait statusline hooks remove <name>     # Uninstall a hook
```

### Installation & Setup

```bash
# Install StatusLine into Claude Code
ait statusline install

# Test with mock data
ait statusline test

# Validate configuration
ait statusline doctor
```

### Advanced Configuration

For power users who prefer direct CLI control:

```bash
# Interactive menu
ait statusline config

# List settings
ait statusline config list
ait statusline config list --category display

# Get/set values
ait statusline config get <key>
ait statusline config set <key> <value>

# Reset to defaults
ait statusline config reset [key]

# Edit in $EDITOR
ait statusline config edit

# Validate config
ait statusline config validate

# Apply preset
ait statusline config preset <name>

# Adjust spacing
ait statusline config spacing <preset>
```

### Theme Management

```bash
# List themes
ait statusline theme list

# Switch theme
ait statusline theme set <theme>

# View current theme
ait statusline theme show
```

### Internal Commands

```bash
# Render StatusLine (called by Claude Code)
ait statusline render

# Uninstall from Claude Code
ait statusline uninstall
```

---

## Examples

### Spacing Adjustments

**Goal:** Customize visual spacing around separators

```bash
# Minimal spacing (1 space) - Most compact
ait statusline config set display.separator_spacing minimal

# Standard spacing (2 spaces) - Default, balanced
ait statusline config set display.separator_spacing standard

# Relaxed spacing (3 spaces) - Most spacious
ait statusline config set display.separator_spacing relaxed
```

**Visual comparison:**

```
Minimal:  Sonnet 4.5 │ 11:46 │ ⏱ 5m │ +123/-45
Standard: Sonnet 4.5  │  11:46  │  ⏱ 5m  │  +123/-45  (default)
Relaxed:  Sonnet 4.5   │   11:46   │   ⏱ 5m   │   +123/-45
```

**Recommended:** Use `standard` (default) for best balance of readability and compactness.

---

### Worktree Display

**Goal:** Show git worktree information for multi-branch workflows

```bash
# Enable worktree display (enabled by default)
ait statusline config set git.show_worktrees true

# Disable if you don't use worktrees
ait statusline config set git.show_worktrees false
```

**In main working directory:**

```
╭─ ░▒▓ 🐍 aiterm  main 🌳4 ▓▒░
                        ^^^^
                        4 total worktrees
```

**In a worktree directory:**

```
╭─ ░▒▓ 🐍 aiterm-test (wt)  feature-auth 🌳4 ▓▒░
                     ^^^^                 ^^^^
                     Worktree marker      Total count
```

**Features:**

- `🌳N` - Shows total worktree count when > 1
- `(wt)` - Marker when in a non-main worktree
- Helps identify context in multi-branch workflows

---

### Minimal Display

**Goal:** Show only essential info (model, time, git)

```bash
# Disable extras
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

### Maximum Detail

**Goal:** Show everything available

```bash
# Enable all features
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

### Git-Focused Display

**Goal:** Emphasize git information

```bash
# Show all git features
ait statusline config set git.show_stash_count true
ait statusline config set git.show_remote_status true
ait statusline config set git.show_worktrees true
ait statusline config set git.show_ahead_behind true
ait statusline config set git.show_untracked_count true

# Disable non-git extras
ait statusline config set display.show_lines_changed false
ait statusline config set project.detect_python_env false
```

**Result:**

```
╭─ ░▒▓ 🐍 aiterm  main* ⇣2 ⇡1 ?3 📦5 🔗origin/main 🌳4 ▓▒░
╰─ Sonnet 4.5 │ 10:30 │ ⏱ 5m
```

---

## Troubleshooting

### StatusLine Not Showing

**Check installation:**

```bash
# Verify settings.json
cat ~/.claude/settings.json | grep -A 3 statusLine

# Expected:
# "statusLine": {
#   "type": "command",
#   "command": "ait statusline render"
# }
```

**Fix:**

```bash
# Reinstall
ait statusline install

# Or manually edit ~/.claude/settings.json
```

### Wrong Colors/Theme

**Check current theme:**

```bash
ait statusline theme show
```

**Fix:**

```bash
# Switch to desired theme
ait statusline theme set purple-charcoal
```

### Missing Git Information

**Check git settings:**

```bash
ait statusline config get git.show_ahead_behind
ait statusline config get git.show_stash_count
```

**Fix:**

```bash
# Enable git features
ait statusline config set git.show_ahead_behind true
ait statusline config set git.show_stash_count true
```

### Python Environment Not Showing

**Check project detection:**

```bash
ait statusline config get project.detect_python_env
```

**Fix:**

```bash
# Enable Python environment detection
ait statusline config set project.detect_python_env true
```

### Background Agents Not Showing

**Check if agents are actually running:**

```bash
# List running Task agents
ait sessions live
```

**Check config:**

```bash
ait statusline config get display.show_background_agents
```

**Fix:**

```bash
# Enable background agents display
ait statusline config set display.show_background_agents true
```

### Config Changes Not Applied

**Restart Claude Code session** - Config is loaded at startup.

**Or manually reload:**

```bash
# Test rendering with current config
ait statusline test
```

---

## Technical Details

### Architecture

**Modular Design:**

- **Renderer** - Main `StatusLineRenderer` class
- **Segments** - 8 independent segment classes:
  - `ProjectSegment` - Project icon, name, Python env
  - `GitSegment` - Git branch, stash, remote
  - `ModelSegment` - Model display name
  - `TimeSegment` - Time, session duration, productivity
  - `ThinkingSegment` - Thinking mode indicator
  - `LinesSegment` - Lines added/removed
  - `UsageSegment` - Usage tracking (disabled)
  - `AgentSegment` - Background agents count

**Data Flow:**

1. Claude Code calls `ait statusline render` every 300ms
2. Renderer reads JSON from stdin (project/git/session data)
3. Each segment renders its portion independently
4. Segments combined into 2-line output
5. ANSI escape sequences for colors/formatting

### Config Location

- **User config:** `~/.config/aiterm/statusline.json` (XDG-compliant)
- **Theme files:** `src/aiterm/statusline/themes/*.json`
- **Session tracking:** `~/.claude/sessions/active/`

### Performance

- **Update interval:** 300ms (Claude Code default)
- **Render time:** < 50ms typically
- **Caching:** Session duration, agent counts cached

### Testing

**919 total tests** including 70 StatusLine-specific tests:

```bash
# Run StatusLine tests
pytest tests/test_statusline_*.py

# Run all tests
pytest
```

---

## Usage Tracking (Currently Disabled)

**Why disabled:** Claude Code does not expose usage limits (session/weekly) programmatically.

**What we tried:**

1. ✅ Extract OAuth token from macOS Keychain
2. ❌ API call to `/api/oauth/usage` - OAuth not supported
3. ❌ Parse `/usage` command output - uses internal endpoints
4. ❌ Read from local files - no usage data stored

**Tracking issue:** [#5621](https://github.com/anthropics/claude-code/issues/5621) - StatusLine should expose API usage/quota

**Future:** If Claude Code exposes usage data in JSON input, usage tracking will be automatically enabled.

**Current display:** Context window size available in JSON:

```json
{
  "context_window": {
    "context_window_size": 200000,
    "current_usage": {
      "input_tokens": 1234,
      "output_tokens": 567
    }
  }
}
```

This data is available but not currently displayed. Could be added as optional feature in future.

---

## FAQ

### Can I use StatusLine with other terminals?

**Currently:** StatusLine is Claude Code-specific. It reads JSON from Claude Code's stdin.

**Future:** Could be adapted for standalone use with manual JSON input.

### Why doesn't usage tracking work?

See [Usage Tracking](#usage-tracking-currently-disabled) section above. Claude Code doesn't expose this data programmatically.

### Can I create my own theme?

Yes! Edit config with custom color overrides:

```bash
ait statusline config edit
```

Add `theme.custom_colors` section with ANSI color codes.

### How do I disable StatusLine temporarily?

```bash
# Disable in config
ait statusline config set enabled false

# Or remove from Claude Code settings
ait statusline uninstall
```

### Can I show custom information?

Not currently, but planned for future versions. The modular segment design makes this feasible.

### Why 2 lines instead of 1?

Powerlevel10k-style 2-line layout provides:

- Clear visual hierarchy (context vs session info)
- More space for detailed information
- Better readability

---

## Related Documentation

- [Claude Code Integration](claude-integration.md) - Auto-approvals, settings management
- [Context Detection](context-detection.md) - How project types are detected
- [Workflows](workflows.md) - Session-aware workflow automation
- [Terminals](terminals.md) - iTerm2/Ghostty integration

---

## Changelog

### v0.7.1 (Dec 31, 2025)

- 🎨 **Configurable Spacing** - Adjust separator spacing (minimal/standard/relaxed)
- ✨ **Better Readability** - Default spacing improved from 1 to 2 spaces
- ⚙️ **New Config Option** - `display.separator_spacing`

### v0.7.0 (Dec 31, 2025)

- ✨ **Initial Release** - Full StatusLine implementation
- 🎨 **3 Themes** - purple-charcoal, cool-blues, forest-greens
- ⚙️ **31 Config Options** - Fully customizable display
- 📊 **Background Agents** - Show running Task agents
- ⏱️ **Enhanced Time Tracking** - Productivity indicators, time-of-day icons
- 🐍 **Python Environment** - venv/conda/pyenv detection
- 🌿 **Enhanced Git** - Stash count, remote tracking
- 🧪 **70 Tests** - Comprehensive test coverage

---

## Contributing

Found a bug or have a feature request?

- **Issues:** [https://github.com/Data-Wise/aiterm/issues](https://github.com/Data-Wise/aiterm/issues)
- **Discussions:** [https://github.com/Data-Wise/aiterm/discussions](https://github.com/Data-Wise/aiterm/discussions)

**Ideas for contributions:**

- [ ] Additional themes
- [ ] Custom segment system
- [ ] Node.js version detection
- [ ] R package health indicators
- [ ] Dependency warning detection
- [ ] MCP server status integration
