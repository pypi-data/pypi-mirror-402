# Common Workflows

Real-world workflows using **aiterm** with Claude Code.

---

## Daily Development Workflow

### Morning Setup

```bash
# 1. Check aiterm health
ait doctor

# 2. Navigate to project
cd ~/projects/myapp

# 3. Apply context
ait switch
# → iTerm2 profile changes to match project type
# → Tab title shows: "📦 node: myapp [main]"

# 4. Start Claude Code
claude

# Context is already set!
```

**Benefits:**
- Visual confirmation you're in the right project
- Git branch visible in tab title
- Profile colors prevent production mistakes

---

## Multi-Project Context Switching

### Scenario: Working on 3 projects simultaneously

```bash
# Terminal Tab 1: Web Frontend
cd ~/projects/webapp
ait switch
# → Node-Dev profile (green theme)
# → Tab: "📦 node: webapp [feature/new-ui]"

# Terminal Tab 2: API Backend
cd ~/projects/api
ait switch
# → Python-Dev profile (blue theme)
# → Tab: "🐍 python: api [develop]"

# Terminal Tab 3: Database Scripts
cd ~/production/migrations
ait switch
# → Production profile (RED theme) 🚨
# → Tab: "🚨 production: migrations [main]"
```

**Visual Safety:**
- Red terminal = production (be extra careful!)
- Different colors = quick visual identification
- Tab titles show branch (no mistakes!)

---

## Claude Code Setup (First Time)

### Safe Progressive Approach

```bash
# Day 1: Read-only exploration
ait claude backup
ait claude approvals add safe-reads
ait claude approvals add minimal

# Day 2-3: Add git operations
ait claude backup
ait claude approvals add git-ops

# Week 2: Add dev tools
ait claude backup
ait claude approvals add python-dev  # or node-dev, r-dev

# Week 3: Add GitHub integration
ait claude backup
ait claude approvals add github-cli

# Optional: Web research
ait claude approvals add web-tools
```

**Philosophy:**
- Start conservative
- Add permissions as needed
- Always backup before changes
- Build trust gradually

---

## R Package Development

### Complete R Package Workflow

```bash
# 1. Navigate to package
cd ~/r-packages/mypackage

# 2. Check context
ait detect
# Shows: 📦 r-package → R-Dev profile

# 3. Set up Claude approvals for R
ait claude backup
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add r-dev

# 4. Apply context
ait switch

# 5. Start Claude
claude
```

**Claude can now:**
- Run `Rscript` and `R CMD check`
- Build documentation with `roxygen2`
- Run `quarto render` for vignettes
- Execute `devtools::test()`
- Git operations for version control

**Example session:**
```
User: Run the package tests and check for errors

Claude: [Runs R CMD check automatically]
Claude: [Shows test results]
Claude: Found 2 failing tests in test-models.R
```

---

## Python Package Development

### pytest + uv Workflow

```bash
# Setup
cd ~/projects/mypkg
ait switch
ait claude approvals add python-dev

# Claude can now:
# - Run pytest automatically
# - Install deps with uv
# - Format code with black/ruff
# - Run type checks with mypy
```

**Example session:**
```
User: Add tests for the new UserAuth class

Claude: [Writes tests in tests/test_auth.py]
Claude: [Runs pytest automatically]
Test Results: 15 passed, 0 failed
```

---

## Production Deployment Safety

### Scenario: Deploying to production

```bash
# 1. Navigate to production directory
cd ~/production/live-site

# 2. Context shows RED warning
ait switch
# → Production profile (RED) 🚨
# → Tab: "🚨 production: live-site [main]"

# 3. Visual cues everywhere
# - Terminal background: red tint
# - Tab title: red warning emoji
# - Status bar: production indicator

# 4. Extra careful mode activated
# - Double-check all commands
# - Review changes before committing
# - Slow down, think first
```

**Safety features:**
- Impossible to miss you're in production
- Different muscle memory (red = danger!)
- Prevents "wrong terminal tab" disasters

---

## Multi-Language Monorepo

### Scenario: Monorepo with Python + Node + R

```bash
# Project structure:
# ~/projects/datascience/
#   ├── api/           (Python)
#   ├── frontend/      (Node.js)
#   ├── analysis/      (R)

# Root level
cd ~/projects/datascience
ait detect
# → Shows: Dev-Tools (has .git + scripts/)

# Work on API
cd ~/projects/datascience/api
ait detect
# → Shows: 🐍 python (has pyproject.toml)
ait switch

# Work on frontend
cd ~/projects/datascience/frontend
ait detect
# → Shows: 📦 node (has package.json)
ait switch

# Work on analysis
cd ~/projects/datascience/analysis
ait detect
# → Shows: 📦 r-package (has DESCRIPTION)
ait switch
```

**Setup once:**
```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev
ait claude approvals add node-dev
ait claude approvals add r-dev
```

**Benefits:**
- Auto-detects sub-project type
- Correct profile for each directory
- Claude uses right tools automatically

---

## GitHub PR Review Workflow

### Complete PR Review with aiterm

```bash
# 1. Setup GitHub CLI permissions
ait claude approvals add github-cli
ait claude approvals add git-ops

# 2. List open PRs
# (Claude can run automatically)
gh pr list

# 3. Checkout PR
gh pr checkout 123

# 4. Context updates automatically
ait switch
# → Shows new branch in tab title

# 5. Review with Claude
claude
```

**Example session:**
```
User: Review this PR for bugs and suggest improvements

Claude: [Reads changed files automatically]
Claude: [Runs tests]
Claude: [Provides review comments]

User: Looks good, approve and merge

Claude: I can approve but you should merge manually
        (gh pr merge requires explicit permission)
```

---

## Quarto Document Workflow

### Academic Paper with Quarto

```bash
# 1. Setup
cd ~/quarto/manuscripts/paper-2024
ait detect
# → Shows: 📊 quarto → R-Dev profile

# 2. Add R dev tools
ait claude approvals add r-dev

# 3. Switch context
ait switch

# 4. Work with Claude
claude
```

**Claude can:**
- Render Quarto documents
- Run R code chunks
- Generate plots
- Format tables
- Manage citations

**Example:**
```
User: Render the manuscript and show any errors

Claude: [Runs quarto render]
Claude: Found error in analysis.qmd line 45
        ggplot requires 'aes' argument
```

---

## Testing Workflow

### Automated Testing Across Projects

**Python:**
```bash
cd ~/projects/myapp
ait switch
# Claude can run: pytest -v
```

**Node.js:**
```bash
cd ~/projects/webapp
ait switch
# Claude can run: npm test, npm run test:unit
```

**R:**
```bash
cd ~/r-packages/mypkg
ait switch
# Claude can run: R CMD check, devtools::test()
```

**Key benefit:** Context detection + auto-approvals = Claude runs tests without asking!

---

## Research Literature Workflow

### With MCP + Web Tools

```bash
# Setup web search permissions
ait claude approvals add web-tools

# Research session
claude
```

**Example:**
```
User: Find recent papers on causal mediation analysis

Claude: [Searches automatically with WebSearch]
Claude: [Fetches paper abstracts with WebFetch]
Claude: [Summarizes findings]
```

**Available:**
- MCP server integration (`ait mcp list`)
- See [MCP Reference](../reference/REFCARD-MCP.md) for Zotero and other servers
- PDF reading and analysis

---

## Emergency "Wrong Directory" Detection

### Scenario: About to deploy to wrong environment

```bash
# Think you're in staging
cd ~/staging/myapp  # Actually: ~/production/myapp
# Terminal turns RED 🚨
# Tab shows: "🚨 production: myapp"

# VISUAL ALARM!
# Red background = STOP
# Check directory
pwd
# /Users/me/production/myapp

# Phew! Caught by context detection.
cd ~/staging/myapp
ait switch
# Back to safe colors
```

**This has saved production countless times!**

---

## Configuration Management Workflow (v0.3.11+)

### First-Time Setup

```bash
# 1. Initialize config directory
ait config init
# → Creates ~/.config/aiterm/config.toml

# 2. View config paths
ait config path --all
# Shows all config locations with status

# 3. Customize settings
ait config edit
# Opens config.toml in $EDITOR
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

### Custom Config Location

```bash
# Override config directory
export AITERM_CONFIG_HOME="$HOME/.aiterm"

# Check where config is loaded from
ait config path
```

---

## flow-cli Terminal Dispatcher (v0.3.10+)

### Using the `tm` Command

The `tm` dispatcher provides instant terminal control via shell-native commands:

```bash
# Set tab title (instant, no Python!)
tm title "Working on API"

# Switch iTerm2 profile
tm profile "Production"

# Set status bar variable
tm var project_name "myapp"

# Detect current terminal
tm which
# → ghostty (or iterm2)
```

### Context Switching with tm

```bash
# Navigate and switch
cd ~/projects/myapp
tm switch
# → Auto-detects context, applies profile, sets title

# Quick detect
tm detect
# Shows project type without applying
```

### Ghostty Commands via tm

```bash
# Show Ghostty config
tm ghost status

# Change theme
tm ghost theme dracula

# Set font
tm ghost font "Fira Code" 16
```

### Integration with flow-cli

`tm` integrates with other flow-cli dispatchers:

```bash
# Combined workflow
work myapp         # Start work session (flow-cli)
tm switch          # Apply terminal context
cc                 # Start Claude Code (flow-cli)
# → Everything is configured!
```

---

## Ghostty Terminal Workflow (v0.3.9+)

### Setting Up Ghostty

```bash
# 1. Check detection
ait terminals detect
# → Detected: ghostty (Version: 1.2.3)

# 2. View current config
ait ghostty status

# 3. Browse themes
ait ghostty theme
# Lists all 14 built-in themes
```

### Theme Switching

```bash
# Available themes (14 built-in)
ait ghostty theme
# catppuccin-mocha, dracula, nord, tokyo-night, gruvbox-dark, ...

# Apply a theme
ait ghostty theme dracula
# → Config updated, Ghostty auto-reloads

# Context-aware theming (future)
# Production dirs could auto-switch to red theme
```

### Font Configuration

```bash
# Check current font
ait ghostty font
# → JetBrains Mono @ 14pt

# Change font and size
ait ghostty font "Fira Code" 16
```

### Custom Settings

```bash
# Set any Ghostty config value
ait ghostty set window-padding-x 12
ait ghostty set background-opacity 0.95
ait ghostty set cursor-style underline
```

---

## Session Coordination Workflow

### Multi-Session Development

When working on multiple Claude Code sessions:

```bash
# Terminal 1: Frontend
cd ~/projects/frontend
ait switch
claude  # Session ID: abc123

# Terminal 2: Backend
cd ~/projects/backend
ait switch
claude  # Session ID: def456

# Check all active sessions
ait sessions live
```

**Output:**
```
Active Sessions
┌──────────────┬──────────────┬──────────────┬──────────┐
│ Session ID   │ Project      │ Branch       │ Duration │
├──────────────┼──────────────┼──────────────┼──────────┤
│ abc123       │ frontend     │ feature/ui   │ 45m      │
│ def456       │ backend      │ develop      │ 12m      │
└──────────────┴──────────────┴──────────────┴──────────┘
```

### Conflict Detection

```bash
# Start second session in same project
cd ~/projects/backend
ait sessions conflicts
# ⚠️ Warning: 1 other session active in this project
```

### Task Tracking

```bash
# Set what you're working on
ait sessions task "Implementing OAuth2 login"

# View current task
ait sessions current
```

### Session History

```bash
# Browse past sessions
ait sessions history
ait sessions history --date 2025-12-29

# Cleanup stale sessions
ait sessions prune
```

---

## IDE Integration Workflow

### Setting Up IDE Detection

```bash
# List supported IDEs
ait ide list

# Check current IDE
ait ide detect
```

**Supported IDEs:**
- VS Code / Cursor
- Zed
- Positron
- Windsurf
- JetBrains (IntelliJ, PyCharm, etc.)

### IDE-Specific Workflows

**VS Code + Claude Code:**
```bash
# Open in VS Code, then switch context
code ~/projects/myapp
cd ~/projects/myapp
ait switch
claude
```

**Cursor + Claude Code:**
```bash
# Cursor has built-in AI, but Claude Code works alongside
cursor ~/projects/myapp
ait switch
claude  # For complex tasks
```

---

## Tips & Tricks

### Alias for Quick Navigation

```bash
# Add to ~/.zshrc
alias cdw='cd ~/projects/webapp && ait switch'
alias cdapi='cd ~/projects/api && ait switch'
alias cdprod='cd ~/production && ait switch'
```

### Check Before Switching

```bash
# Detect before applying (safer)
ait detect ~/production/site  # Check first
ait switch ~/production/site  # Apply if correct
```

### Combine with Shell Hooks

```bash
# Auto-switch on cd (add to ~/.zshrc)
chpwd() {
  if [[ -d ".git" ]] || [[ -f "pyproject.toml" ]]; then
    ait switch &>/dev/null
  fi
}
```

---

## Next Steps

- **CLI Reference:** [All commands](../reference/commands.md)
- **Claude Integration:** [Detailed setup](claude-integration.md)
- **Context Detection:** [How detection works](context-detection.md)
