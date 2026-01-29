# aiterm

> **TL;DR** (30 seconds)
> - **What:** Terminal optimizer CLI that auto-configures iTerm2/Ghostty for AI development
> - **Why:** Save 15+ minutes per day with auto-context detection and smart profile switching
> - **How:** `curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash`
> - **Next:** Run `ait detect` to see your current context, then `ait switch` to apply settings

**Terminal optimizer CLI for AI-assisted development with Claude Code and Gemini CLI.**

[![PyPI](https://img.shields.io/pypi/v/aiterm-dev)](https://pypi.org/project/aiterm-dev/)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/Data-Wise/aiterm/actions/workflows/test.yml/badge.svg)](https://github.com/Data-Wise/aiterm/actions/workflows/test.yml)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)
[![License](https://img.shields.io/github/license/Data-Wise/aiterm)](https://github.com/Data-Wise/aiterm/blob/main/LICENSE)

---

## What It Does

**aiterm** optimizes your terminal for AI-assisted development by:

- 🎯 **Smart Context Detection** - Automatically detects project type (Python, R, Node.js, etc.)
- 🎨 **Auto Profile Switching** - Changes iTerm2 colors based on context (production = red!)
- ⚙️ **Claude Code Integration** - Manages settings, hooks, and auto-approvals
- 🔧 **OpenCode Integration** - Configure agents, MCP servers, and models
- 📊 **Status Bar** - Shows project info, git status, and session metrics
- 🚀 **Fast Setup** - Install in < 5 minutes with `uv` or Homebrew

---

## Quick Example

```bash
# Quick Install (auto-detects best method)
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash

# Or with Homebrew (macOS)
brew install data-wise/tap/aiterm

# Or with UV (fastest)
uv tool install aiterm-dev

# Check health
aiterm doctor

# Detect current project
aiterm detect

# View Claude Code settings
aiterm claude settings

# List auto-approval presets
aiterm claude approvals presets
```

---

## Context Detection

**aiterm** automatically detects 8 project types:

| Context | Icon | Profile | When Detected |
|---------|------|---------|---------------|
| Production | 🚨 | Production | `/production/`, `/prod/` paths |
| AI Session | 🤖 | AI-Session | `/claude-sessions/`, `/gemini-sessions/` |
| R Package | 📦 | R-Dev | `DESCRIPTION` file present |
| Python | 🐍 | Python-Dev | `pyproject.toml` present |
| Node.js | 📦 | Node-Dev | `package.json` present |
| Quarto | 📊 | R-Dev | `_quarto.yml` present |
| Emacs | 🔧 | Dev-Tools | `.spacemacs` file |
| Dev Tools | 🛠️ | Dev-Tools | `.git` + `scripts/` |

---

## Features

### Context Management
- Detect project type from file markers and path patterns
- Apply context to terminal (profile, title, git status)
- Short aliases: `ait detect`, `ait switch`

### Claude Code Integration
- **StatusLine** - Powerlevel10k-style 2-line status display (NEW!)
  - Project context, git info, session metrics
  - 3 color themes, 31 config options
  - Background agents, time tracking, productivity indicators
  - Install: `ait statusline install`
- View and backup `~/.claude/settings.json`
- Manage auto-approval permissions with 8 presets:
  - `safe-reads` - Read-only operations
  - `git-ops` - Git commands (status, diff, log)
  - `github-cli` - GitHub CLI operations
  - `python-dev` - Python tools (pytest, pip, uv)
  - `node-dev` - Node.js tools (npm, npx, bun)
  - `r-dev` - R development tools
  - `web-tools` - Web search and fetch
  - `minimal` - Basic shell commands only

### Terminal Integration (iTerm2)
- Profile switching via escape sequences
- Tab title with project name and git branch
- Status bar variables for custom displays

---

## Installation

### macOS (Recommended)

```bash
brew install data-wise/tap/aiterm
```

**Why Homebrew?**
- ✅ One-line installation
- ✅ Automatic dependency management
- ✅ Simple updates (`brew upgrade`)
- ✅ No Python setup needed

### Cross-Platform (UV)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install aiterm
uv tool install git+https://github.com/Data-Wise/aiterm
```

**Why UV?** 10-100x faster than pip, compatible with everything, no lock file confusion.

### Install with pipx

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install aiterm
pipx install git+https://github.com/Data-Wise/aiterm
```

### Verify Installation

```bash
aiterm --version
aiterm doctor
```

---

## Quick Start

### 1. Basic Usage

```bash
# Check installation
aiterm doctor

# Detect current directory
aiterm detect

# Switch to another project
cd ~/my-python-project
aiterm switch    # Applies context to iTerm2
```

### 2. Claude Code Integration

```bash
# View current settings
aiterm claude settings

# Backup settings
aiterm claude backup

# View auto-approvals
aiterm claude approvals list

# Add safe preset
aiterm claude approvals add safe-reads

# Add development presets
aiterm claude approvals add python-dev
aiterm claude approvals add git-ops
```

### 3. Use Short Alias

```bash
ait detect      # Same as: aiterm detect
ait switch      # Same as: aiterm switch
ait doctor      # Same as: aiterm doctor
```

---

## Use Cases

### For Claude Code Users

```bash
# Set up safe auto-approvals
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev

# Verify configuration
ait claude settings
```

### For Multi-Project Developers

```bash
# Navigate between projects with auto-context
cd ~/projects/my-webapp/
ait switch    # → Node-Dev profile (green)

cd ~/projects/api-service/
ait switch    # → Python-Dev profile (blue)

cd ~/production/live-site/
ait switch    # → Production profile (RED!) 🚨
```

### For R Package Developers

```bash
cd ~/r-packages/mypackage/
ait detect    # Shows: 📦 r-package → R-Dev profile

# Context includes:
# - Package name from DESCRIPTION
# - Git branch and dirty status
# - Profile colors optimized for R work
```

---

## What's New

### v0.7.0 (Next)

- **🎨 Claude Code StatusLine** - Powerlevel10k-style 2-line status display
  - Install: `ait statusline install`
  - 3 color themes (purple-charcoal, cool-blues, forest-greens)
  - 31 configuration options via `ait statusline config`
  - Project icons, Python env detection, enhanced git info
  - Background agents counter, time tracking, productivity indicators
  - 70 comprehensive tests
- **Documentation Site** - Comprehensive StatusLine guide with examples

```bash
# StatusLine Setup (v0.7.0)
ait statusline install             # Install into Claude Code
ait statusline test                # Test with mock data
ait statusline config              # Interactive config menu
ait statusline theme set cool-blues # Switch themes
```

### v0.6.3

- **Feature Workflow Enhancements** - Complete PR automation
  - `ait feature promote` - Create PRs to dev branch
  - `ait feature release` - Create release PRs (dev→main)
  - `ait recipes` - Quick alias for workflow templates
- **Interactive Tutorial System** - Learn aiterm step-by-step
  - `ait learn start` - Begin interactive tutorials
  - `ait learn list` - Browse available tutorials
  - `ait learn progress` - Track your learning
  - Three skill levels: Getting Started, Intermediate, Advanced
  - 75 comprehensive tests, GIF demos
- **PyPI Trusted Publishing** - Automated releases via GitHub Actions

### v0.5.0

- **Release Automation** - Complete CLI for streamlined publishing
  - `ait release check` - Pre-release validation
  - `ait release full` - Complete workflow: check → tag → pypi → homebrew

### v0.4.0

- **Workflow Automation** - Session-aware workflow runner
  - `ait workflows run test` - Run project tests
  - `ait workflows run lint+test+build` - Chain workflows with `+`
- **Craft Plugin Management** - `ait craft status/list/install/sync`

### v0.3.x Highlights

- **Ghostty Terminal** - Full iTerm2 parity with 14 themes
- **Session Coordination** - Hook-based tracking & conflict detection
- **IDE Integrations** - VS Code, Cursor, Zed, Positron, Windsurf

## Roadmap

### v0.8.0 (Next)

- **Ghostty Enhancements** - Theme switching, badge integration
- **Workflow Templates** - Reusable workflow patterns
- **StatusLine Enhancements** - Node.js version, R package health, MCP servers

### v1.0.0

- **Plugin System** - Extend with custom contexts
- **Web UI** - Visual configuration tool
- **Custom StatusLine Segments** - User-defined information display

---

## Links

- **Documentation:** [https://data-wise.github.io/aiterm](https://data-wise.github.io/aiterm)
- **Repository:** [https://github.com/Data-Wise/aiterm](https://github.com/Data-Wise/aiterm)
- **Issues:** [https://github.com/Data-Wise/aiterm/issues](https://github.com/Data-Wise/aiterm/issues)

---

## Why aiterm?

**Built for ADHD-friendly workflows:**

- ⚡ Fast commands with clear output
- 🎯 Single-purpose commands (no analysis paralysis)
- 🎨 Visual context cues (production = red!)
- 📝 Comprehensive docs with examples
- 🧪 Well-tested (685 tests, 85% coverage)

**Perfect for:**

- Claude Code power users
- Multi-project developers
- R package maintainers
- Production/staging separation
- ADHD-friendly workflows

---

## License

MIT - see [LICENSE](https://github.com/Data-Wise/aiterm/blob/main/LICENSE) for details.
