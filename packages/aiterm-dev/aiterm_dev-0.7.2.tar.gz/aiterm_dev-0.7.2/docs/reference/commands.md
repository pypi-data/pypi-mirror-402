# CLI Reference

Complete reference for all **aiterm** commands with examples.

---

## Global Options

```bash
aiterm --help              # Show help message
aiterm --version           # Show version info (enhanced in v0.6.0)
aiterm --install-completion  # Install shell completion
aiterm --show-completion    # Show completion script
```

### Enhanced `--version` (v0.6.0+)

```bash
aiterm --version
```

**Output:**
```
aiterm 0.6.0
Python: 3.12.0
Platform: macOS-15.2-arm64
Path: /Users/dt/.local/bin/aiterm
```

Shows version, Python runtime, platform, and installation path.

---

## Interactive Tutorials (v0.6.0)

Learn aiterm step-by-step with interactive tutorials.

### `aiterm learn start [TUTORIAL]`

Start an interactive tutorial.

```bash
aiterm learn start                    # Show tutorial menu
aiterm learn start getting-started    # Start beginner tutorial
aiterm learn start intermediate       # Start intermediate tutorial
aiterm learn start advanced           # Start advanced tutorial
ait learn start getting-started       # Short alias
```

**Tutorial Levels:**
- **Getting Started** - Installation verification, basic commands
- **Intermediate** - Context detection, profile switching, Claude integration
- **Advanced** - Custom workflows, automation, hooks

---

### `aiterm learn list`

List all available tutorials.

```bash
aiterm learn list
ait learn list
```

**Output:**
```
Available Tutorials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
getting-started   Learn the basics (10 min)
intermediate      Context & profiles (15 min)
advanced          Automation & hooks (20 min)

Start with: ait learn start <tutorial>
```

---

### `aiterm learn progress`

Show your learning progress.

```bash
aiterm learn progress
ait learn progress
```

**Output:**
```
Tutorial Progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
getting-started   ████████░░  80% (4/5 steps)
intermediate      ██░░░░░░░░  20% (1/5 steps)
advanced          ░░░░░░░░░░   0% (not started)
```

---

### `aiterm learn reset [TUTORIAL]`

Reset tutorial progress.

```bash
aiterm learn reset                    # Reset all progress
aiterm learn reset getting-started    # Reset specific tutorial
```

---

## Core Commands

### `aiterm doctor`

Check aiterm installation and configuration health.

```bash
aiterm doctor
```

**Output:**
```
aiterm doctor - Health check

Terminal: iTerm.app
Shell: /bin/zsh
Python: 3.12.0
aiterm: 0.6.0

Basic checks passed!
```

**What it checks:**
- Terminal type (iTerm2 detection)
- Shell environment
- Python version
- aiterm installation

---

### `aiterm hello`

Diagnostic greeting command.

```bash
aiterm hello              # Default greeting
aiterm hello --name "DT"  # Personalized greeting
```

**Output:**
```
👋 Hello from aiterm!
Version: 0.6.0
Terminal: iTerm.app
```

**With name:**
```
👋 Hello, DT!
Version: 0.6.0
Terminal: iTerm.app
```

Useful for verifying aiterm is installed and working correctly.

---

### `aiterm goodbye`

Farewell diagnostic command.

```bash
aiterm goodbye              # Default farewell
aiterm goodbye --name "DT"  # Personalized farewell
```

**Output:**
```
👋 Goodbye from aiterm!
Thanks for using aiterm 0.6.0
```

Pair with `hello` for quick installation testing.

---

### `aiterm info`

Display detailed system diagnostics.

```bash
aiterm info              # Full system info
aiterm info --json       # Output as JSON
```

**Output:**
```
aiterm System Information

Version: 0.6.0
Python: 3.12.0
Platform: macOS-15.2-arm64
Path: /Users/dt/.local/bin/aiterm

Environment:
  TERM_PROGRAM: iTerm.app
  SHELL: /bin/zsh
  CLAUDECODE: 1

Claude Code:
  Settings: ~/.claude/settings.json
  Hooks: 3 configured
  Permissions: 47 allowed
```

**JSON output:**
```bash
aiterm info --json | jq '.version'
# "0.6.0"
```

Useful for debugging, issue reports, and scripting.

---

### `aiterm init`

Interactive setup wizard (coming in v0.1.0 final).

```bash
aiterm init
```

**What it will do:**
- Detect terminal type
- Install base profiles
- Configure context detection
- Test installation

**Current status:** Placeholder (shows preview of features)

---

## Context Detection

### `aiterm detect [PATH]`

Detect project context for a directory.

```bash
# Current directory
aiterm detect

# Specific directory
aiterm detect ~/projects/my-app

# Short alias
ait detect
```

**Example output:**
```
Context Detection
┌────────────┬──────────────────────────┐
│ Directory  │ /Users/dt/projects/webapp│
│ Type       │ 📦 node                  │
│ Name       │ webapp                   │
│ Profile    │ Node-Dev                 │
│ Git Branch │ main *                   │
└────────────┴──────────────────────────┘
```

**Detects 8 context types:**
- 🚨 Production (`/production/`, `/prod/`)
- 🤖 AI Session (`/claude-sessions/`, `/gemini-sessions/`)
- 📦 R Package (`DESCRIPTION` file)
- 🐍 Python (`pyproject.toml`)
- 📦 Node.js (`package.json`)
- 📊 Quarto (`_quarto.yml`)
- 🔧 Emacs (`.spacemacs`)
- 🛠️ Dev Tools (`.git` + `scripts/`)

---

### `aiterm switch [PATH]`

Detect and apply context to terminal (iTerm2 only).

```bash
# Switch current directory context
aiterm switch

# Switch to specific directory
aiterm switch ~/production/live-site

# Short alias
ait switch
```

**What it does:**
1. Detects project context
2. Switches iTerm2 profile (colors)
3. Sets tab title with project name + git branch
4. Updates status bar variables

**Example:**
```bash
cd ~/production/myapp
ait switch
# → iTerm2 switches to Production profile (RED!)
# → Tab title: "🚨 production: myapp [main]"
```

---

### `aiterm context`

Subcommands for context management.

#### `aiterm context detect [PATH]`

Same as `aiterm detect` (full form).

```bash
aiterm context detect ~/projects/myapp
```

#### `aiterm context show`

Show current directory context (alias for `detect`).

```bash
aiterm context show
```

#### `aiterm context apply [PATH]`

Same as `aiterm switch` (full form).

```bash
aiterm context apply ~/projects/myapp
```

---

## Profile Management

### `aiterm profile list`

List available profiles (v0.2.0 feature preview).

```bash
aiterm profile list
```

**Output:**
```
Available Profiles:
  - default (iTerm2 base)
  - ai-session (Claude Code / Gemini)
  - production (warning colors)

Profile management coming in v0.2.0
```

**Coming in v0.2.0:**
- `aiterm profile show <name>` - Show profile details
- `aiterm profile install <name>` - Install profile template
- `aiterm profile create` - Interactive profile creator

---

## Claude Code Integration

### `aiterm claude settings`

Display current Claude Code settings.

```bash
aiterm claude settings
```

**Output:**
```
Claude Code Settings
┌───────────────────┬───────────────────────────┐
│ File              │ ~/.claude/settings.json   │
│ Permissions (allow)│ 47                       │
│ Permissions (deny) │ 0                        │
│ Hooks             │ 2                         │
└───────────────────┴───────────────────────────┘

Allowed:
  ✓ Bash(git status:*)
  ✓ Bash(git diff:*)
  ... and 45 more
```

---

### `aiterm claude backup`

Backup Claude Code settings with timestamp.

```bash
aiterm claude backup
```

**Output:**
```
✓ Backup created: ~/.claude/settings.backup-20241218-153045.json
```

**Backup format:**
- Location: Same directory as settings file
- Naming: `settings.backup-YYYYMMDD-HHMMSS.json`
- Automatic timestamping

---

### `aiterm claude approvals`

Manage auto-approval permissions.

#### `aiterm claude approvals list`

List current auto-approval permissions.

```bash
aiterm claude approvals list
```

**Output:**
```
Auto-Approvals (~/.claude/settings.json)

Allowed:
  ✓ Bash(git add:*)
  ✓ Bash(git commit:*)
  ✓ Bash(git diff:*)
  ✓ Bash(git log:*)
  ✓ Bash(git status:*)
  ✓ Bash(pytest:*)
  ✓ Bash(python3:*)
  ✓ Read(/Users/dt/**)
  ✓ WebSearch
```

---

#### `aiterm claude approvals presets`

List available approval presets.

```bash
aiterm claude approvals presets
```

**Output:**
```
Available Presets
┌────────────┬──────────────────────────────────┬─────────────┐
│ Name       │ Description                      │ Permissions │
├────────────┼──────────────────────────────────┼─────────────┤
│ safe-reads │ Read-only operations             │ 5           │
│ git-ops    │ Git commands                     │ 12          │
│ github-cli │ GitHub CLI operations            │ 8           │
│ python-dev │ Python development tools         │ 6           │
│ node-dev   │ Node.js development tools        │ 7           │
│ r-dev      │ R development tools              │ 5           │
│ web-tools  │ Web search and fetch             │ 2           │
│ minimal    │ Basic shell commands only        │ 10          │
└────────────┴──────────────────────────────────┴─────────────┘
```

---

#### `aiterm claude approvals add <preset>`

Add a preset to auto-approvals.

```bash
# Add safe read permissions
aiterm claude approvals add safe-reads

# Add Python dev tools
aiterm claude approvals add python-dev

# Add git operations
aiterm claude approvals add git-ops
```

**Output:**
```
✓ Added 6 permissions from 'python-dev':
  + Bash(python3:*)
  + Bash(pip3 install:*)
  + Bash(pytest:*)
  + Bash(python -m pytest:*)
  + Bash(uv:*)
  + Bash(uv pip install:*)
```

**Features:**
- Automatic backup before changes
- Duplicate detection (won't add existing permissions)
- Shows exactly what was added

**Available presets:**

**safe-reads** (5 permissions)
- Read-only file operations
- Non-destructive commands

**git-ops** (12 permissions)
- Git status, diff, log
- Git add, commit, push
- Git checkout, branch operations
- No destructive git commands

**github-cli** (8 permissions)
- `gh pr list/view/create`
- `gh issue list/view`
- `gh api` (read-only)
- No `gh pr merge` without confirmation

**python-dev** (6 permissions)
- pytest, python3, pip3
- uv pip install
- Standard Python tooling

**node-dev** (7 permissions)
- npm install/run
- npx commands
- bun operations

**r-dev** (5 permissions)
- Rscript, R CMD
- quarto commands

**web-tools** (2 permissions)
- WebSearch
- WebFetch (read-only)

**minimal** (10 permissions)
- Basic shell: ls, cat, echo
- Safe navigation: cd, pwd
- No write/modify operations

---

## StatusLine (v0.7.0)

Powerlevel10k-style 2-line status display for Claude Code CLI.

### `aiterm statusline install`

Install StatusLine into Claude Code settings.

```bash
aiterm statusline install
ait statusline install  # Short alias
```

**What it does:**
- Updates `~/.claude/settings.json`
- Sets statusLine command to `ait statusline render`
- Creates backup of previous settings
- Verifies installation

**Output:**
```
✓ Backup created: ~/.claude/settings.backup-20251231-120000.json
✓ StatusLine installed successfully

Configuration:
  Command: ait statusline render
  Type: command
  Update Interval: 300ms (Claude Code default)

Next: Start a new Claude Code session to see StatusLine!
```

---

### `aiterm statusline test`

Test StatusLine with mock data.

```bash
aiterm statusline test
ait statusline test
```

**Output:**
```
╭─ ░▒▓ 🐍 aiterm (venv: py3.11)  main* ⇣2 ⇡1 ?3 📦5 ▓▒░
╰─ Sonnet 4.5 │ 🌅 10:30 │ ⏱ 5m 🟢 │ 🤖2 │ +123/-45 │ [learning]
```

---

### `aiterm statusline config`

Manage StatusLine configuration.

#### `aiterm statusline config`

Interactive configuration menu.

```bash
aiterm statusline config
```

**Output:**
```
StatusLine Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. List all settings
2. Get a value
3. Set a value
4. Reset to defaults
5. Edit in $EDITOR
6. Validate configuration

Choose an option:
```

---

#### `aiterm statusline config list`

List all configuration settings.

```bash
aiterm statusline config list
aiterm statusline config list --category display
aiterm statusline config list --category git
```

**Output:**
```
StatusLine Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Display Settings (12):
  display.directory_mode          smart
  display.show_git                true
  display.show_thinking_indicator true
  display.show_output_style       auto
  display.show_session_duration   true
  display.show_current_time       true
  display.show_lines_changed      true
  display.show_r_version          true
  display.show_background_agents  true
  display.show_mcp_status         false
  display.max_directory_length    50

Git Settings (5):
  git.show_ahead_behind          true
  git.show_untracked_count       true
  git.show_stash_count           true
  git.show_remote_status         true
  git.truncate_branch_length     32
```

**Categories:**
- `display` - Display toggles and formatting (12 settings)
- `git` - Git information display (5 settings)
- `project` - Project context detection (4 settings)
- `time` - Time tracking options (3 settings)
- `theme` - Color theme settings (2 settings)
- `usage` - Usage tracking (disabled, 3 settings)

---

#### `aiterm statusline config get <key>`

Get a configuration value.

```bash
aiterm statusline config get display.show_git
aiterm statusline config get theme.name
aiterm statusline config get git.show_stash_count
```

**Output:**
```
display.show_git = true
```

---

#### `aiterm statusline config set <key> <value>`

Set a configuration value.

```bash
# Toggle features
aiterm statusline config set display.show_git false
aiterm statusline config set git.show_stash_count true

# Change theme
aiterm statusline config set theme.name cool-blues

# Set numeric values
aiterm statusline config set git.truncate_branch_length 40
```

**Output:**
```
✓ Updated: display.show_git = false
```

**Type conversion:**
- `true/false` → boolean
- Numbers → integer
- Strings → string
- Validation automatically applied

---

#### `aiterm statusline config reset [key]`

Reset configuration to defaults.

```bash
# Reset all settings
aiterm statusline config reset

# Reset single key
aiterm statusline config reset display.show_git
```

**Output:**
```
✓ Configuration reset to defaults
```

---

#### `aiterm statusline config edit`

Edit configuration in $EDITOR.

```bash
aiterm statusline config edit
```

Opens `~/.config/aiterm/statusline.json` in your editor with validation on save.

---

#### `aiterm statusline config spacing <preset>`

Configure gap spacing between left and right segments (v0.7.1+).

```bash
# Apply a spacing preset
aiterm statusline config spacing minimal    # Tight (15%, 5-20 chars)
aiterm statusline config spacing standard   # Balanced (20%, 10-40 chars) [default]
aiterm statusline config spacing spacious   # Wide (30%, 15-60 chars)

# Short alias
ait statusline config spacing minimal
```

**Spacing Presets:**

| Preset | Gap Size | Min-Max | Use Case |
|--------|----------|---------|----------|
| **minimal** | 15% of terminal width | 5-20 chars | Compact, information-dense |
| **standard** | 20% of terminal width | 10-40 chars | Balanced (default) |
| **spacious** | 30% of terminal width | 15-60 chars | Wide, maximum clarity |

**What it does:**
- Sets gap size between left (project+git) and right (worktree) segments
- Adds optional centered separator (`…`) in the gap
- Constrains gap within min/max limits for consistency

**Output:**
```
✓ Spacing preset updated

  Setting      Old        New
  ──────────────────────────────
  spacing.mode standard   minimal

✓ Spacing set to 'minimal'

Run 'ait statusline test' to preview the new spacing
```

**Manual overrides:**
```bash
# Set custom minimum gap
ait statusline config set spacing.min_gap 12

# Set custom maximum gap
ait statusline config set spacing.max_gap 50

# Disable separator
ait statusline config set spacing.show_separator false
```

**See also:** [StatusLine Spacing Guide](../guides/statusline-spacing.md)

---

#### `aiterm statusline config preset <name>`

Apply a configuration preset (v0.7.0+).

```bash
# Apply minimal preset (disables bloat)
aiterm statusline config preset minimal

# Short alias
ait statusline config preset minimal
```

**Available presets:**
- `minimal` - Disables session duration, current time, lines changed, usage tracking

**Output:**
```
✓ Applied minimal preset

  Disabled:
    • display.show_session_duration
    • display.show_current_time
    • display.show_lines_changed
    • usage.enabled
    • usage.show_session
    • usage.show_weekly

Restart Claude Code to see changes
```

**See also:** [Minimal StatusLine Guide](../guides/statusline-minimal.md)

---

### `aiterm statusline theme`

Manage color themes.

#### `aiterm statusline theme list`

List available themes.

```bash
aiterm statusline theme list
```

**Output:**
```
Available Themes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
purple-charcoal  Purple + dark gray (default)
cool-blues       Blue tones (calm, professional)
forest-greens    Green tones (natural, easy on eyes)

Current: purple-charcoal

Switch with: ait statusline theme set <theme>
```

---

#### `aiterm statusline theme set <theme>`

Switch to a different theme.

```bash
aiterm statusline theme set cool-blues
aiterm statusline theme set forest-greens
aiterm statusline theme set purple-charcoal  # Default
```

**Output:**
```
✓ Theme changed to: cool-blues
  Restart Claude Code to see changes
```

---

#### `aiterm statusline theme show`

Show current theme details.

```bash
aiterm statusline theme show
```

**Output:**
```
Current Theme: purple-charcoal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:       Purple (141)
Git:           Cyan (75)
Model:         Purple (141)
Separator:     Gray (240)
Time:          Green (107)
Lines Added:   Green (2)
Lines Removed: Red (1)
```

---

### `aiterm statusline doctor`

Validate StatusLine installation and configuration.

```bash
aiterm statusline doctor
```

**Output:**
```
StatusLine Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Claude Code settings found
✓ StatusLine command configured
✓ Config file exists
✓ Theme loaded successfully
✓ All segments functional

Status: Ready ✨
```

---

### `aiterm statusline uninstall`

Remove StatusLine from Claude Code settings.

```bash
aiterm statusline uninstall
```

**Output:**
```
✓ Backup created: ~/.claude/settings.backup-20251231-120000.json
✓ StatusLine removed from Claude Code settings

Configuration file preserved at: ~/.config/aiterm/statusline.json
```

---

### `aiterm statusline render`

Render StatusLine (called by Claude Code).

```bash
# Not usually called directly
# Claude Code runs this command every 300ms
echo '{"workspace":{"current_dir":"..."}}' | ait statusline render
```

**Usage:** Set as statusLine command in `~/.claude/settings.json`.

---

## OpenCode Integration

### `aiterm opencode config`

Display current OpenCode configuration.

```bash
aiterm opencode config
aiterm opencode config --raw    # Output as JSON
```

---

### `aiterm opencode validate`

Validate OpenCode configuration against schema.

```bash
aiterm opencode validate
```

---

### `aiterm opencode backup`

Backup OpenCode configuration with timestamp.

```bash
aiterm opencode backup
```

---

### `aiterm opencode servers`

Manage MCP server configurations.

#### `aiterm opencode servers list`

List all configured MCP servers.

```bash
aiterm opencode servers list
```

#### `aiterm opencode servers enable <name>`

Enable a disabled server.

```bash
aiterm opencode servers enable github
aiterm opencode servers enable sequential-thinking
```

#### `aiterm opencode servers disable <name>`

Disable an enabled server.

```bash
aiterm opencode servers disable playwright
```

#### `aiterm opencode servers test <name>`

Test if a server can start successfully.

```bash
aiterm opencode servers test filesystem
aiterm opencode servers test time --timeout 5
```

**Output:**
```
Testing filesystem...
Command: npx -y @modelcontextprotocol/server-filesystem /Users/dt
✓ Server 'filesystem' started successfully
```

#### `aiterm opencode servers health`

Check health of all enabled servers.

```bash
aiterm opencode servers health          # Check enabled servers
aiterm opencode servers health --all    # Check all servers
```

**Output:**
```
                           MCP Server Health
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Server              ┃ Enabled ┃ Status ┃ Details                    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ filesystem          │ yes     │ ✓ OK   │ Started successfully       │
│ memory              │ yes     │ ✓ OK   │ Started successfully       │
│ github              │ yes     │ ✓ OK   │ Started successfully       │
└─────────────────────┴─────────┴────────┴────────────────────────────┘
Summary: 3 ok, 0 errors
```

#### `aiterm opencode servers templates`

List available MCP server templates.

```bash
aiterm opencode servers templates
```

**Available templates:**
- `filesystem` - File system read/write access
- `memory` - Persistent context memory
- `sequential-thinking` - Complex reasoning chains
- `playwright` - Browser automation
- `time` - Timezone tracking
- `github` - PR/issue management (requires GITHUB_TOKEN)
- `brave-search` - Web search (requires BRAVE_API_KEY)
- `slack` - Slack integration (requires SLACK_TOKEN)
- `sqlite` - SQLite database access
- `puppeteer` - Headless browser
- `fetch` - HTTP fetch for web content
- `everything` - Demo server (testing only)

#### `aiterm opencode servers add <name>`

Add a new MCP server configuration.

```bash
# Add from template
aiterm opencode servers add brave-search --template

# Add with custom command
aiterm opencode servers add myserver --command "npx -y my-mcp-server"

# Add disabled
aiterm opencode servers add sqlite --template --disabled
```

#### `aiterm opencode servers remove <name>`

Remove an MCP server configuration.

```bash
aiterm opencode servers remove myserver
aiterm opencode servers remove filesystem --force  # Force remove essential
```

---

### `aiterm opencode agents`

Manage custom agent configurations.

#### `aiterm opencode agents list`

List configured agents.

```bash
aiterm opencode agents list
```

#### `aiterm opencode agents add <name>`

Add a new custom agent.

```bash
aiterm opencode agents add quick --desc "Fast responses" --model anthropic/claude-haiku-4-5
```

#### `aiterm opencode agents remove <name>`

Remove a custom agent.

```bash
aiterm opencode agents remove quick
```

---

### `aiterm opencode models`

List recommended models for OpenCode.

```bash
aiterm opencode models
```

---

### `aiterm opencode set-model <model>`

Set the primary or small model.

```bash
aiterm opencode set-model anthropic/claude-opus-4-5           # Set primary
aiterm opencode set-model anthropic/claude-haiku-4-5 --small  # Set small model
```

---

## Terminal Management

### `aiterm terminals list`

List all supported terminal emulators with installation status.

```bash
aiterm terminals list
```

**Output:**
```
                         Supported Terminals
┏━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Terminal  ┃ Installed ┃ Version      ┃ Active ┃ Features             ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ iterm2    │ ✓         │ unknown      │        │ profiles, tab_title  │
│ kitty     │ ✗         │ -            │        │ -                    │
│ alacritty │ ✗         │ -            │        │ -                    │
│ wezterm   │ ✓         │ 20240203...  │        │ tab_title, lua_config│
│ ghostty   │ ✓         │ 1.2.3        │   ●    │ tab_title, themes    │
└───────────┴───────────┴──────────────┴────────┴──────────────────────┘
```

**Supported terminals:**
- **iTerm2** - macOS terminal with profiles, badges, status bar
- **Kitty** - GPU-accelerated with kitten plugins
- **Alacritty** - Minimalist, YAML configuration
- **WezTerm** - Cross-platform with Lua scripting
- **Ghostty** - Fast, native UI with themes (v0.3.9+)

---

### `aiterm terminals detect`

Detect and display information about the current terminal.

```bash
aiterm terminals detect
```

**Output:**
```
Terminal Detection

✓ Detected: ghostty
  Version: Ghostty 1.2.3

Version
  - version: 1.2.3
  - channel: stable
Build Config
  - Zig version: 0.14.1
  - build mode: ReleaseFast
  Features: tab_title, themes, native_ui
```

**Detection methods:**
- Environment variables (`TERM_PROGRAM`, `GHOSTTY_RESOURCES_DIR`)
- Process inspection
- Version command output parsing

---

### `aiterm terminals features <terminal>`

Show features supported by a specific terminal.

```bash
aiterm terminals features ghostty
aiterm terminals features iterm2
```

**Output (Ghostty):**
```
╭─────────────────── ghostty Features ────────────────────╮
│   ✓ tab_title                                           │
│   ✓ themes                                              │
│   ✓ native_ui                                           │
│                                                         │
│   Config: ~/.config/ghostty/config                      │
╰─────────────────────────────────────────────────────────╯
```

**Feature types:**
- `profiles` - Named configuration profiles
- `tab_title` - Tab/window title setting
- `badge` - Status badges (iTerm2)
- `themes` - Theme switching
- `native_ui` - Native macOS UI elements
- `lua_config` - Lua scripting support

---

### `aiterm terminals config <terminal>`

Show configuration file location for a terminal.

```bash
aiterm terminals config ghostty
aiterm terminals config iterm2
aiterm terminals config wezterm
```

**Output:**
```
Config path: ~/.config/ghostty/config
```

**Config locations:**
| Terminal | Config Path |
|----------|-------------|
| Ghostty | `~/.config/ghostty/config` |
| iTerm2 | `~/Library/Preferences/com.googlecode.iterm2.plist` |
| Kitty | `~/.config/kitty/kitty.conf` |
| Alacritty | `~/.config/alacritty/alacritty.toml` |
| WezTerm | `~/.wezterm.lua` |

---

### `aiterm terminals compare`

Compare features across all terminal emulators.

```bash
aiterm terminals compare
```

**Output:**
```
                    Terminal Feature Comparison
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┓
┃ Terminal  ┃ Profiles ┃ Tab Title ┃ Badge ┃ Themes ┃ Native UI ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━┩
│ iTerm2    │    ✓     │     ✓     │   ✓   │   ✓    │     ✓     │
│ Kitty     │    ✓     │     ✓     │   ✗   │   ✓    │     ✗     │
│ Alacritty │    ✗     │     ✓     │   ✗   │   ✓    │     ✗     │
│ WezTerm   │    ✓     │     ✓     │   ✗   │   ✓    │     ✓     │
│ Ghostty   │    ✗     │     ✓     │   ✗   │   ✓    │     ✓     │
└───────────┴──────────┴───────────┴───────┴────────┴───────────┘
```

---

### `aiterm terminals title <text>`

Set the terminal tab or window title.

```bash
aiterm terminals title "Working on aiterm"
aiterm terminals title "🚀 Production Server"
```

**Note:** Works with terminals that support the `tab_title` feature.

---

### `aiterm terminals profile <name>`

Switch to a named terminal profile (iTerm2 only).

```bash
aiterm terminals profile "Python-Dev"
aiterm terminals profile "Production"
```

**Note:** Requires iTerm2 with the named profile configured.

---

## Ghostty Integration (v0.3.9+, Enhanced v0.3.15)

Commands for managing Ghostty terminal configuration. Ghostty is a fast, GPU-accelerated terminal emulator by Mitchell Hashimoto.

### `aiterm ghostty status`

Show current Ghostty configuration.

```bash
aiterm ghostty status
ait ghostty status
```

**Output:**
```
Ghostty Configuration
========================================
Config file: /Users/dt/.config/ghostty/config

Font:       JetBrains Mono @ 14pt
Theme:      catppuccin-mocha
Padding:    x=10, y=8
Opacity:    1.0
Cursor:     block
```

---

### `aiterm ghostty config`

Display config file location and current values.

```bash
aiterm ghostty config
```

**Output:**
```
Config Path: ~/.config/ghostty/config

Current values:
  font-family = JetBrains Mono
  font-size = 14
  theme = catppuccin-mocha
  window-padding-x = 10
  window-padding-y = 8
```

---

### `aiterm ghostty theme [name]`

List available themes or set a theme.

```bash
# List all 14 built-in themes
aiterm ghostty theme

# Set a theme
aiterm ghostty theme dracula
aiterm ghostty theme tokyo-night
```

**Output (list):**
```
Available Ghostty Themes (14)

catppuccin-mocha    catppuccin-latte    catppuccin-frappe
catppuccin-macchiato dracula            gruvbox-dark
gruvbox-light       nord               solarized-dark
solarized-light     tokyo-night        tokyo-night-storm
one-dark            one-light

Current: catppuccin-mocha

Set theme: aiterm ghostty theme <name>
```

**Output (set):**
```
✓ Theme set to 'dracula'
  Config updated: ~/.config/ghostty/config
  Note: Ghostty auto-reloads on config change
```

---

### `aiterm ghostty font [family] [size]`

Get or set font configuration.

```bash
# Show current font
aiterm ghostty font

# Set font family only
aiterm ghostty font "Fira Code"

# Set font family and size
aiterm ghostty font "JetBrains Mono" 16
```

**Output (get):**
```
Current Font: JetBrains Mono @ 14pt
```

**Output (set):**
```
✓ Font updated
  Family: JetBrains Mono
  Size: 16pt
```

---

### `aiterm ghostty set <key> <value>`

Set any Ghostty configuration value.

```bash
# Set window padding
aiterm ghostty set window-padding-x 12
aiterm ghostty set window-padding-y 8

# Set background opacity
aiterm ghostty set background-opacity 0.95

# Set cursor style
aiterm ghostty set cursor-style underline
```

**Output:**
```
✓ Set window-padding-x = 12
  Config: ~/.config/ghostty/config
```

**Common configuration keys:**
| Key | Values | Description |
|-----|--------|-------------|
| `theme` | Theme name | Color scheme |
| `font-family` | Font name | Monospace font |
| `font-size` | Integer | Font size in points |
| `window-padding-x` | Integer | Horizontal padding |
| `window-padding-y` | Integer | Vertical padding |
| `background-opacity` | 0.0-1.0 | Window transparency |
| `cursor-style` | block/bar/underline | Cursor shape |

---

### Profile Management (v0.3.15)

#### `aiterm ghostty profile list`

List all saved profiles.

```bash
aiterm ghostty profile list
```

#### `aiterm ghostty profile show <name>`

Show details of a specific profile.

```bash
aiterm ghostty profile show coding
```

#### `aiterm ghostty profile create <name> [description]`

Create a new profile from current configuration.

```bash
aiterm ghostty profile create coding "My development setup"
```

#### `aiterm ghostty profile apply <name>`

Apply a saved profile to the config.

```bash
aiterm ghostty profile apply coding
```

#### `aiterm ghostty profile delete <name>`

Delete a saved profile.

```bash
aiterm ghostty profile delete old-profile
```

**Profile storage:** `~/.config/ghostty/profiles/*.conf`

---

### Config Backup (v0.3.15)

#### `aiterm ghostty backup`

Create a timestamped backup of the current config.

```bash
aiterm ghostty backup
aiterm ghostty backup --suffix before-update
```

**Output:**
```
✓ Backup created: ~/.config/ghostty/config.backup.20251230123456
```

#### `aiterm ghostty restore [backup]`

List backups or restore from a specific backup.

```bash
# List available backups
aiterm ghostty restore

# Restore from specific backup
aiterm ghostty restore config.backup.20251230123456
```

---

### Keybind Management (v0.3.15)

#### `aiterm ghostty keybind list`

List all keybindings from config.

```bash
aiterm ghostty keybind list
```

#### `aiterm ghostty keybind add <trigger> <action>`

Add a keybinding to config.

```bash
aiterm ghostty keybind add "ctrl+t" "new_tab"
aiterm ghostty keybind add "ctrl+q" "quit" --prefix global:
```

**Supported prefixes:**
- `global:` - Works even when terminal isn't focused
- `unconsumed:` - Only if not consumed by shell
- `all:` - Combines global + unconsumed

#### `aiterm ghostty keybind remove <trigger>`

Remove a keybinding.

```bash
aiterm ghostty keybind remove "ctrl+t"
```

#### `aiterm ghostty keybind preset <name>`

Apply a keybind preset.

```bash
aiterm ghostty keybind preset vim
aiterm ghostty keybind preset emacs
aiterm ghostty keybind preset tmux
aiterm ghostty keybind preset macos
```

**Available presets:**

| Preset | Description |
|--------|-------------|
| `vim` | Vim-style navigation (ctrl+h/j/k/l, ctrl+w prefixes) |
| `emacs` | Emacs-style (ctrl+x prefixes, buffer navigation) |
| `tmux` | tmux-style (ctrl+b prefix for all operations) |
| `macos` | macOS native (cmd+t/w/d, cmd+shift+[]) |

---

### Session Management (v0.3.15)

#### `aiterm ghostty session list`

List all saved sessions.

```bash
aiterm ghostty session list
```

#### `aiterm ghostty session show <name>`

Show details of a saved session.

```bash
aiterm ghostty session show work
```

#### `aiterm ghostty session save <name>`

Save current state as a session.

```bash
aiterm ghostty session save work
aiterm ghostty session save dev --description "Development session" --layout split-h
```

**Layout types:** `single`, `split-h`, `split-v`, `grid`

#### `aiterm ghostty session restore <name>`

Restore a saved session.

```bash
aiterm ghostty session restore work
```

#### `aiterm ghostty session delete <name>`

Delete a saved session.

```bash
aiterm ghostty session delete old-session
```

#### `aiterm ghostty session split [direction]`

Create a terminal split.

```bash
aiterm ghostty session split right    # Horizontal split
aiterm ghostty session split down     # Vertical split
```

**Session storage:** `~/.config/ghostty/sessions/*.json`

---

## Craft Plugin Management (v0.4.0)

Commands for managing Claude Code's craft plugin - a collection of commands, skills, and agents.

### `aiterm craft status`

Show craft plugin installation status and overview.

```bash
aiterm craft status
ait craft status
```

**Output:**
```
Craft Plugin Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Installed: ~/.claude/plugins/craft
  Source: ~/projects/dev-tools/claude-plugins/craft
  Version: 1.8.0

Overview:
  Commands: 60
  Skills: 16
  Agents: 8
```

---

### `aiterm craft list`

List available craft commands, skills, and agents.

```bash
aiterm craft list              # List all
aiterm craft list --commands   # Commands only
aiterm craft list --skills     # Skills only
aiterm craft list --agents     # Agents only
```

---

### `aiterm craft install`

Install or reinstall craft plugin via symlink.

```bash
aiterm craft install
aiterm craft install --source ~/my-craft-plugin
```

Creates symlink: `~/.claude/plugins/craft` → source directory

---

### `aiterm craft update`

Update craft plugin (git pull in source directory).

```bash
aiterm craft update
```

---

### `aiterm craft sync`

Sync craft with project context detection.

```bash
aiterm craft sync                    # Auto-detect project type
aiterm craft sync --type python      # Force Python project type
aiterm craft sync --type node        # Force Node.js project type
aiterm craft sync --type r           # Force R project type
```

---

### `aiterm craft run <command>`

Show how to run a craft command in Claude Code.

```bash
aiterm craft run commit
aiterm craft run test:generate
```

**Output:**
```
To run 'commit' in Claude Code:

  /craft:commit

Or invoke via chat:
  "Run the craft commit workflow"
```

---

### `aiterm craft commands [namespace]`

Show detailed craft command info.

```bash
aiterm craft commands              # All namespaces
aiterm craft commands git          # Git commands only
aiterm craft commands test         # Test commands only
aiterm craft commands docs         # Docs commands only
```

---

## Workflows (v0.4.0)

Session-aware workflow runner with built-in and custom workflow support.

### `aiterm workflows status`

Check session status and available workflows.

```bash
aiterm workflows status
ait workflows status
```

**Output:**
```
Workflow Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session: ✓ Active (1766786256-71941)
Project: aiterm
Branch: dev

Available Workflows (13):
  test      Run project tests
  lint      Run linter (ruff/eslint/lintr)
  format    Auto-format code
  check     Type checking (mypy/tsc)
  build     Build project
  docs      Build documentation
  ...
```

---

### `aiterm workflows run <name>`

Run a workflow with session task updates.

```bash
# Run single workflow
aiterm workflows run test
aiterm workflows run lint
aiterm workflows run docs

# Chain multiple workflows with +
aiterm workflows run lint+test
aiterm workflows run format+lint+test+build
```

**Workflow chaining:**
- Use `+` to chain workflows: `lint+test+build`
- Executes sequentially, stops on first failure
- Session task updates show progress: "Running lint+test (2/3)"

**Example output:**
```
Running workflow: lint+test

[1/2] lint
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running: ruff check .
✓ Lint passed

[2/2] test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running: pytest
✓ Tests passed (44 passed in 0.58s)

✓ Workflow chain completed successfully
```

---

### `aiterm workflows task <description>`

Update current session task description.

```bash
aiterm workflows task "Implementing feature X"
aiterm workflows task "Code review for PR #123"
```

---

### `aiterm workflows list`

List all available workflows (built-in + custom).

```bash
aiterm workflows list
```

**Output:**
```
Available Workflows
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Built-in (13):
  test        Run project tests
  lint        Run linter (ruff/eslint/lintr)
  format      Auto-format code
  check       Type checking (mypy/tsc)
  build       Build project (wheel/bundle)
  docs        Build documentation
  docs-serve  Serve docs locally
  clean       Clean build artifacts
  deploy-docs Deploy to GitHub Pages
  release     Full release workflow

Custom (2):
  my-deploy   Custom deployment workflow
  ci-check    Pre-CI validation
```

---

### Built-in Workflows

| Workflow | Description | Command |
|----------|-------------|---------|
| `test` | Run project tests | Auto-detected (pytest/npm test/testthat) |
| `lint` | Run linter | ruff/eslint/lintr |
| `format` | Auto-format code | ruff format/prettier/styler |
| `check` | Type checking | mypy/tsc |
| `build` | Build project | wheel/npm build/R CMD build |
| `docs` | Build documentation | mkdocs build/quarto |
| `docs-serve` | Serve docs locally | mkdocs serve |
| `clean` | Clean artifacts | rm -rf dist/ build/ |
| `deploy-docs` | Deploy to GitHub Pages | mkdocs gh-deploy |
| `release` | Full release | lint+test+build+deploy |

---

### Custom YAML Workflows

Create custom workflows in `~/.config/aiterm/workflows/`.

#### `aiterm workflows custom list`

List custom workflows.

```bash
aiterm workflows custom list
```

#### `aiterm workflows custom show <name>`

Show custom workflow details.

```bash
aiterm workflows custom show my-deploy
```

#### `aiterm workflows custom create <name>`

Create a new custom workflow.

```bash
aiterm workflows custom create my-deploy
```

Creates `~/.config/aiterm/workflows/my-deploy.yaml`:

```yaml
name: my-deploy
description: Custom deployment workflow
commands:
  - git pull origin main
  - npm run build
  - npm run deploy
requires_session: false
```

#### `aiterm workflows custom delete <name>`

Delete a custom workflow.

```bash
aiterm workflows custom delete my-deploy
```

---

### Custom Workflow YAML Format

```yaml
# ~/.config/aiterm/workflows/example.yaml
name: example
description: Example workflow description
commands:
  - echo "Step 1"
  - echo "Step 2"
  - npm run build
requires_session: false  # true if Claude Code session required
```

**Fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Workflow identifier |
| `description` | Yes | Human-readable description |
| `commands` | Yes | List of shell commands to run |
| `requires_session` | No | Whether active Claude Code session is required (default: false) |

---

## Feature Workflow (v0.3.13)

Commands for managing feature branches and worktrees.

### `aiterm feature status`

Show feature branch pipeline visualization.

```bash
aiterm feature status
ait feature status
```

**Output:**
```
Feature Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

main ──────► dev ──────► feature/*
  │            │
  │            ├── feature/auth (worktree: ~/.git-worktrees/aiterm/auth)
  │            │     └── 3 commits ahead
  │            │
  │            └── feature/api-v2
  │                  └── 7 commits ahead, needs rebase

Branch: dev (current)
Status: 2 active features
```

---

### `aiterm feature list`

List feature branches with details.

```bash
aiterm feature list          # Active features
aiterm feature list --all    # Include merged
```

---

### `aiterm feature start <name>`

Start a new feature branch.

```bash
aiterm feature start auth
aiterm feature start api-v2 --worktree    # Create worktree
aiterm feature start api-v2 -w            # Short form
aiterm feature start ui --base main       # Custom base branch
aiterm feature start ui --no-install      # Skip dependency install
```

---

### `aiterm feature cleanup`

Clean up merged feature branches.

```bash
aiterm feature cleanup              # Interactive
aiterm feature cleanup --dry-run    # Preview only
aiterm feature cleanup --force      # No confirmation
```

---

## Release Management (v0.5.0)

Commands for managing releases to PyPI and Homebrew.

### `aiterm release check`

Validate release readiness.

```bash
aiterm release check
ait release check
ait release check --skip-tests    # Skip running tests
ait release check --verbose       # Show detailed output
```

**Output:**
```
╭─────────────────╮
│ Release Check   │
╰─────────────────╯

✓  Version consistency       0.5.0
✓  Tests                     55 passed in 1.03s
✓  Clean working tree        No uncommitted changes
✓  On main branch            Current: main
✓  Tag available             v0.5.0 not yet tagged

Ready to release v0.5.0

Next steps:
  ait release tag 0.5.0
  ait release pypi
```

**Checks:**
- Version consistency across pyproject.toml, __init__.py, CHANGELOG.md
- All tests passing
- Clean git working tree
- On main/master branch
- Tag not already existing

---

### `aiterm release status`

Show current release state and pending changes.

```bash
aiterm release status
ait release status
```

**Output:**
```
╭────────────────╮
│ Release Status │
╰────────────────╯

Current version: 0.5.0
Latest tag: v0.4.0
Commits since tag: 5

Pending changes:
  • feat(release): complete all v0.5.0 release commands
  • feat(release): add pypi command for build and publish
  • feat(release): add release management CLI commands
  • docs: add v0.5.0 plan - release automation
  • docs: streamline CLAUDE.md for v0.4.0

Suggested next versions:
  Patch: 0.5.1
  Minor: 0.6.0
  Major: 1.0.0
```

---

### `aiterm release pypi`

Build and publish package to PyPI.

```bash
aiterm release pypi
ait release pypi --dry-run      # Build only, don't publish
ait release pypi --test         # Publish to TestPyPI
ait release pypi --skip-build   # Use existing dist/
ait release pypi --skip-verify  # Skip PyPI verification
```

**Output:**
```
╭─────────────────╮
│ Publish to PyPI │
╰─────────────────╯

Package: aiterm-dev
Version: 0.5.0

Building package...
✓ Built with uv
  • aiterm_dev-0.5.0-py3-none-any.whl
  • aiterm_dev-0.5.0.tar.gz

Publishing to PyPI...
✓ Published with uv

Verifying on PyPI (may take a moment)...
✓ Verified: aiterm-dev 0.5.0 on PyPI

Published aiterm-dev 0.5.0 to PyPI!

Install with:
  pip install aiterm-dev==0.5.0
```

---

### `aiterm release tag`

Create an annotated git tag.

```bash
aiterm release tag 0.5.0
ait release tag                      # Use version from pyproject.toml
ait release tag 0.5.0 -m "Release"   # Custom message
ait release tag 0.5.0 --push         # Push tag to origin
```

**Output:**
```
✓ Created tag v0.5.0
Push with: git push origin v0.5.0
```

---

### `aiterm release notes`

Generate release notes from commits since last tag.

```bash
aiterm release notes
ait release notes 0.5.0               # Specify version for header
ait release notes --since v0.4.0      # Compare from specific tag
ait release notes -o RELEASE.md       # Write to file
ait release notes --clipboard         # Copy to clipboard
```

**Output:**
```markdown
# Release v0.5.0

## ✨ Features

- complete all v0.5.0 release commands
- add pypi command for build and publish
- add release management CLI commands

## 📚 Documentation

- add v0.5.0 plan - release automation
- streamline CLAUDE.md for v0.4.0

---

**Full Changelog**: https://github.com/Data-Wise/aiterm/compare/v0.5.0...HEAD
```

**Categories:**
- ✨ Features (feat:)
- 🐛 Bug Fixes (fix:)
- 📚 Documentation (docs:)
- ♻️ Refactoring (refactor:)
- 🧪 Tests (test:)
- 🔧 Chores (chore:)
- 📝 Other Changes

---

### `aiterm release homebrew`

Update Homebrew formula in tap.

```bash
aiterm release homebrew
ait release homebrew --tap ~/homebrew-tap   # Specify tap path
ait release homebrew --version 0.5.0        # Specify version
ait release homebrew --commit --push        # Commit and push
ait release homebrew --dry-run              # Preview only
```

**Output:**
```
╭─────────────────────────╮
│ Update Homebrew Formula │
╰─────────────────────────╯

Package: aiterm-dev
Version: 0.5.0

Fetching SHA256 from PyPI...
✓ SHA256: a1b2c3d4e5f6...

Updating formula...
✓ Updated aiterm.rb

Homebrew formula updated for aiterm-dev 0.5.0!

Test with:
  brew update && brew upgrade aiterm
```

---

### `aiterm release full`

Full release workflow: check → tag → push → pypi → homebrew.

```bash
aiterm release full 0.5.0
ait release full 0.5.0 --dry-run        # Preview steps
ait release full 0.5.0 --skip-tests     # Skip test step
ait release full 0.5.0 --skip-homebrew  # Skip Homebrew update
```

**Output:**
```
╭─────────────────────╮
│ Full Release: v0.5.0│
╰─────────────────────╯

Step 1/5: Validate release readiness
✓ Ready for release

Step 2/5: Create git tag
✓ Created v0.5.0

Step 3/5: Push tag to origin
✓ Pushed v0.5.0

Step 4/5: Publish to PyPI
Building package...
✓ Built with uv
Publishing...
✓ Published with uv

Step 5/5: Update Homebrew formula
✓ Updated aiterm.rb
✓ Pushed formula update

╭───────────────────────────────────────────────╮
│ 🎉 Released aiterm v0.5.0!                    │
│                                               │
│ PyPI: https://pypi.org/project/aiterm-dev/   │
│ GitHub: https://github.com/Data-Wise/aiterm  │
╰───────────────────────────────────────────────╯
```

**Steps executed:**
1. **Check** - Validate version, tests, git status
2. **Tag** - Create annotated git tag
3. **Push** - Push tag to origin
4. **PyPI** - Build and publish package
5. **Homebrew** - Update formula (optional)

---

## Examples

### Quick Setup for Claude Code

```bash
# 1. Check installation
ait doctor

# 2. View current settings
ait claude settings

# 3. Backup before changes
ait claude backup

# 4. Add safe permissions
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev

# 5. Verify
ait claude approvals list
```

### Context Switching Workflow

```bash
# Work on web app
cd ~/projects/webapp
ait switch
# → Node-Dev profile (green)

# Switch to API service
cd ~/projects/api
ait switch
# → Python-Dev profile (blue)

# Deploy to production
cd ~/production/live-site
ait switch
# → Production profile (RED!) 🚨
```

### R Package Development

```bash
# Navigate to R package
cd ~/r-packages/mypackage

# Check context
ait detect
# Shows: 📦 r-package → R-Dev profile

# Add R dev permissions
ait claude approvals add r-dev

# Apply context
ait switch
```

---

## Short Aliases

All commands support the `ait` shortalias:

```bash
ait --version              # = aiterm --version
ait doctor                 # = aiterm doctor
ait detect                 # = aiterm detect
ait switch                 # = aiterm switch
ait claude settings        # = aiterm claude settings
ait claude approvals list  # = aiterm claude approvals list
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | General error (missing file, invalid input) |
| 2    | Command failed (operation couldn't complete) |

---

## Environment Variables

**aiterm** respects these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `TERM_PROGRAM` | Terminal detection | `iTerm.app` |
| `SHELL` | Shell detection | `/bin/zsh` |
| `CLAUDECODE` | Claude Code detection | `1` |

---

## Configuration Commands

### `aiterm config path`

Show configuration file paths.

```bash
# Show config directory only
ait config path

# Show all paths with existence status
ait config path --all
```

**Output (`--all`):**
```
Configuration Paths
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Path Type   ┃ Location                             ┃ Exists ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Config Home │ /Users/dt/.config/aiterm             │ yes    │
│ Config File │ /Users/dt/.config/aiterm/config.toml │ yes    │
│ Profiles    │ /Users/dt/.config/aiterm/profiles    │ no     │
│ Themes      │ /Users/dt/.config/aiterm/themes      │ no     │
│ Cache       │ /Users/dt/.config/aiterm/cache       │ no     │
└─────────────┴──────────────────────────────────────┴────────┘

Using default: ~/.config/aiterm
```

---

### `aiterm config show`

Display current configuration settings.

```bash
ait config show
```

---

### `aiterm config init`

Initialize configuration directory and create default config file.

```bash
ait config init          # Create if not exists
ait config init --force  # Overwrite existing
```

Creates `~/.config/aiterm/config.toml` with default settings.

---

### `aiterm config edit`

Open configuration file in your default editor.

```bash
ait config edit
```

Uses `$EDITOR` environment variable (defaults to `nano`).

---

## Configuration Files

| File | Purpose |
|------|---------|
| `~/.config/aiterm/config.toml` | aiterm main configuration |
| `~/.config/aiterm/profiles/` | Terminal profiles |
| `~/.config/aiterm/themes/` | Custom themes |
| `~/.claude/settings.json` | Claude Code settings |
| `~/.claude/hooks/` | Claude Code hooks |

**Environment Variable Override:**
```bash
# Override config location
export AITERM_CONFIG_HOME="/custom/path"
```

---

## Next Steps

- **Workflows:** [Common use cases](../guide/workflows.md)
- **Claude Integration:** [Detailed integration guide](../guide/claude-integration.md)
- **Troubleshooting:** [Common issues and solutions](troubleshooting.md)
