# aiterm User Guide

**Version:** 0.3.11
**Last Updated:** 2025-12-29
**Reading Time:** 20 minutes
**Difficulty:** Beginner to Intermediate

---

## Welcome to aiterm!

This guide will help you get started with aiterm, the terminal optimizer for AI-assisted development with Claude Code, OpenCode, and Gemini CLI.

**What's New in v0.3.x:**
- XDG-compliant configuration (`~/.config/aiterm/`)
- flow-cli integration (`tm` dispatcher)
- Ghostty terminal support
- Session coordination
- IDE integrations

---

## Table of Contents

1. [What is aiterm?](#what-is-aiterm)
2. [Installation](#installation)
3. [First-Time Setup](#first-time-setup)
4. [Daily Workflows](#daily-workflows)
5. [Terminal Support](#terminal-support)
6. [Configuration](#configuration)
7. [Advanced Features](#advanced-features)
8. [Tips & Tricks](#tips-tricks)
9. [FAQ](#faq)

---

## What is aiterm?

### The Problem

When working with AI coding assistants (Claude Code, Gemini CLI), switching between different project types is manual and error-prone:

**Before aiterm:**
```bash
$ cd ~/projects/r-packages/RMediation
# Manual: Change iTerm2 profile to "R-Dev"
# Manual: Set auto-approvals for R package tools
# Manual: Update tab title
# Manual: Remember which profile to use
```

**Repeat this every time you switch projects!** 😫

### The Solution

**aiterm automatically optimizes your terminal for each project:**

```bash
$ cd ~/projects/r-packages/RMediation
# ✅ Auto-detects: R package
# ✅ Auto-switches: R-Dev profile (blue theme)
# ✅ Auto-sets: Tab title "RMediation v1.0.0"
# ✅ Auto-applies: R-specific auto-approvals
```

**Just `cd` and everything is configured!** 🚀

---

### Key Features

**Automatic Context Detection**
- Detects R packages, Python projects, Node.js apps, production paths, AI sessions
- 8 built-in context types, extensible for custom types

**Multi-Terminal Support**
- **iTerm2**: Full support (profiles, badges, status bar)
- **Ghostty**: Full support (themes, fonts, settings)
- **WezTerm, Kitty, Alacritty**: Basic support

**Claude Code Integration**
- Auto-approval presets for different workflows
- 8 built-in presets (minimal, development, production, r-package, etc.)
- Settings management with automatic backups
- Session coordination and conflict detection

**flow-cli Integration (v0.3.10+)**
- `tm` dispatcher for instant terminal control
- Shell-native commands (no Python overhead)
- Integrates with flow-cli workflow system

**XDG Configuration (v0.3.11+)**
- Config at `~/.config/aiterm/config.toml`
- Override with `AITERM_CONFIG_HOME`
- Clean separation of config, profiles, themes

**ADHD-Friendly Design**
- Zero manual configuration needed
- Visual feedback for all operations
- Fast operations (< 200ms for everything)
- Clear error messages with solutions

---

## Installation

### Prerequisites

**Required:**
- Python 3.10 or higher
- macOS or Linux

**Recommended:**
- iTerm2 or Ghostty (for full terminal features)
- Claude Code CLI (for Claude integration)
- flow-cli (for `tm` dispatcher)

### Method 1: Quick Install (Recommended)

```bash
# Auto-detects best method (uv/pipx/brew/pip)
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash
```

### Method 2: Homebrew (macOS)

```bash
brew install data-wise/tap/aiterm
```

### Method 3: UV/pipx

```bash
# With uv (fastest)
uv tool install aiterm-dev

# With pipx
pipx install aiterm-dev
```

### Method 4: pip

```bash
pip install aiterm-dev
```

### Method 5: From Source (Development)

```bash
git clone https://github.com/Data-Wise/aiterm.git
cd aiterm
uv pip install -e ".[dev]"
```

### Verify Installation

```bash
$ ait --version
aiterm 0.3.11
Python: 3.12.0
Platform: macOS-15.2-arm64
Path: /Users/you/.local/bin/aiterm

$ ait doctor
aiterm doctor - Health check

Terminal: iTerm.app
Shell: /bin/zsh
Python: 3.12.0
aiterm: 0.3.11

Basic checks passed!
```

**If any checks fail:** See [Troubleshooting Guide](../troubleshooting/AITERM-TROUBLESHOOTING.md)

---

## First-Time Setup

### Step 1: Run Doctor Check

```bash
ait doctor
```

This verifies:
- ✅ Python version (≥ 3.10)
- ✅ Terminal type (iTerm2, Ghostty, or basic)
- ✅ Claude Code installation
- ✅ Configuration files

**Example - All Good:**
```
✅ Python: 3.12.0
✅ Terminal: iTerm2 (Build 3.5.0)
✅ Claude Code: 1.0.0
✅ Settings: ~/.config/aiterm/config.toml

System Status: All checks passed!
```

**Example - Basic Terminal:**
```
✅ Python: 3.12.0
⚠️ Terminal: Terminal.app (basic features only)
   → For full features, use iTerm2 or Ghostty
✅ Claude Code: 1.0.0
✅ Settings: ~/.config/aiterm/config.toml

System Status: All checks passed (some features limited)
```

### Step 1b: Initialize Configuration (Optional)

```bash
# Create default config file
ait config init
# → Creates ~/.config/aiterm/config.toml

# View config locations
ait config path --all
# → Shows all config paths with status

# View current settings
ait config show
```

---

### Step 2: Test Context Detection

Navigate to a project and test detection:

```bash
$ cd ~/projects/r-packages/RMediation
$ aiterm detect

╔════════════════════════════════════════════════════╗
║  Context Detection                                 ║
╚════════════════════════════════════════════════════╝

📁 Path: /Users/dt/projects/r-packages/RMediation
🎯 Type: R Package
📦 Package: RMediation
📋 Profile: R-Dev
🎨 Title: RMediation v1.0.0

Detected: R package development environment
```

**What it detects:**
- DESCRIPTION file → R package
- pyproject.toml → Python project
- package.json → Node.js project
- */production/* path → Production environment
- */claude-sessions/* → AI coding session
- And more! (See [Context Types](#context-types))

---

### Step 3: Explore Available Profiles

```bash
$ aiterm profile list

╔════════════════════════════════════════════════════╗
║  Available Profiles                                ║
╚════════════════════════════════════════════════════╝

📋 R-Dev
   → For R package development
   🎨 Blue theme, white text
   🔧 Optimized for ESS/Claude Code

📋 Python-Dev
   → For Python projects
   🎨 Green theme, white text
   🔧 Optimized for pytest/Claude Code

📋 Production
   → For production deployments (SAFE MODE)
   🎨 Red theme, black text
   ⚠️  Read-only, extra confirmations

📋 AI-Session
   → For Claude Code/Gemini sessions
   🎨 Purple theme, white text
   🔧 Optimized for AI coding workflows

📋 Default
   → Standard profile
   🎨 Default iTerm2 theme
```

---

### Step 4: (Optional) Set Auto-Approvals

If you use Claude Code, configure auto-approvals:

```bash
$ aiterm claude approvals list

╔════════════════════════════════════════════════════╗
║  Auto-Approval Presets                             ║
╚════════════════════════════════════════════════════╝

⚡ minimal (15 tools)
   → Essential operations only

🚀 development (45 tools)
   → Full development workflow

🔒 production (20 tools)
   → Production-safe operations

🎯 r-package (35 tools)
   → R package development

...
```

**Apply a preset:**
```bash
$ aiterm claude approvals set r-package

✅ Applied preset: r-package
📋 Approved tools: 35
📝 Updated: ~/.claude/settings.json
```

**Done!** aiterm is now configured.

---

## Daily Workflows

### Workflow 1: R Package Development

**Scenario:** You're developing an R package

**Before aiterm:**
```bash
$ cd ~/projects/r-packages/RMediation
# 1. Manually change iTerm2 profile to "R-Dev"
# 2. Manually update tab title
# 3. Manually set Claude Code auto-approvals
# 4. Remember R-specific commands
```

**With aiterm:**
```bash
$ cd ~/projects/r-packages/RMediation
# ✅ Auto-switched to R-Dev profile (blue theme)
# ✅ Title: "RMediation v1.0.0"
# ✅ Status bar: "R PKG | RMediation"
# ✅ Claude Code auto-approvals: R package tools
```

**Visual change:**
- Background: Dark blue
- Foreground: White
- Accent: Light blue
- Tab title: "RMediation v1.0.0"

**What you can do:**
```bash
# All R development commands work
R CMD check .
R CMD build .
devtools::test()
# Claude Code knows R package context
```

---

### Workflow 2: Python Development

**Scenario:** You're working on a Python project

**Before:**
```bash
$ cd ~/projects/python/my-api
# Manually configure everything...
```

**With aiterm:**
```bash
$ cd ~/projects/python/my-api
# ✅ Auto-switched to Python-Dev profile (green theme)
# ✅ Title: "my-api"
# ✅ Status bar: "PYTHON | my-api"
```

**Visual change:**
- Background: Dark green
- Foreground: White
- Tab title: "my-api"

**What you can do:**
```bash
pytest
python -m mypy .
# Claude Code knows Python context
```

---

### Workflow 3: Production Deployment (SAFE MODE)

**Scenario:** You need to deploy to production

**Critical:** Production mode has EXTRA SAFETY

**Before:**
```bash
$ cd ~/production/api-server
# ⚠️ No visual indicator you're in production!
# ⚠️ Easy to run destructive commands by accident
```

**With aiterm:**
```bash
$ cd ~/production/api-server
# ✅ Auto-switched to Production profile (RED theme)
# ✅ Title: "⚠️ PROD: api-server"
# ✅ Status bar: "⚠️ PRODUCTION"
# ✅ Extra confirmations enabled
```

**Visual change:**
- **Background: RED** 🔴 (impossible to miss!)
- Foreground: Black
- Tab title: "⚠️ PROD: api-server"
- Every destructive command requires confirmation

**Safety features:**
```bash
$ rm important-file.txt
⚠️  PRODUCTION MODE - Are you sure? [y/N]

$ git push --force
⚠️  PRODUCTION MODE - Force push detected. Confirm: [y/N]
```

**Use this for:**
- Production servers
- Deployments
- Database migrations
- Any high-risk environment

---

### Workflow 4: AI Coding Session

**Scenario:** You're doing intensive AI-assisted coding

**Before:**
```bash
$ cd ~/claude-sessions/refactor-2025
# Generic terminal setup
# Have to manually configure Claude Code
```

**With aiterm:**
```bash
$ cd ~/claude-sessions/refactor-2025
# ✅ Auto-switched to AI-Session profile (purple theme)
# ✅ Title: "Claude Session: refactor-2025"
# ✅ Maximum auto-approvals (50 tools)
# ✅ Optimized for rapid iteration
```

**Visual change:**
- Background: Dark purple
- Foreground: White
- Tab title: "Claude Session: refactor-2025"

**What's different:**
- Broadest auto-approvals (50 tools)
- Fast iteration focus
- Optimized for Claude Code workflows

---

### Workflow 5: Switching Between Projects

**Scenario:** You work on multiple projects daily

**Example session:**
```bash
# Morning: R package work
$ cd ~/projects/r-packages/RMediation
# → R-Dev profile (blue)

# Afternoon: Python API
$ cd ~/projects/python/api-server
# → Python-Dev profile (green)

# Evening: Production hotfix
$ cd ~/production/api-server
# → Production profile (RED, safe mode)

# Night: AI coding session
$ cd ~/claude-sessions/new-feature
# → AI-Session profile (purple)
```

**Each `cd` automatically:**
- ✅ Detects context
- ✅ Switches profile
- ✅ Updates title
- ✅ Sets appropriate auto-approvals
- ✅ Adjusts safety settings

**No manual steps needed!**

---

## Terminal Support

aiterm supports multiple terminals with varying feature levels.

### Supported Terminals

| Terminal | Profile Switching | Themes | Tab Titles | Status Bar |
|----------|------------------|--------|------------|------------|
| **iTerm2** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Ghostty** | ✅ Via themes | ✅ 14 built-in | ✅ Full | ❌ N/A |
| **WezTerm** | 🔄 Planned | 🔄 Planned | ✅ Basic | 🔄 Planned |
| **Kitty** | 🔄 Planned | 🔄 Planned | ✅ Basic | 🔄 Planned |
| **Alacritty** | ❌ N/A | 🔄 Planned | ❌ N/A | ❌ N/A |
| **Terminal.app** | ❌ Limited | ❌ N/A | ✅ Basic | ❌ N/A |

### Detecting Your Terminal

```bash
$ ait terminals detect
Detected: iTerm.app
Version: 3.5.0
Features: profiles, themes, badges, status-bar, escape-sequences

$ ait terminals features
┌────────────────────────────────────────┐
│ Terminal Features: iTerm.app           │
├────────────────────────────────────────┤
│ ✅ Profile switching                   │
│ ✅ Theme support                       │
│ ✅ Tab title                           │
│ ✅ Badge support                       │
│ ✅ Status bar variables                │
│ ✅ Escape sequences                    │
└────────────────────────────────────────┘
```

### iTerm2 Setup

iTerm2 is the recommended terminal with full feature support.

**Create profiles for each context type:**

1. Open iTerm2 → Preferences → Profiles
2. Create profiles matching aiterm's expected names:
   - `R-Dev` - Blue theme for R development
   - `Python-Dev` - Green theme for Python
   - `Production` - Red theme (safety warning!)
   - `AI-Session` - Purple theme for AI coding
   - `Default` - Your standard profile

**Tab title configuration:**
- Preferences → Profiles → [Profile] → General
- Title: "Name (Job)" or custom format
- Badge: Enable for context info

### Ghostty Setup (v0.3.9+)

Ghostty is a fast, GPU-accelerated terminal with excellent aiterm support.

**Check Ghostty status:**
```bash
$ ait ghostty status
Ghostty Configuration
─────────────────────
Config file: ~/.config/ghostty/config
Theme: catppuccin-mocha
Font: JetBrains Mono @ 14pt
```

**Theme management:**
```bash
# List available themes (14 built-in)
$ ait ghostty theme
Available themes:
  catppuccin-mocha    dracula         nord
  tokyo-night         gruvbox-dark    gruvbox-light
  solarized-dark      solarized-light one-dark
  ...

# Apply a theme
$ ait ghostty theme dracula
✅ Theme set: dracula
```

**Font configuration:**
```bash
# Check current font
$ ait ghostty font
Font: JetBrains Mono @ 14pt

# Change font and size
$ ait ghostty font "Fira Code" 16
✅ Font set: Fira Code @ 16pt
```

**Custom settings:**
```bash
# Set any Ghostty config value
$ ait ghostty set window-padding-x 12
$ ait ghostty set background-opacity 0.95
$ ait ghostty set cursor-style underline
```

### flow-cli Integration (v0.3.10+)

The `tm` dispatcher provides instant terminal control from shell:

```bash
# Set tab title (instant, no Python!)
$ tm title "Working on API"

# Switch iTerm2 profile
$ tm profile "Production"

# Detect and apply context
$ tm switch

# Show detected terminal
$ tm which
→ iterm2

# Ghostty commands via tm
$ tm ghost status
$ tm ghost theme dracula
$ tm ghost font "Fira Code" 16
```

**Benefits of tm dispatcher:**
- Shell-native (no Python startup overhead)
- Instant response (~5ms vs ~100ms)
- Works in shell scripts and aliases
- Integrates with flow-cli workflow system

---

## Configuration

aiterm uses XDG-compliant configuration paths (v0.3.11+).

### Configuration Paths

| Path | Purpose |
|------|---------|
| `~/.config/aiterm/config.toml` | Main configuration |
| `~/.config/aiterm/profiles/` | Custom profile definitions |
| `~/.config/aiterm/themes/` | Custom color themes |

**Override with environment variable:**
```bash
export AITERM_CONFIG_HOME="$HOME/.aiterm"
```

### Managing Configuration

```bash
# Show config directory
$ ait config path
~/.config/aiterm

# Show all paths with status
$ ait config path --all
Configuration Paths
───────────────────
Config home: ~/.config/aiterm (exists)
Config file: ~/.config/aiterm/config.toml (exists)
Profiles dir: ~/.config/aiterm/profiles (missing)
Themes dir: ~/.config/aiterm/themes (missing)

# Create default config
$ ait config init
✅ Created: ~/.config/aiterm/config.toml

# View current config
$ ait config show

# Edit config in $EDITOR
$ ait config edit
```

### Configuration File

```toml
# ~/.config/aiterm/config.toml

[general]
default_terminal = "auto"  # auto, iterm2, ghostty
quiet_mode = false

[profiles]
default = "default"
auto_switch = true

[flow_cli]
enabled = true
dispatcher = "tm"

[claude]
manage_settings = true
backup_on_change = true
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AITERM_CONFIG_HOME` | Override config directory | `~/.config/aiterm` |
| `AITERM_AUTO_SWITCH` | Enable/disable auto-switch | `1` |
| `AITERM_QUIET` | Suppress output | `0` |
| `AITERM_TERMINAL` | Force terminal type | auto-detect |

---

## Advanced Features

### Context Types

aiterm detects 8 context types (priority order):

| Priority | Type | Detection | Profile | Use Case |
|----------|------|-----------|---------|----------|
| 1 | Production | `*/production/*` or `*/prod/*` | Production | Deployments, servers |
| 2 | AI Session | `*/claude-sessions/*` or `*/gemini-sessions/*` | AI-Session | AI coding |
| 3 | R Package | `DESCRIPTION` + `R/` | R-Dev | R development |
| 4 | Python | `pyproject.toml` or `setup.py` | Python-Dev | Python development |
| 5 | Node.js | `package.json` | Node-Dev | JavaScript/TypeScript |
| 6 | Quarto | `_quarto.yml` | R-Dev | Quarto documents |
| 7 | MCP Server | `mcp-server/` directory | AI-Session | MCP development |
| 8 | Dev Tools | `.git/` + `scripts/` | Dev-Tools | Tool development |
| 9 | Default | (no match) | Default | Generic work |

**Priority matters:** If a directory matches multiple types, the highest priority wins.

**Example:**
```bash
$ cd ~/production/r-api
# Contains both */production/* AND DESCRIPTION
# → Production wins (priority 1 > priority 3)
# → Production profile applied (safety first!)
```

---

### Manual Profile Switching

**When automatic detection isn't enough:**

```bash
# Switch to specific profile
$ aiterm profile switch R-Dev
✅ Switched to profile: R-Dev

# Switch with custom title
$ aiterm profile switch Python-Dev --title "API Server"
✅ Switched to profile: Python-Dev
🎨 Title: API Server
```

**Use cases:**
- Override automatic detection
- Work in non-standard directory structure
- Temporary profile change
- Testing different profiles

---

### Disabling Auto-Switching

**If you prefer manual control:**

```bash
# Disable automatic switching
export AITERM_AUTO_SWITCH=0

# Add to ~/.zshrc or ~/.bashrc for permanent
echo 'export AITERM_AUTO_SWITCH=0' >> ~/.zshrc
```

**Then manually switch:**
```bash
aiterm profile switch PROFILE_NAME
```

---

### Claude Code Auto-Approval Presets

**8 Built-in Presets:**

| Preset | Tools | Use Case |
|--------|-------|----------|
| `minimal` | 15 | Essential read operations only |
| `development` | 45 | Full development workflow |
| `production` | 20 | Production-safe (read-only) |
| `r-package` | 35 | R package development |
| `python-dev` | 40 | Python development |
| `teaching` | 30 | Teaching/course development |
| `research` | 35 | Research/manuscript writing |
| `ai-session` | 50 | AI coding sessions (broadest) |

**Applying presets:**

```bash
# Apply preset
$ aiterm claude approvals set r-package
✅ Applied preset: r-package (35 tools)

# Merge with existing approvals
$ aiterm claude approvals set development --merge
✅ Merged preset: development
📋 Total approved: 58 tools
```

**What gets approved:**

**r-package preset example:**
```
✅ Bash(git *)          # All git commands
✅ Bash(R CMD *)        # R CMD build/check/install
✅ Bash(Rscript:*)      # Run R scripts
✅ Bash(pytest:*)       # Run tests
✅ Read(**)             # Read any file
✅ Write(**)            # Write any file
✅ Edit(**)             # Edit any file
... (28 more)
```

---

### Checking Current Settings

```bash
$ aiterm claude settings show

╔════════════════════════════════════════════════════╗
║  Claude Code Settings                              ║
╚════════════════════════════════════════════════════╝

📁 Settings: ~/.claude/settings.json
📊 File size: 2.4 KB
🕐 Modified: 2025-12-21 10:30:45

Auto-Approvals:
  ✅ 35 tools approved
  📋 Active preset: r-package

Status Line:
  ✅ Configured: /bin/bash ~/.claude/statusline-p10k.sh
  ⏱️  Update interval: 300ms

MCP Servers:
  ✅ statistical-research (14 tools)
  ✅ shell (5 tools)
  ✅ project-refactor (4 tools)
```

---

## Tips & Tricks

### Tip 1: Use `detect` to Preview

Before relying on automatic switching, preview what aiterm detects:

```bash
$ cd ~/my-project
$ aiterm detect

📁 Path: /Users/dt/my-project
🎯 Type: Python
📋 Profile: Python-Dev
🎨 Title: my-project
```

**Then decide:**
- Automatic switching correct? → Let it happen
- Need different profile? → Manual switch
- Context not detected? → See Troubleshooting

---

### Tip 2: Production Safety Workflow

**Always check before production work:**

```bash
$ aiterm detect
# Should show:
# 🎯 Type: Production
# ⚠️  Profile: Production (safe mode)

# If NOT showing Production:
$ aiterm profile switch Production
```

**Visual confirmation:**
- Background MUST be RED 🔴
- Title MUST have ⚠️ symbol
- Every command should feel slower (confirmations)

---

### Tip 3: Rapid Context Switching

**Work on multiple projects:**

```bash
# Use shell aliases for common projects
alias rmed='cd ~/projects/r-packages/RMediation'
alias api='cd ~/projects/python/api-server'
alias prod='cd ~/production/api-server'

# Then just:
$ rmed    # → R-Dev profile
$ api     # → Python-Dev profile
$ prod    # → Production profile (RED!)
```

**aiterm handles the rest automatically!**

---

### Tip 4: Custom Context Detection (Advanced)

**Coming in Phase 2:** Custom detector plugins

**Preview:**
```python
# ~/.aiterm/custom_detectors.py
from aiterm.context import ContextDetector, Context

class MyProjectDetector(ContextDetector):
    def detect(self, path: str) -> Context | None:
        if self._has_file(path, ".myproject"):
            return Context(
                type="my-project",
                profile="My-Profile",
                title="My Project",
                path=path
            )
        return None
```

---

### Tip 5: Backup and Recovery

**aiterm automatically backs up Claude Code settings:**

```bash
# Backups location
ls ~/.claude/settings.json.backup.*

# Restore from backup
cp ~/.claude/settings.json.backup.20251221_103045 \
   ~/.claude/settings.json
```

**Backups created when:**
- Applying auto-approval presets
- Updating settings
- Before any destructive operation

**Retention:** Last 5 backups

---

## FAQ

### Q: Does aiterm work outside iTerm2?

**A:** Yes! aiterm now supports multiple terminals (v0.3.9+):

**Full support:**
- **iTerm2** - Profiles, themes, titles, status bar, badges
- **Ghostty** - Themes (14 built-in), fonts, titles, settings

**Basic support (context detection + titles):**
- WezTerm
- Kitty
- Terminal.app

**Universal features (all terminals):**
- ✅ Context detection
- ✅ Auto-approval management
- ✅ Settings management
- ✅ Configuration commands

Check your terminal's features:
```bash
ait terminals detect
ait terminals features
```

---

### Q: Will automatic switching slow down my terminal?

**A:** No! aiterm is extremely fast:
- Context detection: < 50ms
- Profile switching: < 150ms
- Total overhead: < 200ms per `cd`

**You won't notice any delay.**

---

### Q: Can I customize profiles?

**A:** Yes! Edit `~/.config/aiterm/config.toml`:

```toml
[profiles.custom.my-project]
theme = "my-theme"
triggers = [".myproject"]
auto_approvals = ["Bash(git *)", "Read(**)"]
```

Or create a profile file in `~/.config/aiterm/profiles/`:

```toml
# ~/.config/aiterm/profiles/my-project.toml
name = "My-Project"
theme = "my-theme"
triggers = [".myproject", "myproject.json"]
auto_approvals = ["Bash(git *)", "Read(**)"]
```

**Coming in Phase 2:** Profile creation wizard (`ait profile create`)

---

### Q: What if I work on production AND development in the same path?

**A:** Production always wins (priority 1).

**Example:**
```bash
$ cd ~/production/my-r-package
# Contains: */production/* AND DESCRIPTION
# → Production profile applied (safety first!)
```

**Override if needed:**
```bash
$ aiterm profile switch R-Dev
# Manually switch to R-Dev for development work
# → But be careful! You're in production path
```

---

### Q: How do I uninstall aiterm?

**With UV:**
```bash
uv tool uninstall aiterm-dev
```

**With pipx:**
```bash
pipx uninstall aiterm-dev
```

**With pip:**
```bash
pip uninstall aiterm-dev
```

**With Homebrew:**
```bash
brew uninstall aiterm
```

**Remove config files (optional):**
```bash
rm -rf ~/.config/aiterm
```

**Note:** Claude Code settings (`~/.claude/`) are NOT removed (safe to keep)

---

### Q: Can I use aiterm with Gemini CLI?

**A:** Basic support now, full integration planned for Phase 2.

**Currently works:**
- ✅ Context detection
- ✅ Profile switching
- ✅ AI-Session detection (gemini-sessions/ paths)

**Planned:**
- Gemini-specific auto-approvals
- Gemini settings management
- Gemini MCP integration

---

### Q: What's the difference between presets?

**Quick comparison:**

| Feature | minimal | development | production | ai-session |
|---------|---------|-------------|-----------|------------|
| Read operations | ✅ | ✅ | ✅ | ✅ |
| Write operations | ❌ | ✅ | ❌ | ✅ |
| Git commands | Basic | All | Read-only | All |
| Testing | ❌ | ✅ | ❌ | ✅ |
| Package management | ❌ | ✅ | ❌ | ✅ |
| Destructive operations | ❌ | ⚠️ Some | ❌ | ⚠️ Some |

**Choose:**
- `minimal` - Untrusted environments
- `development` - Daily development
- `production` - Production systems (safest)
- `ai-session` - Rapid AI-assisted coding

---

### Q: Can I see what changed in my settings?

**A:** Yes! Compare with backup:

```bash
# Show current settings
aiterm claude settings show

# Compare with last backup
diff ~/.claude/settings.json \
     ~/.claude/settings.json.backup.20251221_103045
```

---

### Q: Does aiterm modify my existing iTerm2 profiles?

**A:** No! aiterm uses your existing profiles by name.

**What aiterm does:**
- Reads profile names from iTerm2
- Switches between profiles by name
- Does NOT modify profile settings

**What you control:**
- Profile colors, fonts, appearance (iTerm2 settings)
- Profile creation (iTerm2)
- Profile deletion (iTerm2)

**aiterm only switches between profiles you've created.**

---

## Next Steps

### Learn More

- **[API Documentation](../api/AITERM-API.md)** - Detailed CLI and Python API
- **[Architecture](../architecture/AITERM-ARCHITECTURE.md)** - How aiterm works internally
- **[Integration Guide](AITERM-INTEGRATION.md)** - Custom contexts and backends
- **[Troubleshooting](../troubleshooting/AITERM-TROUBLESHOOTING.md)** - Solve common issues

### Get Help

- **GitHub Issues:** https://github.com/Data-Wise/aiterm/issues
- **Discussions:** https://github.com/Data-Wise/aiterm/discussions
- **Documentation:** https://Data-Wise.github.io/aiterm/

### Contribute

- **Source Code:** https://github.com/Data-Wise/aiterm
- **Development Guide:** Coming in Phase 2
- **Plugin System:** Coming in Phase 2

---

## Congratulations! 🎉

You're now ready to use aiterm for optimized AI-assisted development!

**Remember:**
- ✅ Just `cd` to projects - aiterm handles the rest
- ✅ Production mode uses RED theme for safety
- ✅ Auto-approvals save time in Claude Code
- ✅ Manual override always available

**Happy coding!** 🚀

---

**Last Updated:** 2025-12-29
**Maintained By:** aiterm Development Team
