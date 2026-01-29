# CLAUDE.md

This file provides guidance to Claude Code when working with the aiterm project.

## Project Overview

**aiterm** - AI Terminal Optimizer CLI for Claude Code, OpenCode, and Gemini CLI workflows.

**What it does:**

- Optimizes terminal setup (iTerm2, Ghostty, etc.) for AI coding workflows
- Manages terminal profiles, context detection, and visual customization
- Integrates with Claude Code CLI (hooks, commands, auto-approvals, MCP servers)
- Session-aware workflow automation with chaining support
- Craft plugin management for Claude Code
- OpenCode and Gemini CLI configuration management

**Tech Stack:**

- **Language:** Python 3.10+
- **CLI Framework:** Typer + Rich
- **Testing:** pytest (849 tests, all passing)
- **Distribution:** Homebrew, PyPI, curl installer
- **CI/CD:** GitHub Actions (6 Python versions, strict mode)

---

## Current Version: v0.7.2 (Jan 17, 2026)

### v0.7.2 Features - Ghostty 1.2.x Integration & StatusBar Fix

**Ghostty 1.2.x Support:**

- ✅ New config keys: `macos-titlebar-style`, `background-image`, `mouse-scroll-multiplier`
- ✅ Native progress bars (OSC 9;4) for Ghostty users
- ✅ Full profile support for 1.2.x settings
- ✅ CLI display of all new configuration options

**StatusBar Critical Fix:**

- ✅ Fixed `NameError: name 'sys' is not defined` in Claude Code status bar
- ✅ Added missing `import sys` to segments.py
- ✅ Verified with 166 passing tests

**Quick Commands:**

```bash
# View Ghostty 1.2.x settings
ait ghostty config

# Set new Tahoe titlebar style
ait ghostty set macos-titlebar-style tabs

# Set background image
ait ghostty set background-image ~/Pictures/bg.jpg

# Test status bar rendering
echo '{"workspace":{...}}' | ait statusline render
```

**Files:**

- [src/aiterm/terminal/ghostty.py](src/aiterm/terminal/ghostty.py) - 1.2.x config support
- [src/aiterm/cli/ghostty.py](src/aiterm/cli/ghostty.py) - Updated CLI
- [src/aiterm/statusline/segments.py](src/aiterm/statusline/segments.py) - OSC 9;4 + sys import fix

**Statistics:**

| Metric | Value |
|--------|-------|
| Files Changed | 4 |
| Lines Added | 150 |
| New Config Keys | 3 |
| Tests Passing | 166 |

---

### v0.7.1 Features - StatusLine Spacing Presets

**Spacing Presets System:**

- ✅ Configurable gap spacing between left/right segments (v0.7.1)
- ✅ 3 presets: minimal (15%), standard (20%), spacious (30%)
- ✅ Dynamic gap calculation based on terminal width
- ✅ Optional centered separator (`…`) in gap
- ✅ Smart constraints (min/max limits)
- ✅ CLI command: `ait statusline config spacing <preset>`
- ✅ 12 comprehensive tests (all passing)
- ✅ Complete documentation with visual examples

**Visual Example:**

```text
Terminal: 120 columns, standard preset (20%)

Before (filled):
╭─ ░▒▓ 📁 aiterm  main ▓▒░                               ░▒▓ (wt) feature ▓▒░

After (spacing preset):
╭─ ░▒▓ 📁 aiterm  main ▓▒░            …           ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^^^^^^^^^^^^^^
                        24 chars (20% of 120)
```

**Quick Commands:**

```bash
# Apply spacing presets
ait statusline config spacing minimal    # Tight (15%, 5-20 chars)
ait statusline config spacing standard   # Balanced (20%, 10-40 chars)
ait statusline config spacing spacious   # Wide (30%, 15-60 chars)

# Manual overrides
ait statusline config set spacing.min_gap 12
ait statusline config set spacing.max_gap 50
ait statusline config set spacing.show_separator false

# Preview changes
ait statusline test
```

**Files:**

- [docs/guides/statusline-spacing.md](docs/guides/statusline-spacing.md) - Complete user guide (416 lines)
- [docs/reference/commands.md](docs/reference/commands.md) - Command reference
- [docs/specs/SPEC-statusline-spacing-2026-01-02.md](docs/specs/SPEC-statusline-spacing-2026-01-02.md) - Implementation spec

**Statistics:**

| Metric | Value |
|--------|-------|
| Files Changed | 6 |
| Lines Added | 1,303 |
| New Tests | 12 |
| Total Tests | 173 (all passing) |
| Documentation | 541 lines |

---

### v0.7.0 Features - Minimal StatusLine Redesign

**StatusLine Redesign:**

- ✅ Minimal preset command (`ait statusline config preset minimal`)
- ✅ Right-side Powerlevel10k worktree display (adaptive)
- ✅ Smart branch truncation (preserves start/end, not just prefix)
- ✅ Removed bloat: session duration, current time, lines changed, battery %, cost data
- ✅ Adaptive layout (different for main vs worktree branches)
- ✅ Terminal width auto-detection with proper ANSI code stripping
- ✅ 24 new comprehensive tests (all passing)
- ✅ Complete documentation guide

**Visual Example:**

```text
Main:     ╭─ ░▒▓ 📁 aiterm  main ▓▒░
          ╰─ Sonnet 4.5

Worktree: ╭─ ░▒▓ 📁 aiterm  feature-auth ▓▒░          ░▒▓ (wt) feature-auth ▓▒░
          ╰─ Sonnet 4.5
```

**Files:**

- [docs/guides/statusline-minimal.md](docs/guides/statusline-minimal.md) - Complete user guide
- [BRAINSTORM-statusline-redesign-2026-01-01.md](BRAINSTORM-statusline-redesign-2026-01-01.md) - Design brainstorm
- [docs/specs/SPEC-statusline-redesign-2026-01-01.md](docs/specs/SPEC-statusline-redesign-2026-01-01.md) - Implementation spec

### v0.6.3 Features - StatusLine & Feature Workflow

**StatusLine System (Legacy):**

- Comprehensive Claude Code statusLine customization
- 32 configuration options across 6 categories (display, git, project, usage, theme, time)
- Configurable separator spacing (minimal/standard/relaxed)
- Git branch truncation, ahead/behind indicators, dirty status
- 57 comprehensive tests

**Feature Workflow Enhancements:**

- `ait feature promote` - Create PR to dev branch
- `ait feature release` - Create PR from dev to main
- `ait recipes` - Alias for workflow templates
- Automated PR creation with gh CLI
- Draft PR support, custom titles/bodies, browser opening

**CI/Testing Improvements:**

- Documentation strict mode (catches orphaned pages, broken links)
- All 849 tests passing across Python 3.10-3.13 (Ubuntu + macOS)
- ANSI code handling in CLI tests
- StatusLine config test coverage

### v0.6.0 Features - Interactive Tutorial System

**Tutorial System** (`ait learn`):

- `ait learn` - List all tutorials
- `ait learn start <level>` - Begin a tutorial
- `ait learn start <level> -s N` - Resume from step
- `ait learn info <level>` - Show tutorial details

**3 Progressive Levels (31 total steps):**

| Level | Steps | Duration | Topics |
|-------|-------|----------|--------|
| Getting Started | 7 | ~10 min | Install, detect, switch, help |
| Intermediate | 11 | ~20 min | Claude Code, workflows, sessions |
| Advanced | 13 | ~35 min | Release, craft, MCP, IDE |

**Visual Documentation:**

- 9 GIF demos (VHS-generated)
- 6 Mermaid diagrams
- 4 tutorial pages
- REFCARD-TUTORIALS.md

**Statistics:** 75 tutorial tests, 849 total tests

### Previous Releases

| Version | Date | Highlights |
|---------|------|------------|
| v0.6.0 | Dec 30 | Interactive tutorials (31 steps, 3 levels) |
| v0.5.0 | Dec 30 | Release automation (7 commands) |
| v0.4.0 | Dec 30 | Workflows + Craft integration |
| v0.3.15 | Dec 30 | Ghostty full iTerm2 parity |
| v0.3.9 | Dec 29 | Ghostty terminal support |
| v0.3.6 | Dec 27 | curl installer |

---

## Quick Reference

### Installation

```bash
# Quick Install (auto-detects best method)
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash

# Homebrew (macOS)
brew install data-wise/tap/aiterm

# PyPI
pip install aiterm-dev
```

### Essential Commands

```bash
# Core
ait doctor                       # Health check
ait detect                       # Show project context
ait switch                       # Apply context to terminal

# Tutorials (v0.6.0)
ait learn                        # List all tutorials
ait learn start getting-started  # Begin tutorial
ait learn info intermediate      # Show tutorial details

# Release Management (v0.5.0)
ait release check                # Validate release readiness
ait release full 0.6.0           # Full release workflow

# Workflows (v0.4.0)
ait workflows status             # Session + workflow status
ait workflows run test           # Run test workflow
ait workflows run lint+test      # Chain workflows
ait workflows custom list        # List custom workflows

# Craft (v0.4.0)
ait craft status                 # Plugin status
ait craft list                   # List commands/skills
ait craft sync                   # Sync with project

# Claude Code
ait claude settings              # View settings
ait claude approvals list        # Show auto-approvals
ait sessions live                # Active sessions

# Terminals
ait terminals detect             # Detect current terminal
ait ghostty theme                # List/set Ghostty themes
ait ghostty status               # Ghostty config status

# Feature Workflow (v0.6.3)
ait feature status               # Branch pipeline view
ait feature start auth -w        # Start feature with worktree
ait feature promote              # Create PR to dev
ait feature release              # Create PR from dev to main
ait feature cleanup              # Clean merged branches
ait recipes                      # Workflow templates (alias)

# StatusLine (v0.6.3)
ait statusline render            # Display statusLine output
ait statusline config list       # Show all config options
ait statusline config get KEY    # Get config value
ait statusline config set KEY VAL # Set config value
```

### Key Paths

| Path | Purpose |
|------|---------|
| `~/.config/aiterm/` | Config directory (XDG) |
| `~/.config/aiterm/workflows/` | Custom YAML workflows |
| `~/.claude/plugins/craft` | Craft plugin location |
| `~/.claude/sessions/` | Session tracking data |

---

## Development

### Running Tests

```bash
pytest                           # All tests
pytest tests/test_workflows.py   # Workflow tests only
pytest tests/test_craft.py       # Craft tests only
pytest -x                        # Stop on first failure
```

### Project Structure

```
src/aiterm/
├── cli/                 # CLI commands (Typer)
│   ├── main.py          # Entry point
│   ├── craft.py         # Craft plugin management
│   ├── workflows.py     # Workflow runner
│   ├── ghostty.py       # Ghostty terminal
│   ├── feature.py       # Feature workflow
│   └── sessions.py      # Session coordination
├── terminal/            # Terminal backends
│   ├── iterm2.py
│   └── ghostty.py
├── context/             # Context detection
├── statusline/          # StatusLine system (v0.6.3)
│   ├── config.py        # Configuration management
│   ├── render.py        # Output rendering
│   └── project.py       # Project health checks
├── claude/              # Claude Code integration
└── opencode/            # OpenCode integration
```

### Adding a New Command

1. Create file in `src/aiterm/cli/`
2. Define Typer app with commands
3. Register in `main.py`
4. Add tests in `tests/`
5. Update `docs/reference/commands.md`

### Commit Convention

```
type(scope): subject

feat(workflows): add workflow chaining
fix(ghostty): handle missing config
docs: update commands reference
```

---

## Integration Points

### Craft Plugin (v1.8.0+)

- Location: `~/.claude/plugins/craft`
- Source: `~/projects/dev-tools/claude-plugins/craft`
- 60 commands, 16 skills, 8 agents

### Session Coordination

- Hooks: `~/.claude/hooks/session-register.sh`, `session-cleanup.sh`
- Data: `~/.claude/sessions/active/`, `~/.claude/sessions/history/`
- Auto-registers sessions on Claude Code start

### Terminal Support

| Terminal | Features |
|----------|----------|
| iTerm2 | Profiles, badges, status bar |
| Ghostty | Themes, keybinds, sessions |
| Kitty | Tab titles |
| WezTerm | Lua config |

---

## CI/CD

Automated workflows in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | Push/PR | Run pytest (849 tests) ✅ All passing |
| `docs.yml` | Push to main | Deploy docs (strict mode enabled) ✅ |
| `pypi-release.yml` | Release published | Build & publish to PyPI |
| `homebrew-release.yml` | Release published | Update Homebrew formula |
| `demos.yml` | Manual | Generate VHS demo GIFs |

### Release Flow

```
git tag v0.6.0 && git push origin v0.6.0
gh release create v0.6.0 --title "v0.6.0" --notes "..."
  ↓ triggers
├─ pypi-release.yml → PyPI publish (trusted publisher)
├─ homebrew-release.yml → PR to homebrew-tap
└─ docs.yml → GitHub Pages deploy
```

### Manual Triggers

```bash
# Trigger Homebrew update
gh workflow run homebrew-release.yml -f version=0.6.0
```

### PyPI Publishing

**Option 1: Local CLI (working)**

```bash
ait release pypi  # Uses uv build + twine
```

**Option 2: GitHub Actions (requires PyPI setup)**

1. Go to <https://pypi.org/manage/account/publishing/>
2. Add trusted publisher for `Data-Wise/aiterm`
3. Then: `gh workflow run pypi-release.yml -f version=X.Y.Z`

---

## Links

- **Repo:** <https://github.com/Data-Wise/aiterm>
- **Docs:** <https://Data-Wise.github.io/aiterm/>
- **PyPI:** <https://pypi.org/project/aiterm-dev/>
- **Homebrew:** `brew install data-wise/tap/aiterm`
