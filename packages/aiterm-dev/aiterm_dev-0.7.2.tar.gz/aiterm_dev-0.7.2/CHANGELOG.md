# Changelog

All notable changes to this project will be documented in this file.

---

## [0.7.2] - 2026-01-17 - Ghostty 1.2.x Integration & StatusBar Fix 🎨

**Tag:** v0.7.2
**PyPI:** <https://pypi.org/project/aiterm-dev/0.7.2/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### 🎉 New Features: Ghostty 1.2.x Support

Full integration with Ghostty 1.2.x features (latest: 1.2.3).

**New Configuration Keys:**

- `macos-titlebar-style` - Support for Tahoe titlebar styles (native/tabs)
- `background-image` - Terminal background image support
- `mouse-scroll-multiplier` - Precision scroll control

**Native Progress Bars (OSC 9;4):**

- **Lines Changed**: Visualizes code changes as success/error progress bar
- **Usage Tracking**: Shows API usage with warning thresholds
- Automatically enabled when Ghostty is detected

**CLI Enhancements:**

- `ait ghostty config` now displays all 1.2.x settings
- Full profile support for new configuration keys
- Updated `ait ghostty set` for new options

### 🐛 Critical Fix: StatusBar sys Import

**Issue:** `NameError: name 'sys' is not defined` in Claude Code status bar

**Root Cause:** Missing `import sys` in `segments.py` after OSC 9;4 implementation

**Resolution:**

- Added missing import statement
- Verified status bar rendering with test cases
- All 166 tests passing

### 📊 Statistics

| Metric | Value |
|--------|-------|
| Files Changed | 4 |
| Lines Added | 150 |
| New Config Keys | 3 |
| Tests Updated | 3 |
| Total Tests | 166 (all passing) |

### 🔧 Technical Details

**Files Modified:**

- `src/aiterm/terminal/ghostty.py`: Added 1.2.x config support
- `src/aiterm/cli/ghostty.py`: Updated CLI display
- `src/aiterm/statusline/segments.py`: Added sys import + OSC 9;4
- `tests/test_ghostty.py`: Added 1.2.x field tests

**Ghostty Features Researched:**

- Command Palette (Ctrl+Shift+P)
- Graphical Progress Bars (OSC 9;4)
- macOS Tahoe support (Liquid Glass style)
- Background image support
- Mouse scroll multiplier for precision devices

---

## [0.7.1] - 2026-01-02 - StatusLine Spacing Presets ✨

**Tag:** v0.7.1
**PyPI:** <https://pypi.org/project/aiterm-dev/0.7.1/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### 🎉 New Feature: Spacing Presets

Configurable spacing system for gap between left and right Powerlevel10k segments.

**New Command:**

```bash
ait statusline config spacing <preset>
```

**Spacing Presets:**

| Preset | Gap Size | Range | Use Case |
|--------|----------|-------|----------|
| **minimal** | 15% of terminal width | 5-20 chars | Compact, information-dense |
| **standard** | 20% of terminal width | 10-40 chars | Balanced (default) |
| **spacious** | 30% of terminal width | 15-60 chars | Wide, maximum clarity |

**Features:**

- Dynamic gap calculation based on terminal width
- Optional centered separator (`…` character) in dim gray
- Min/max gap constraints (5-60 chars range)
- Graceful degradation for narrow terminals
- 4 new config settings (spacing.mode, min_gap, max_gap, show_separator)

**Technical:**

- SPACING_PRESETS constant with preset parameters
- `_calculate_gap()` method for dynamic sizing
- `_render_gap()` method with separator support
- Updated `_align_line()` to use new spacing system

**Testing:**

- 12 comprehensive tests (all passing)
- Gap calculation, rendering, and alignment tests
- Config override and constraint tests
- Visual testing at different terminal widths

**Files Changed:**

- `src/aiterm/statusline/config.py`: Added 4 spacing settings
- `src/aiterm/statusline/renderer.py`: Added SPACING_PRESETS and 3 methods (+200 lines)
- `src/aiterm/cli/statusline.py`: Added spacing command (+129 lines)
- `tests/test_statusline_renderer.py`: Added TestSpacingFeatures (+199 lines)

**Documentation:**

- `docs/specs/SPEC-statusline-spacing-2026-01-02.md`: Implementation spec
- `IMPLEMENTATION-SUMMARY-spacing-2026-01-02.md`: Feature summary

### 📊 Statistics

| Metric | Value |
|--------|-------|
| Files Changed | 6 |
| Lines Added | 1,303 |
| Tests Added | 12 |
| Total Tests | 173 (all passing) |

---

## [0.7.0] - 2026-01-01 - StatusLine Minimal Redesign 🎨

**Tag:** v0.7.0
**PyPI:** <https://pypi.org/project/aiterm-dev/0.7.0/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### 🎉 Major Redesign: Minimal StatusLine

Complete StatusLine redesign focusing on clarity and reduced visual clutter.

**Key Changes:**

- **Minimal Preset (Default):** Removed bloat - session duration, current time, lines changed, battery %, cost data
- **Right-Side Worktree Display:** Adaptive layout showing worktree context on the right
- **Smart Branch Truncation:** Preserves both start and end of branch names (not just prefix)
- **Terminal Width Auto-Detection:** Responsive layout with proper ANSI code stripping

**Visual Example:**

```
Main:     ╭─ ░▒▓ 📁 aiterm  main ▓▒░
          ╰─ Sonnet 4.5

Worktree: ╭─ ░▒▓ 📁 aiterm  feature-auth ▓▒░          ░▒▓ (wt) feature-auth ▓▒░
          ╰─ Sonnet 4.5
```

**New Command:**

```bash
ait statusline config preset minimal    # Apply minimal preset
ait statusline config preset default    # Restore defaults
```

**Features:**

- Adaptive layout: Different display for main vs worktree branches
- Worktree marker moved to right side: `░▒▓ (wt) feature-name ▓▒░`
- Main branch shows worktree count or nothing
- Smart branch truncation: `feature/...auth-system` (preserves both ends)
- Terminal width detection with fallback to 120 chars

**Technical:**

- Updated `_build_line1()` for right-side segments
- Added `_build_right_segments()` for worktree context
- Added `_render_right_segment()` for P10k reversed style
- Added `_align_line()` for dynamic padding
- Added `_strip_ansi_length()` for accurate width calculation
- Updated `_truncate_branch()` to preserve start/end

**Testing:**

- 24 new comprehensive tests (all passing)
- Worktree display tests
- Branch truncation tests
- Layout adaptation tests

**Bug Fixes:**

- Fixed NoneType error when Claude Code sends `null` values in JSON
- Changed defensive pattern from `data.get('key', {})` to `data.get('key') or {}`
- Fixed 5 test failures due to v0.7.0 minimal preset defaults

**Files Changed:**

- `src/aiterm/statusline/renderer.py`: Major refactoring for right-side display
- `src/aiterm/statusline/segments.py`: Worktree refactoring, smart truncation
- `tests/test_statusline_renderer.py`: Updated test fixtures
- `tests/test_statusline_worktree.py`: 24 new worktree tests

**Documentation:**

- `docs/guides/statusline-minimal.md`: Complete user guide
- `docs/specs/SPEC-statusline-redesign-2026-01-01.md`: Implementation spec
- `STATUSLINE-FIX-SUMMARY.md`: Bug fixes and feature summary
- `BRAINSTORM-statusline-redesign-2026-01-01.md`: Design brainstorm

### 📊 Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Default metrics shown | 8 | 3 | -63% clutter |
| Character count (main) | ~80 | ~60 | -25% |
| Tests | 156 | 161 | +5 tests |
| Test pass rate | 97% (5 failing) | 100% | All passing ✅ |
| Critical bugs | 1 (NoneType) | 0 | Fixed ✅ |

---

## [0.6.3] - 2025-12-31 - StatusLine System & CI Improvements 🎨

**Tag:** v0.6.3
**PyPI:** <https://pypi.org/project/aiterm-dev/0.6.3/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### 🎉 Major Features

#### StatusLine System

Complete Claude Code statusLine customization system with 32 configuration options.

**Commands:**

| Command | Description |
|---------|-------------|
| `ait statusline render` | Display statusLine output |
| `ait statusline config list` | Show all 32 config options |
| `ait statusline config get KEY` | Get specific config value |
| `ait statusline config set KEY VALUE` | Update config value |
| `ait statusline config reset [KEY]` | Reset to defaults |

**Features:**

- **6 Configuration Categories:** display, git, project, usage, theme, time
- **Worktree Display:** 🌳N count when multiple worktrees, `(wt)` marker in non-main
- **Configurable Spacing:** minimal (1 space), standard (2 spaces), relaxed (3 spaces)
- **Git Integration:** Branch name, dirty status, ahead/behind indicators, worktree count
- **Session Tracking:** Duration, current time, cost tracking
- **Themes:** 3 built-in themes (cool-blues, forest-greens, purple-charcoal)

#### Feature Workflow Enhancements

| Command | Description |
|---------|-------------|
| `ait feature promote` | Create PR to dev branch |
| `ait feature release` | Create PR from dev to main |
| `ait recipes` | Alias for workflow templates |

**Features:**

- Automated PR creation using gh CLI
- Draft PR support (`--draft` flag)
- Custom titles and bodies
- Browser opening on creation (`--web` flag)
- Default titles from branch names

### ✅ CI/CD Improvements

- **Documentation Strict Mode:** Catches orphaned pages and broken links automatically
- **Enhanced Test Coverage:** 849 tests passing across 6 Python versions (3.10-3.13)
- **ANSI Handling:** Fixed CLI test assertions to work in CI environments
- **Cross-Platform:** Tests run on both Ubuntu and macOS

### 📊 Statistics

| Category | Count |
|----------|-------|
| New CLI Commands | 5 (statusline) |
| Config Options | 32 |
| Tests Added | 164 (statusline + feature) |
| Total Tests | 849 (all passing) |
| Python Versions | 6 (3.10-3.13, Ubuntu + macOS) |

### 🐛 Bug Fixes

- Fixed test count assertions for statusline config changes
- Fixed ANSI color code handling in feature help tests
- Fixed orphaned documentation pages in navigation
- Disabled usage tracking (Anthropic API not programmatically accessible)

### 📝 Documentation

- Added comprehensive StatusLine guide
- Added StatusLine specs (config UX, integration)
- Updated CLAUDE.md for v0.6.3
- Added StatusLine section to REFCARD.md
- Documentation strict mode enabled in CI

---

## [0.6.0] - 2025-12-30 - Interactive Tutorial System 📚

**Tag:** v0.6.0
**PyPI:** <https://pypi.org/project/aiterm-dev/0.6.0/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### 🎉 Major Features

Complete interactive tutorial system for onboarding new users.

#### Tutorial System (`ait learn`)

Progressive learning with 3 levels (31 total steps):

| Level | Steps | Duration | Topics |
|-------|-------|----------|--------|
| Getting Started | 7 | ~10 min | Install, detect, switch, help |
| Intermediate | 11 | ~20 min | Claude Code, workflows, sessions |
| Advanced | 13 | ~35 min | Release, craft, MCP, IDE |

#### Commands

| Command | Description |
|---------|-------------|
| `ait learn` | List all available tutorials |
| `ait learn start <level>` | Begin a tutorial |
| `ait learn start <level> -s N` | Resume from step N |
| `ait learn info <level>` | Show tutorial details |

#### Visual Documentation

- **9 GIF demos** for key commands (VHS-generated)
- **6 Mermaid diagrams** for learning paths and workflows
- **4 tutorial pages** in docs site
- **1 quick reference card** (REFCARD-TUTORIALS.md)

### 📊 Statistics

| Category | Count |
|----------|-------|
| New CLI Commands | 4 |
| Tutorial Steps | 31 |
| GIF Demos | 9 |
| Mermaid Diagrams | 6 |
| New Tests | 75 (tutorial module) |
| Total Tests | 685 |

### Craft Plugin Integration

- New `/craft:docs:tutorial` skill (craft v1.12.0)
- 6-phase tutorial generation workflow
- VHS tape templates for demos

### Documentation

- New `docs/tutorials/` directory with 4 pages
- Learning path diagrams in `docs/diagrams/`
- Updated mkdocs.yml navigation
- User testing checklist for validation

---

## [0.5.1] - 2025-12-30

**Tag:** v0.5.1

### Fixed

- Test suite update for PyPI verification (now uses v0.5.0)

### Documentation

- Updated docs/index.md with v0.5.0 release info
- Updated getting started guide version reference

---

## [0.5.0] - 2025-12-30 - Release Automation 🚀

**Tag:** v0.5.0
**PyPI:** <https://pypi.org/project/aiterm-dev/0.5.0/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### 🎉 Major Features

Complete release automation CLI for streamlined publishing workflow.

#### Release Management (`ait release`)

7 new commands for end-to-end release automation:

| Command | Description |
|---------|-------------|
| `ait release check` | Pre-release validation (version, tests, changelog, git) |
| `ait release status` | Show current version, latest tag, pending changes |
| `ait release pypi` | Build and publish to PyPI with uv |
| `ait release homebrew` | Update Homebrew formula with SHA256 from PyPI |
| `ait release tag` | Create annotated git tag |
| `ait release notes` | Generate release notes from conventional commits |
| `ait release full` | Complete workflow: check → tag → push → pypi → homebrew |

#### Features

- **Conventional commit parsing** - Categorizes commits by type (feat, fix, docs, etc.)
- **Automatic SHA256 fetching** - Gets hash from PyPI for Homebrew formula
- **Dry-run support** - Preview all commands without execution
- **Version detection** - Reads from pyproject.toml automatically
- **Git integration** - Creates annotated tags with release notes

### 📊 Statistics

| Category | Count |
|----------|-------|
| New CLI Commands | 7 |
| New Tests | 55 |
| Total Tests | 611 |

### Added

- `src/aiterm/cli/release.py` - Complete release management CLI (1032 lines)
- `tests/test_release.py` - Comprehensive test suite (651 lines)
- `docs/reference/commands.md` - Release Management section
- `docs/REFCARD.md` - Release commands quick reference

---

## [0.4.0] - 2025-12-30 - Workflow Automation & Craft Integration 🚀

**Tag:** v0.4.0
**PyPI:** <https://pypi.org/project/aiterm-dev/0.4.0/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### 🎉 Major Features

Three complete feature systems for workflow automation:

#### Phase 2: Craft Plugin Management (`ait craft`)

- **Craft CLI** - Manage Claude Code's craft plugin
  - `ait craft status` - Show craft plugin installation status and overview
  - `ait craft list` - List available craft commands, skills, and agents
  - `ait craft install` - Install/reinstall craft plugin via symlink
  - `ait craft update` - Update craft plugin (git pull in source)
  - `ait craft sync` - Sync craft with project context detection
  - `ait craft run <cmd>` - Show how to run craft commands in Claude Code
  - `ait craft commands [namespace]` - Show detailed craft command info
- **19 tests** for craft plugin management

#### Phase 3: Session-Aware Workflows (`ait workflows`)

- **Workflow Runner** with Claude Code session awareness
  - `ait workflows status` - Check session status and available workflows
  - `ait workflows run <name>` - Run workflow with session task updates
  - `ait workflows task <desc>` - Update current session task
- **Session task auto-update** - Workflows update session task as they progress
- **Session requirement checks** - Some workflows require active Claude Code session

#### Phase 3 Quick Wins: Advanced Workflow Features

- **13 Built-in Workflows:**
  - `test` - Run project tests (auto-detected)
  - `lint` - Run linter (ruff/eslint/lintr)
  - `format` - Auto-format code
  - `check` - Type checking (mypy/tsc)
  - `build` - Build project (wheel/bundle)
  - `docs` - Build documentation
  - `docs-serve` - Serve docs locally
  - `clean` - Clean build artifacts
  - `deploy-docs` - Deploy docs to GitHub Pages
  - `release` - Full release workflow
- **Custom YAML Workflows:**
  - Store workflows in `~/.config/aiterm/workflows/*.yaml`
  - `ait workflows custom list` - List custom workflows
  - `ait workflows custom show <name>` - Show workflow details
  - `ait workflows custom create <name>` - Create new workflow
  - `ait workflows custom delete <name>` - Delete workflow
  - Auto-discovered and merged with built-in workflows
- **Workflow Chaining:**
  - Use `+` separator: `ait workflows run lint+test+build`
  - Sequential execution with early exit on failure
  - Session task shows chain progress (e.g., "Running lint+test (2/3)")

### 📊 Statistics

| Category | Count |
|----------|-------|
| New CLI Commands | 14 (7 craft + 7 workflows) |
| New Tests | 63 (19 craft + 44 workflows) |
| Built-in Workflows | 13 |
| Custom Workflow YAML Support | ✅ |

### Added

---

## [0.3.15] - 2025-12-30 - Ghostty Full iTerm2 Parity

**Tag:** v0.3.15
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.15/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

Phase 0.8 Complete - Ghostty now has full feature parity with iTerm2!

### Added

#### Phase 0.8.1-0.8.2: Ghostty Profile & Backup Management

- **Profile Management** - Save and switch between Ghostty configurations
  - `ait ghostty profile list` - List saved profiles
  - `ait ghostty profile show <name>` - Show profile details
  - `ait ghostty profile create <name>` - Create profile from current config
  - `ait ghostty profile apply <name>` - Apply profile to config
  - `ait ghostty profile delete <name>` - Delete a profile
  - Profiles stored in `~/.config/ghostty/profiles/*.conf`
- **Config Backup** - Timestamped backups matching claude backup pattern
  - `ait ghostty backup [--suffix]` - Create timestamped backup
  - `ait ghostty restore [backup]` - Restore from backup (with pre-restore safety)
  - `ait ghostty restore` (no args) - List available backups

#### Phase 0.8.3: Ghostty Keybind Management

- **Keybind Management** - Manage Ghostty keyboard shortcuts
  - `ait ghostty keybind list` - List current keybinds from config
  - `ait ghostty keybind add <trigger> <action>` - Add a keybind
  - `ait ghostty keybind remove <trigger>` - Remove a keybind
  - `ait ghostty keybind preset <name>` - Apply keybind preset
  - **Presets:** vim, emacs, tmux, macos (for common workflows)
  - Supports prefixes: `global:`, `unconsumed:`, `all:`

#### Phase 0.8.4: Ghostty Session Management

- **Session Management** - Save and restore terminal layouts
  - `ait ghostty session list` - List saved sessions
  - `ait ghostty session show <name>` - Show session details
  - `ait ghostty session save <name>` - Save current directory as session
  - `ait ghostty session restore <name>` - Restore a session
  - `ait ghostty session delete <name>` - Delete a session
  - `ait ghostty session split [direction]` - Create terminal split
  - Sessions stored in `~/.config/ghostty/sessions/*.json`
  - Layout types: single, split-h, split-v, grid

### Tests

- 96 Ghostty tests total (34 new for keybind/session management)

---

## [0.3.13] - 2025-12-30 - Feature Workflow & Ghost Aliases

**Tag:** v0.3.13
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.13/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

#### Phase 0.7: Quick Wins

- **Ghost Aliases** - Shortcuts for Ghostty terminal management
  - `ait ghost` - Show Ghostty status (alias for `ait ghostty status`)
  - `ait ghost theme [name]` - List or apply Ghostty theme
  - `ait ghost config [-e]` - Show or edit Ghostty config
  - `ait ghost font [name] [--size N]` - Show or set Ghostty font
- **Terminal-Aware Switch** - `ait switch` now auto-detects terminal
  - Supports iTerm2, Ghostty, Kitty, Alacritty, WezTerm, Apple Terminal
  - Shows terminal type in context detection output
  - Uses appropriate backend for each terminal

#### Phase 1b: Feature Workflow Commands

- **Feature Status** - `ait feature status`
  - Rich pipeline visualization (main → dev → features)
  - Shows worktree locations for each feature
  - Displays merge status and commit counts
- **Feature List** - `ait feature list [--all]`
  - Detailed feature branch listing with status
  - Shows worktree paths and commit counts
  - Use `--all` to include merged branches
- **Feature Start** - `ait feature start <name> [-w] [--no-install]`
  - Creates feature branch from dev (or custom base)
  - Optional worktree creation with `-w`/`--worktree`
  - Auto-installs dependencies (Python/Node/R detection)
- **Feature Cleanup** - `ait feature cleanup [--dry-run] [--force]`
  - Interactive cleanup of merged feature branches
  - Removes associated worktrees
  - Use `--dry-run` to preview deletions

### Tests

- 17 new tests for feature CLI (all passing)

---

## [0.3.12] - 2025-12-30 - Version Display Fix

**Tag:** v0.3.12
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.12/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Fixed

- **Version Display** - Fixed mismatch between `--version` output and package version
  - `__version__` in `__init__.py` now syncs with `pyproject.toml`
- **CI Workflow** - Fixed checkout ref handling for `workflow_dispatch` triggers
  - Ensures correct version is built when manually triggered

---

## [0.3.11] - 2025-12-30 - XDG Config Support

**Tag:** v0.3.11
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.11/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

- **XDG-Compliant Configuration** - Config paths now follow XDG Base Directory Specification
  - Default config directory: `~/.config/aiterm/`
  - Config file: `~/.config/aiterm/config.toml`
  - Profiles directory: `~/.config/aiterm/profiles/`
  - Themes directory: `~/.config/aiterm/themes/`
- **AITERM_CONFIG_HOME Environment Variable** - Override config location
  - Priority: `AITERM_CONFIG_HOME` > `XDG_CONFIG_HOME/aiterm` > `~/.config/aiterm`
  - Pattern follows `ZDOTDIR` from ZSH
- **Config CLI Commands** - New `ait config` command group
  - `config path` - Show config directory path
  - `config path --all` - Show all paths with existence status
  - `config show` - Display current configuration
  - `config init` - Create default config.toml
  - `config edit` - Open config in $EDITOR

### Documentation

- `docs/proposals/XDG-CONFIG-MIGRATION.md` - Full migration proposal
- Updated `docs/reference/configuration.md` - XDG paths and environment variables
- Updated `docs/reference/commands.md` - Config command reference

---

## [0.3.10] - 2025-12-29 - flow-cli Integration

**Tag:** v0.3.10
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.10/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

- **flow-cli Integration** - New `tm` dispatcher for flow-cli
  - `tm title <text>` - Set tab/window title (shell-native, instant)
  - `tm profile <name>` - Switch iTerm2 profile (shell-native)
  - `tm var <key> <val>` - Set iTerm2 status bar variable
  - `tm which` - Show detected terminal
  - `tm ghost` - Delegate to `ait ghostty` commands
  - `tm switch` - Delegate to `ait switch`
  - `tm detect` - Delegate to `ait detect`
  - `tm doctor` - Delegate to `ait doctor`
- **Symlink-based Sync** - Automatic integration with flow-cli
  - `flow-integration/aiterm.zsh` - Main dispatcher file
  - `flow-integration/install-symlink.sh` - Setup script
  - Version compatibility checks with graceful fallbacks
- **Homebrew Integration** - Auto-install flow-cli symlink
  - `post_install` hook detects flow-cli and creates symlink
  - Caveats show manual installation instructions

### Removed

- **Legacy ZSH** - Removed `zsh/iterm2-integration.zsh` (186 lines)
  - Replaced by `flow-integration/aiterm.zsh`
  - All functionality preserved in new dispatcher

### Documentation

- `docs/design/TERMINAL-DISPATCHER-DESIGN.md` - Naming research, escape sequences, sync mechanism
- `docs/proposals/AITERM-IN-FLOW-CLI.md` - Integration architecture proposal
- `docs/proposals/ZSH-DELEGATION-FLOW-CLI.md` - Delegation strategy proposal

---

## [0.3.9] - 2025-12-29 - Ghostty Terminal Support

**Tag:** v0.3.9
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.9/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

- **Ghostty Terminal Support** - Full integration with Ghostty terminal emulator
  - Auto-detection when running in Ghostty (`TERM_PROGRAM=ghostty`)
  - Version detection (channel, build config)
  - Config parsing and modification (`~/.config/ghostty/config`)
  - 14 built-in themes (catppuccin, dracula, nord, solarized, tokyo-night, etc.)
  - Window title setting via OSC escape sequences
  - Context-aware title updates
- **Ghostty CLI Commands** - New `ait ghostty` command group
  - `ghostty status` - Show current Ghostty configuration
  - `ghostty config` - Display config file location and contents
  - `ghostty theme [name]` - List or set themes
  - `ghostty font [name] [size]` - Get or set font configuration
  - `ghostty set <key> <value>` - Set any config value
- **Terminals Subcommand** - New `ait terminals` command group
  - `terminals list` - List all supported terminals with installation status
  - `terminals detect` - Detect current terminal with version info
  - `terminals features <terminal>` - Show terminal-specific features
  - `terminals config <terminal>` - Show config file location
  - `terminals compare` - Side-by-side feature comparison
  - `terminals title <text>` - Set tab/window title
  - `terminals profile <name>` - Switch terminal profile (iTerm2)
- **Comprehensive Test Suite** - 25 new Ghostty tests
  - Subprocess handling (version detection, timeouts, errors)
  - OSC escape sequence tests (title setting)
  - Context-to-title mapping tests
  - Config parsing edge cases (invalid values, malformed lines)
  - Config path detection tests
  - Theme list immutability tests

### Changed

- **CI Pipelines** - Migrated from pip to uv for faster builds
  - `publish.yml`: Faster PyPI publishing
  - `docs.yml`: Faster documentation builds
- **Test Suite** - Expanded from 399 to 424 tests (+25)
- **Terminal Detection** - Now supports 6 terminals (iTerm2, Ghostty, Kitty, Alacritty, WezTerm, Terminal.app)

### Documentation

- New `docs/guide/terminals.md` - Multi-terminal support guide
- Updated commands reference with Ghostty CLI
- Added IDEAS.md with v0.4.0 planning and flow-cli integration brainstorm

---

## [0.3.7] - 2025-12-27 - Craft v1.6.0 Integration

**Tag:** v0.3.7
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.7/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Documentation

- Updated CLAUDE.md with Craft v1.6.0-dev integration
  - 58 commands available for workflow recipes (was 53)
  - 15 skills for intelligent task routing (was 13)
  - New docs workflow commands: update, feature, done, site
- Updated .STATUS with session accomplishments
- Updated V0.4.0-PLAN.md with current version references

### Integration

- **Craft plugin v1.6.0-dev** compatibility
  - New `/craft:docs:update` - Smart universal documentation updater
  - New `/craft:docs:feature` - Comprehensive feature documentation
  - New `/craft:docs:done` - End-of-session doc updates
  - New `/craft:docs:site` - Website-focused updates with deploy

---

## [0.3.6] - 2025-12-27 - curl Installation Script

**Tag:** v0.3.6
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.6/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

- **install.sh:** Universal curl-based installer
  - Auto-detects best method: uv → pipx → brew → pip
  - `INSTALL_METHOD` env var for method override
  - `AITERM_VERSION` env var for version pinning
  - Colored output with verification

```bash
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash
```

### Documentation

- Updated README with curl install as primary option
- Updated docs/GETTING-STARTED.md with Quick Install tab
- Updated docs/index.md with dynamic PyPI badge
- Updated docs/REFCARD.md with v0.3.6 and new commands
- Updated docs/reference/commands.md with hello/goodbye/info
- Added architecture/RFORGE-UNIVERSAL-BACKEND.md to nav
- Deployed updated documentation to GitHub Pages

---

## [0.3.5] - 2025-12-27 - Diagnostic Commands & Enhanced Version

**Tag:** v0.3.5
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.5/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

- **hello command:** `ait hello` - Simple diagnostic greeting
  - `ait hello --name <name>` for personalized greeting
- **goodbye command:** `ait goodbye` - Farewell message
  - `ait goodbye --name <name>` for personalized farewell
- **info command:** `ait info` - Comprehensive system diagnostics
  - Shows: aiterm, Python, platform, environment, dependencies, tools, paths
  - `ait info --json` for scripted output
- **18 new CLI tests** for diagnostic commands

### Enhanced

- **--version flag:** Now shows Python version, platform info, and install path
  - Rich formatted panel output

### Developer Notes

- Added via Craft Orchestrator v2.1 dogfooding tests
- Validated: live orchestration, 4-agent stress test, session persistence

---

## [0.3.4] - 2025-12-27 - OpenCode MCP Server Tools

**Tag:** v0.3.4
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.4/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

- **MCP server test command:** `ait opencode servers test <name>` - Test individual server startup
- **MCP server health check:** `ait opencode servers health` - Check all enabled servers at once
- **MCP server add/remove:** `ait opencode servers add/remove` - Manage server configurations
- **Server templates:** Pre-configured setups for common MCP servers
- **MCP server tests:** 23 new tests for server validation, connectivity, and health checks
- **Integration test marker:** `pytest -m integration` to run actual server tests

### Changed

- **OpenCode schema v1.0.203 compatibility:**
  - Use singular keys: `agent` (not `agents`), `command` (not `commands`)
  - Commands require `template` field (not `command`)
  - MCP servers use `environment` key (not `env`)
  - Tools are boolean enabled/disabled (not permission objects)
  - Keybinds are not supported (show informational message)

### Usage

```bash
# Test individual server
ait opencode servers test filesystem

# Check all enabled servers
ait opencode servers health

# Add a new server from template
ait opencode servers add brave-search --template

# Add custom server
ait opencode servers add myserver --command "npx -y my-mcp-server"
```

---

## [0.3.3] - 2025-12-26 - CLI Test Enhancements

**Tag:** v0.3.3
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.3/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`

### Added

- **JUnit XML output** for CLI tests (`--junit results.xml`)
- **Performance benchmarking** for CLI tests (`--benchmark`)
- **GitHub Actions integration** with test result upload
- Performance summary showing fast/medium/slow test distribution

### Changed

- Improved interactive test runner with Ghostty AppleScript support
- Simplified interactive test flow (run → show → judge)
- Enhanced terminal detection for Claude Code context

### Usage

```bash
# Run with benchmarks
bash tests/cli/automated-tests.sh --benchmark

# Generate JUnit XML for CI
bash tests/cli/automated-tests.sh --junit test-results.xml
```

---

## [0.3.2] - 2025-12-26 - Bug Fixes

**Tag:** v0.3.2

### Fixed

- Session prune command stability improvements

---

## [0.3.1] - 2025-12-26 - Session Prune Command

**Tag:** v0.3.1

### Added

- `ait sessions prune` command to clean up stale session files

---

## [0.3.0] - 2025-12-26 - IDE Integrations & Session Coordination 🎉

**Status:** Released
**Tag:** v0.3.0
**PyPI:** <https://pypi.org/project/aiterm-dev/0.3.0/>
**Homebrew:** `brew upgrade data-wise/tap/aiterm`
**Documentation:** <https://Data-Wise.github.io/aiterm/>

### 🎉 Major Features

#### Phase 4.1: IDE Integrations (`ait ide`)

Multi-IDE support for AI-assisted development workflows.

- **Supported IDEs:** VS Code, Positron, Zed, Cursor, Windsurf
- **Commands:** `list`, `status`, `extensions`, `configure`, `terminal-profile`, `sync-theme`, `open`, `compare`
- **Features:**
  - AI development extension recommendations per IDE
  - Terminal profile generation for aiterm integration
  - Theme synchronization across IDEs
  - Configuration management (load/save settings)
  - IDE installation detection

#### Phase 4.2: Session Coordination (`ait sessions`)

Automatic tracking and coordination of parallel Claude Code sessions.

- **Hook-based auto-registration:** Sessions auto-register when Claude Code starts
- **Conflict detection:** Warns when same project has multiple active sessions
- **Session archival:** Auto-archives sessions to `~/.claude/sessions/history/` by date
- **Task tracking:** Set/view current task description for active sessions
- **New hooks:**
  - `~/.claude/hooks/session-register.sh` (SessionStart)
  - `~/.claude/hooks/session-cleanup.sh` (Stop)
- **New CLI commands:** `live`, `conflicts`, `history`, `task`, `current`

### 📊 Statistics

| Category | Count |
|----------|-------|
| New CLI Commands | 13 (8 IDE + 5 sessions) |
| New Tests | 47 (32 IDE + 15 sessions) |
| New Documentation | 4 guides/refcards |
| IDEs Supported | 5 |

### Installation

```bash
# macOS (Homebrew)
brew upgrade data-wise/tap/aiterm

# PyPI
pip install --upgrade aiterm-dev

# uv
uv tool upgrade aiterm-dev
```

---

## [0.2.1] - 2025-12-26 - PyPI & Distribution Release 🚀

- **Phase 2.5: Advanced Claude Features** ✅ COMPLETE (9 new CLI modules)
  - **Subagent Management** (`ait agents`): Create, list, validate Claude Code subagents
    - Templates: research, coding, review, quick, statistical
    - Commands: list, templates, create, show, remove, validate, test
  - **Memory System** (`ait memory`): Manage CLAUDE.md hierarchy
    - Commands: hierarchy, validate, create, show, stats, rules
    - Tracks global/project/rules precedence
  - **Output Styles** (`ait styles`): Manage Claude response styles
    - Presets: default, concise, detailed, academic, teaching, code-review
    - Commands: list, show, set, create, remove, preview
  - **Plugin Management** (`ait plugins`): Bundle commands/agents/skills/hooks
    - Commands: list, show, create, validate, remove, package, import

- **Phase 3: Multi-Tool Integration** ✅ COMPLETE
  - **Gemini CLI Integration** (`ait gemini`): Full Gemini CLI management
    - Commands: status, settings, init, models, set, mcp, compare, sync-mcp
    - Model support: gemini-2.0-flash, gemini-1.5-pro, etc.
  - **Status Bar Builder** (`ait statusbar`): Build custom status bars
    - Templates: minimal, powerlevel10k, developer, stats
    - Commands: status, templates, preview, set, list, create, test, components, disable

- **Phase 4: Advanced Features** ✅ COMPLETE
  - **Multi-Terminal Support** (`ait terminals`): Unified terminal management
    - Backends: iTerm2, Kitty, Alacritty, WezTerm, Ghostty
    - Commands: detect, list, features, config, title, profile, compare
    - Auto-detection via environment variables
  - **Workflow Templates** (`ait workflows`): Pre-configured workflow profiles
    - Templates: r-development, python-development, node-development, research, teaching, mcp-development, documentation, adhd-friendly
    - Commands: list, show, apply, create, remove, detect, export, import
  - **Session Management** (`ait sessions`): Track development sessions
    - Commands: start, end, status, list, show, stats, delete, export, cleanup
    - Auto-tracks: duration, commits, workflow, tags

- **93 New Tests** for Phase 2.5-4 modules
  - `tests/test_phase2_5_cli.py`: 25 tests for agents/memory/styles/plugins
  - `tests/test_phase3_4_cli.py`: 34 tests for gemini/statusbar/terminals/workflows/sessions
  - `tests/test_cli_integration.py`: 34 tests for full CLI integration
  - All tests include self-diagnostic validation

- **OpenCode Phase 3: Full Configuration System** ✅ COMPLETE
  - `research` agent: Academic research & manuscript writing (Opus 4.5, 7 tools + web search)
  - Keyboard shortcuts: `ctrl+r` (r-dev), `ctrl+q` (quick), `ctrl+s` (research)
  - Custom commands: rpkg-check, rpkg-document, rpkg-test, sync, status
  - Tool permissions: auto (bash/read/glob/grep), ask (write/edit)
  - Time MCP server enabled for timezone & deadline tracking
  - New CLI commands: `keybinds`, `commands`, `tools`, `summary`
  - 28 Phase 3 tests (`test_opencode_phase3.py`)
  - 131 total OpenCode tests (103 passing)

- **OpenCode CLI Integration** (`ait opencode`)
  - `ait opencode config` - View current OpenCode configuration
  - `ait opencode validate` - Validate configuration file
  - `ait opencode backup` - Create timestamped backup
  - `ait opencode models` - List recommended models
  - `ait opencode set-model` - Set primary or small model
  - `ait opencode agents list|add|remove` - Manage custom agents
  - `ait opencode servers list|enable|disable` - Manage MCP servers
  - `ait opencode instructions` - Show CLAUDE.md sync status
  - `ait opencode keybinds` - List keyboard shortcuts (NEW)
  - `ait opencode commands` - List custom commands (NEW)
  - `ait opencode tools` - List tool permissions (NEW)
  - `ait opencode summary` - Complete configuration summary (NEW)

- **OpenCode Phase 2: Custom Agents & GitHub Integration**
  - `r-dev` agent: R package development specialist (Sonnet 4.5, 6 tools)
  - `quick` agent: Fast responses for simple questions (Haiku 4.5, 3 tools)
  - GitHub MCP server enabled with automatic GITHUB_TOKEN from gh CLI
  - CLAUDE.md sync: OpenCode reads same instructions as Claude Code
  - AGENTS.md symlink: `~/.config/opencode/AGENTS.md` → `~/.claude/CLAUDE.md`
  - Instructions config: Reads `CLAUDE.md` and `.claude/rules/*.md`
  - 14-test validation suite for agent configuration

- **OpenCode Test Suite**
  - `tests/test_opencode_config.py` - Core config tests (55 tests)
  - `tests/test_opencode_cli.py` - CLI command tests (20 tests)
  - `tests/test_opencode_agents.py` - Agent validation (14 tests)
  - `tests/test_opencode_phase3.py` - Phase 3 features (28 tests)

- **CI/CD Pipeline**
  - Added GitHub Actions test workflow (`test.yml`)
  - Test matrix: Python 3.10, 3.11, 3.12 on Ubuntu and macOS
  - Coverage reporting with pytest-cov
  - Automatic PR checks

### Changed

- **Project Organization**
  - Moved planning docs to `archive/planning/`
  - Moved phase docs to `archive/phases/`
  - Moved session notes to `archive/sessions/`
  - Moved setup guides to `archive/guides/`
  - Moved technical docs to `docs/reference/`
  - Root directory now contains only README, CHANGELOG, and CLAUDE.md

### Fixed

- **Test Suite**
  - Fixed `test_hooks_list` to accept empty hooks state
  - Fixed `test_all_commands_have_help` for Typer CLI help format

---

## [0.2.1] - 2025-12-26 - PyPI & Distribution Release 🚀

**Status:** Published to PyPI & Homebrew
**Tag:** v0.2.1
**PyPI:** <https://pypi.org/project/aiterm-dev/0.2.1/>
**Homebrew:** `brew install data-wise/tap/aiterm`
**Documentation:** <https://Data-Wise.github.io/aiterm/>

### 🎉 Distribution Milestone

aiterm is now available on PyPI and Homebrew!

#### Installation Options

```bash
# macOS (Homebrew)
brew install data-wise/tap/aiterm

# Cross-platform (PyPI)
pip install aiterm-dev

# Using uv (fastest)
uv tool install aiterm-dev

# Using pipx
pipx install aiterm-dev
```

### Added

- **PyPI Publishing**
  - Published as `aiterm-dev` (name `aiterm` was unavailable)
  - GitHub Actions workflow for trusted publishing (OIDC)
  - Automated releases on new tags
  - Cross-platform installation via pip/uv/pipx

- **Documentation Standards (flow-cli based)**
  - `docs/REFCARD.md` - One-page ASCII quick reference
  - `docs/QUICK-START.md` - 30-second setup guide
  - `docs/GETTING-STARTED.md` - 10-minute hands-on tutorial
  - `docs/guide/shell-completion.md` - Zsh/Bash/Fish completion setup

- **Domain-Specific Reference Cards**
  - `REFCARD-CLAUDE.md` - Claude Code commands
  - `REFCARD-MCP.md` - MCP server management
  - `REFCARD-HOOKS.md` - Hook management
  - `REFCARD-CONTEXT.md` - Context detection
  - `REFCARD-OPENCODE.md` - OpenCode integration

- **CLI Improvements**
  - Added epilog examples to 19 commands
  - Rich formatted help with usage examples

### Fixed

- **Homebrew Formula**
  - Fixed transitive dependency installation
  - Added all deps explicitly (click, shellingham, typing_extensions, mdurl, markdown-it-py, pygments, wcwidth, prompt_toolkit)
  - Both `aiterm` and `ait` commands now work correctly

### Changed

- Version sync across pyproject.toml, **init**.py, and .STATUS
- Updated README with simplified installation section
- Updated mkdocs.yml navigation with all new pages

---

## [0.2.0] - 2025-12-24 - PHASE 3A COMPLETE 🎉

**Status:** Production-Ready Stable Release
**Tag:** v0.2.0
**Release URL:** <https://github.com/Data-Wise/aiterm/releases/tag/v0.2.0>
**Documentation:** <https://Data-Wise.github.io/aiterm/>

### 🎉 Major Features

Four complete feature systems delivered in Phase 3A:

#### 1. Hook Management System (580 lines)

- Commands: `aiterm claude hooks list/install/validate/test`
- Interactive hook templates (5 hooks included)
- Validation and testing framework
- Beautiful Rich output

#### 2. Command Library System (600 lines)

- Commands: `aiterm claude commands list/browse/install/validate`
- Category-based organization (git, docs, workflow, etc.)
- Command template library (5 commands included)
- Installation wizard

#### 3. MCP Server Integration (513 lines + 597 lines docs)

- Commands: `aiterm mcp list/test/test-all/validate/info`
- Server health monitoring and testing
- Automatic sensitive data masking
- Comprehensive MCP-INTEGRATION.md documentation

#### 4. Documentation Helpers (715 lines + 647 lines docs)

- Commands: `aiterm docs stats/validate-links/test-examples/validate-all`
- Link validation (internal + external)
- Code syntax checking (Python + Bash)
- Found 35 real issues in aiterm documentation
- Comprehensive DOCS-HELPERS.md documentation

### 📊 Statistics

- **Production Code:** 2,673 lines
- **Documentation:** 2,585 lines (27 pages)
- **Integration Tests:** 29 tests (100% passing)
- **Templates:** 10 templates (5 hooks, 5 commands)
- **Development Time:** 23.5 hours (27% ahead of schedule)

### ✅ Quality Metrics

- Test Pass Rate: 100% (29/29 integration tests)
- Documentation Links: 100% validated (204 links)
- Build Warnings: 0 (strict mode enabled)
- Version Consistency: 100% across all files

<!-- Auto-generated 2025-12-24 by update-changelog.sh -->

### Changed

- release: Phase 3A complete - v0.2.0-dev preparation (1d9d2e9)

### Documentation

- update .STATUS - Phase 3A Week 2 Days 3-4 complete ([810b732](https://github.com/Data-Wise/aiterm/commit/810b732))
- Phase 3A Week 2 Days 3-4 completion summary ([b4ddd8e](https://github.com/Data-Wise/aiterm/commit/b4ddd8e))
- auto-update CHANGELOG with documentation helpers ([4c9947e](https://github.com/Data-Wise/aiterm/commit/4c9947e))

<!-- Auto-generated 2025-12-24 by update-changelog.sh -->

### Added

- **docs**: implement documentation validation system ([5ec60ca](https://github.com/Data-Wise/aiterm/commit/5ec60ca))

### Documentation

- update .STATUS - Phase 3A Week 2 complete ([eb6f4db](https://github.com/Data-Wise/aiterm/commit/eb6f4db))
- Phase 3A Week 2 completion summary ([688de8f](https://github.com/Data-Wise/aiterm/commit/688de8f))
- auto-update CHANGELOG with MCP integration ([9205896](https://github.com/Data-Wise/aiterm/commit/9205896))

<!-- Auto-generated 2025-12-24 by update-changelog.sh -->

### Added

- **mcp**: implement MCP server management system ([bb3e51c](https://github.com/Data-Wise/aiterm/commit/bb3e51c))

### Documentation

- **mcp**: add comprehensive MCP integration guide ([2f168c5](https://github.com/Data-Wise/aiterm/commit/2f168c5))
- auto-update CHANGELOG with command library ([0c42bb9](https://github.com/Data-Wise/aiterm/commit/0c42bb9))

<!-- Auto-generated 2025-12-24 by update-changelog.sh -->

### Added

- **commands**: implement command template library (Phase 3A Days 3-4) ([f32be78](https://github.com/Data-Wise/aiterm/commit/f32be78))

### Documentation

- auto-update CHANGELOG with hook implementation ([33fba90](https://github.com/Data-Wise/aiterm/commit/33fba90))

<!-- Auto-generated 2025-12-24 by update-changelog.sh -->

### Added

- **hooks**: add 4 production-ready hook templates ([8469e1b](https://github.com/Data-Wise/aiterm/commit/8469e1b))
- **hooks**: implement hook management system (Phase 3A Day 1) ([e42fa76](https://github.com/Data-Wise/aiterm/commit/e42fa76))

### Documentation

- auto-update CHANGELOG with Phase 3 commits ([17568e8](https://github.com/Data-Wise/aiterm/commit/17568e8))

<!-- Auto-generated 2025-12-24 by update-changelog.sh -->

### Added

- **docs**: implement Phase 2 auto-update system ([6289379](https://github.com/Data-Wise/aiterm/commit/6289379))

### Documentation

- Phase 3 quick start guide ([da3acf3](https://github.com/Data-Wise/aiterm/commit/da3acf3))
- Phase 3 planning - core features vs AI documentation ([25eeeb8](https://github.com/Data-Wise/aiterm/commit/25eeeb8))

<!-- Auto-generated 2025-12-24 by update-changelog.sh -->

### Documentation

- enhance Phase 0 documentation with diagrams and fixes ([68d92eb](https://github.com/Data-Wise/aiterm/commit/68d92eb))
- fix mkdocs navigation and broken links ([0ad3dd7](https://github.com/Data-Wise/aiterm/commit/0ad3dd7))
- comprehensive Phase 2 test results ([b1b7744](https://github.com/Data-Wise/aiterm/commit/b1b7744))
- auto-update CHANGELOG with Phase 2 commits ([4e13734](https://github.com/Data-Wise/aiterm/commit/4e13734))

<!-- Auto-generated 2025-12-22 by update-changelog.sh -->

### Added

- **docs**: implement mkdocs navigation updater - Phase 2 Session 2 ([2b3eadd](https://github.com/Data-Wise/aiterm/commit/2b3eadd))
- **docs**: implement Phase 2 auto-updates - CHANGELOG generator ([dfadd0e](https://github.com/Data-Wise/aiterm/commit/dfadd0e))

### Documentation

- update .STATUS - Phase 2 100% complete ([79a1931](https://github.com/Data-Wise/aiterm/commit/79a1931))
- Phase 2 MVP complete - documentation auto-updates ([1bf4807](https://github.com/Data-Wise/aiterm/commit/1bf4807))
- session completion - Phase 2 auto-updates progress ([a487fd2](https://github.com/Data-Wise/aiterm/commit/a487fd2))

<!-- Auto-generated 2025-12-21 by update-changelog.sh -->

### Added

- **workflow**: implement Phase 1 documentation detection ([1324721](https://github.com/Data-Wise/aiterm/commit/1324721))

### Documentation

- session completion - Phase 1 documentation automation ([8f2750b](https://github.com/Data-Wise/aiterm/commit/8f2750b))

### Added

- 🍺 **Homebrew Distribution** - macOS users can now install via `brew install data-wise/tap/aiterm`
  - Added formula to private Homebrew tap
  - Automatic dependency management
  - Simple updates with `brew upgrade aiterm`
  - Primary installation method for macOS

### Workflow & Documentation

- 🔧 **Created `/workflow:done` Command** - Critical missing ADHD-friendly session completion
  - Captures session progress from git changes (commits, diffs, file changes)
  - Updates .STATUS file automatically
  - Generates commit messages based on work completed
  - 474 lines, comprehensive implementation
  - Location: `~/.claude/commands/workflow/done.md`
  - Integrates with `/workflow:recap` for context restoration
  - ADHD-optimized with 30-second fast path

### Changed

- Updated README with Homebrew as recommended macOS installation method
- Added installation methods comparison table
- Updated website documentation (docs/getting-started/*.md, docs/index.md)
- Enhanced CLAUDE.md with Homebrew installation methods

### Documentation

- Created `HOMEBREW-DISTRIBUTION-PLAN.md` - comprehensive Homebrew roadmap
- Created `HOMEBREW-QUICKSTART.md` - quick implementation guide
- Updated `IDEAS.md` with:
  - Phase 2.6: Workflow Commands & Documentation Automation
  - Phase 2.7: Distribution & Installation (Homebrew complete)
  - Phase 3: Public Homebrew release plan
  - Phase 4.5: Official Homebrew Core submission plan
- Updated `ROADMAP.md` with Phase 2.6 (Workflow & Documentation Automation)
  - 3-phase enhancement plan for `/workflow:done`
  - Detection methods for CLAUDE.md, mkdocs.yml staleness
  - Auto-update strategies for documentation ecosystem
- Deployed updated documentation to GitHub Pages

---

## [0.1.0] - 2024-12-18 - FIRST PRODUCTION RELEASE 🎉

**First production release of aiterm!**

### 🎉 Highlights

- ✅ Production-ready CLI with 51 tests (83% coverage)
- ✅ Comprehensive documentation (2,647 lines)
- ✅ UV-optimized installation (10-100x faster than pip)
- ✅ Repository renamed to "aiterm"
- ✅ Deployed docs to GitHub Pages

### Installation

```bash
# Recommended (UV - fastest!)
uv tool install git+https://github.com/Data-Wise/aiterm

# Alternative (pipx)
pipx install git+https://github.com/Data-Wise/aiterm
```

**Documentation:** <https://data-wise.github.io/aiterm/>

### What's New in v0.1.0

#### Core Features

- 🎯 Smart context detection (8 project types)
- 🎨 Auto profile switching for iTerm2
- ⚙️ Claude Code integration
- 📦 8 auto-approval presets
- 🧪 Well-tested (51 tests, 83% coverage)

#### Documentation (NEW!)

- Complete installation guide (UV, pipx, dev)
- CLI reference with all commands
- Claude Code integration guide (8 presets explained)
- Real-world workflows guide (10+ examples)
- Contributing guide
- Architecture documentation

#### Performance

- UV build system (10-100x faster installation)
- < 100ms for all operations
- < 2 minutes full setup

#### Testing

- Comprehensive testing report
- Real workflow validation
- All 51 tests passing

### Repository

- Renamed from `iterm2-context-switcher` to `aiterm`
- GitHub: <https://github.com/Data-Wise/aiterm>
- Docs: <https://data-wise.github.io/aiterm/>

---

## [0.1.0-dev] - 2024-12-16 - Development Preview

### 🎉 aiterm Python CLI is Here

The first functional Python release of aiterm, migrated from zsh to a modern CLI.

### Installation

```bash
# Recommended (uv)
uv tool install git+https://github.com/Data-Wise/aiterm

# Alternative (pipx)
pipx install git+https://github.com/Data-Wise/aiterm
```

### New Features

#### Context Detection (8 types)

- **Production** 🚨 - Red theme for `*/production/*` paths
- **AI Sessions** 🤖 - Purple theme for `*/claude-sessions/*`
- **R Packages** 📦 - Blue theme (DESCRIPTION file)
- **Python** 🐍 - Green theme (pyproject.toml)
- **Node.js** 📦 - Dark theme (package.json)
- **Quarto** 📊 - Blue theme (_quarto.yml)
- **Emacs** ⚡ - Purple theme (init.el, Cask)
- **Dev-Tools** 🔧 - Amber theme (commands/, scripts/)

#### Claude Code Integration

- `ait claude settings` - View settings summary
- `ait claude backup` - Backup settings.json
- `ait claude approvals list` - Show allow/deny permissions
- `ait claude approvals presets` - List 8 ready-to-use presets
- `ait claude approvals add <preset>` - Add preset permissions

#### Auto-Approval Presets

- **safe-reads** - Safe read-only operations
- **git-ops** - Git commands (status, diff, log, branch)
- **github-cli** - GitHub CLI (gh pr, gh issue)
- **python-dev** - Python tools (pytest, pip, ruff)
- **node-dev** - Node.js tools (npm, yarn, pnpm)
- **r-dev** - R development (R, Rscript)
- **web-tools** - Web utilities (curl, wget, jq)
- **minimal** - Basic safe commands only

#### CLI Commands

```bash
ait --version          # Show version
ait doctor             # Health check
ait detect             # Detect project context
ait switch             # Apply context to terminal
ait context detect     # Full context detection
ait context apply      # Apply to iTerm2
ait profile list       # List profiles
```

### Tech Stack

- **Language:** Python 3.10+
- **CLI Framework:** Typer
- **Terminal Output:** Rich
- **Testing:** pytest (51 tests, 83% coverage)
- **Distribution:** uv/pipx/PyPI

### Files Added

- `src/aiterm/` - Main package (cli, context, terminal, claude, utils)
- `tests/` - 51 tests across 4 files
- `templates/commands/` - 6 hub commands + 5 archived
- `pyproject.toml` - Modern Python project config

### What's Next (v0.2.0)

- Hook management system
- Command template library
- MCP server integration
- Gemini CLI support

---

## [3.0.0] - 2025-12-15 - PROJECT PIVOT

### 🎉 Major Change: aiterm → **aiterm**

**Vision Evolution:**

- **Was:** zsh-based iTerm2 context switcher
- **Now:** Python CLI for optimizing terminals for AI development

**Why the pivot:**

- Expand beyond iTerm2 to support multiple terminals
- Deep integration with Claude Code and Gemini CLI
- Hook/command/MCP management systems
- Easier to extend and maintain in Python
- Better testing and distribution (PyPI)

### Project Reorganization

- **New name:** aiterm (AI Terminal optimizer)
- **New architecture:** Python CLI (Typer + Rich)
- **New scope:** Multi-tool terminal optimization
- **Target users:** DT first, then public release

### Documentation Overhaul

- ✅ `IDEAS.md` - Full feature roadmap (Phases 1-4)
- ✅ `ROADMAP.md` - Week 1 MVP plan (day-by-day)
- ✅ `ARCHITECTURE.md` - Technical design
- ✅ `CLAUDE.md` - Updated for Python project
- ✅ `README.md` - Complete rewrite
- ✅ `.STATUS` - Reset to v0.1.0-dev

### v2.5.0 Features Preserved

All existing functionality will be ported to Python:

- 8 context types (R, Python, Node, Quarto, MCP, Production, AI sessions, Dev-tools)
- Profile switching
- Tab titles with icons
- Git branch + dirty indicator
- Status bar integration
- 15 comprehensive tests

### What's Next

See `ROADMAP.md` for Week 1 MVP plan:

- Day 1-2: Python project setup
- Day 3-4: Core terminal integration
- Day 5: Claude Code settings management
- Day 6: Testing & documentation
- Day 7: Polish & dogfooding

**Target:** DT using aiterm daily by Dec 22, 2025

---

## [2.5.0] - 2025-12-15 - Final zsh-based release

### Added

- **Comprehensive test suite** - `scripts/test-context-switcher.sh`
  - Tests all 8 context detection scenarios
  - Validates profile switching and title/badge setting
  - Includes git dirty indicator testing
  - 15 test cases with full coverage
- **Statusline theme alternatives** - `statusline-alternatives/`
  - 3 color theme variants (cool-blues, forest-greens, purple-charcoal)
  - Preview and installation scripts
  - Theme comparison documentation
- **Expanded auto-approvals** - Updated `.claude/settings.local.json`
  - Added 40+ common safe commands (gh, mkdocs, find, grep, jq, etc.)
  - Reduces approval friction for routine operations

## [2.5.0] - 2025-12-15

### Added

- **Comprehensive test suite** - `scripts/test-context-switcher.sh`
  - Tests all 8 context detection scenarios
  - Validates profile switching and title/badge setting
  - Includes git dirty indicator testing
  - 15 test cases with full coverage
- **Statusline theme alternatives** - `statusline-alternatives/`
  - 3 color theme variants (cool-blues, forest-greens, purple-charcoal)
  - Preview and installation scripts
  - Theme comparison documentation
- **Expanded auto-approvals** - Updated `.claude/settings.local.json`
  - Added 40+ common safe commands (gh, mkdocs, find, grep, jq, etc.)
  - Reduces approval friction for routine operations

## [2.4.0] - 2025-12-14

### Added

- **Status Bar Integration** - Display context in iTerm2 status bar
  - `\(user.ctxIcon)` - Context icon (📦, 🐍, 🔧, etc.)
  - `\(user.ctxName)` - Project name
  - `\(user.ctxBranch)` - Git branch
  - `\(user.ctxProfile)` - Active profile name
- **Status bar documentation** - New docs/guide/status-bar.md with setup guide

### Changed

- Refactored detection to set user variables alongside profile/title
- Variables update on every directory change

## [2.3.0] - 2025-12-14

### Added

- **iTerm2 Triggers for Claude Code** - Auto-notifications in AI-Session profile
  - Bounce Dock Icon when tool approval needed (`Allow .+?`)
  - Highlight errors in red (`Error:|error:|failed`)
  - macOS notification on `/cost` command
  - Highlight success markers in green (`✓|completed`)
- **Trigger documentation** - Updated docs/guide/triggers.md with customization guide

### Changed

- AI-Session profile now includes built-in triggers
- Triggers activate automatically when using AI-Session profile

## [2.2.0] - 2025-12-14

### Added

- **Git branch in title** - Shows current branch: `📦 medfit (main)`
- **Git dirty indicator** - Shows `*` when uncommitted changes: `📦 medfit (main)*`
- **Install script** - `scripts/install-profiles.sh` for easy setup
- **Profiles in repo** - `profiles/context-switcher-profiles.json` for distribution

### Changed

- Titles now include git info for all contexts
- Long branch names truncated (>20 chars)

## [2.1.0] - 2025-12-14

### Added

- **Dynamic Profiles** - Auto-installed color themes for all project types
  - R-Dev: Blue theme 📦
  - AI-Session: Purple theme 🤖
  - Production: Red theme 🚨
  - Dev-Tools: Amber/orange theme 🔧
  - Emacs: Purple/magenta theme ⚡
  - Python-Dev: Green theme 🐍
  - Node-Dev: Dark theme 📦
- **Quarto profile switching** - Uses R-Dev profile (blue theme) 📊
- **MCP profile switching** - Uses AI-Session profile 🔌
- **Emacs profile switching** - New dedicated purple theme ⚡

### Changed

- All project types now have profile + icon switching
- Profiles auto-load via iTerm2 Dynamic Profiles

## [2.0.1] - 2025-12-14

### Added

- **Dev-Tools profile** - New profile for dev-tools projects with 🔧 icon
- **scripts/ detection** - Dev-tools now detected by `scripts/` directory (not just `commands/`)

### Fixed

- **Shared detector bypass** - Skip generic "project" type, use local detection for specifics
- **False positive fix** - Require `.git` for dev-tools detection (prevents `~/scripts` false positive)
- **iTerm2 title setting** - Profiles must use "Session Name" for escape sequences to work

### Changed

- Detection now more specific: dev-tools requires git repo + commands/ or scripts/

## [2.0.0] - 2025-12-14

### Added

- **MkDocs documentation site** - Material theme, dark/light toggle
- **GitHub Pages deployment** - Auto-deploy on push to main
- **Tab title support** - Icons + project names in tab title
- **Profile caching** - Prevents redundant profile switches
- **Hook registration guard** - Prevents duplicate hooks
- **New commands** (in ~/.claude/commands/):
  - `/mkdocs-init` - Create new documentation site
  - `/mkdocs` - Status and actions menu
  - `/mkdocs-preview` - Quick preview

### Changed

- **Removed badges** - Using tab titles instead (more reliable)
- **Simplified detection** - File-based only, no glob patterns
- **OSC 2 for titles** - Window title escape sequence
- **Emacs detection** - Now checks `Cask`, `.dir-locals.el`, `init.el`, `early-init.el`
- **Dev-tools detection** - Checks for `commands/` directory

### Fixed

- Loop issues with badge escape sequences
- OMZ title conflicts (DISABLE_AUTO_TITLE)
- Profile switch escape sequence format (`it2profile -s`)

### Documentation

- 7 documentation pages covering installation, guides, and reference
- Live site: <https://data-wise.github.io/aiterm/>

## [1.1.0] - 2025-12-13

### Added

- **Git dirty indicator** - Badges now show `✗` when repo has uncommitted changes
- **New context patterns:**
  - Python projects (`pyproject.toml`) → Python-Dev profile
  - Node.js projects (`package.json`) → Node-Dev profile
  - Quarto projects (`_quarto.yml`) → 📊 icon
  - MCP server projects → 🔌 icon
  - Emacs Lisp projects → ⚡ icon
- **Verification script** - `scripts/verify-setup.sh`

### Changed

- Refactored main function with clear priority sections
- Improved code organization with helper functions

## [1.0.0] - 2025-12-13

### Added

- Initial project structure
- Core auto-switching integration (iterm2-integration.zsh)
- Profile creation guide
- Setup guide with verification tests
- ADHD-friendly quick reference

## [Unreleased]

### Planned

- Production warning sound/bell
- Smart triggers for test results

---

**Project Status:** Complete (v2.4.0)
**Live Docs:** <https://data-wise.github.io/aiterm/>
