# IDEAS - Terminal Optimizer for AI Coding

**Project Vision:** CLI tool for optimizing terminals (iTerm2+) for AI-assisted development with Claude Code and Gemini CLI.

**Target Users:**
- Primary: DT (power user, R developer, statistician)
- Secondary: Public release (developers using Claude Code/Gemini)

**Tech Stack:**
- Language: Python
- CLI Framework: Typer
- Terminal API: iTerm2 Python API
- Distribution: pip installable

---

## Phase 1: MVP (Week 1) - v0.1.0 ✅ COMPLETE

**Goal:** Working CLI that improves on current aiterm
**Status:** 95% complete - awaiting PR merge (2025-12-16)

### Core Features

#### 1. Setup & Diagnostics ✅
- [x] ✅ `aiterm init` - Interactive setup wizard (placeholder)
- [x] ✅ `aiterm doctor` - Health check (terminal, shell, Python, version)
- [x] ✅ `aiterm --version` - Show version info

#### 2. Terminal Optimization ✅
- [x] ✅ Migrated iterm2-integration.zsh → Python
- [x] ✅ Profile management commands
  - `aiterm profile list` - List available profiles
- [x] ✅ Context detection (8 types)
  - `aiterm detect` / `aiterm context detect`
  - `aiterm switch` / `aiterm context apply`
  - Production 🚨, AI-Session 🤖, R-Pkg 📦, Python 🐍, Node 📦, Quarto 📊, Emacs ⚡, Dev-Tools 🔧

#### 3. Basic Claude Code Integration ✅
- [x] ✅ Settings file management
  - `aiterm claude settings` - Show settings
  - `aiterm claude backup` - Timestamped backup
- [x] ✅ Auto-approval presets (8 presets)
  - `aiterm claude approvals add <preset>` - Add preset
  - `aiterm claude approvals list` - Show permissions
  - `aiterm claude approvals presets` - List all presets
  - Presets: safe-reads, git-ops, github-cli, python-dev, node-dev, r-dev, web-tools, minimal

#### 4. Testing ✅
- [x] ✅ Port existing test suite → pytest
- [x] ✅ Add CLI command tests (test_cli.py)
- [x] ✅ Context detection tests (test_context.py)
- [x] ✅ iTerm2 tests (test_iterm2.py)
- [x] ✅ Claude settings tests (test_claude_settings.py)
- [x] ✅ **Result:** 51 tests, 83% coverage

---

## Phase 2: Enhanced Claude Integration (v0.2.0)

**Goal:** Deep Claude Code customization
**Timeline:** 2 weeks post v0.1.0 release
**Priorities:** Hook management > MCP integration > StatusLine builder

### NEW KNOWLEDGE: 9 Hook Types Available!
- PreToolUse (block/approve tools before execution)
- PermissionRequest (auto-approve/deny dialogs)
- PostToolUse (actions after tool completion)
- UserPromptSubmit (add context to prompts)
- Notification (custom alerts)
- Stop/SubagentStop (control when Claude stops)
- PreCompact (before context compaction)
- SessionStart (initialize sessions)
- SessionEnd (cleanup and logging)

### Features

#### 1. Hook Management
- [ ] `aiterm claude hooks list` - Show available hooks and their configs
- [ ] `aiterm claude hooks install <name>` - Install from template library
- [ ] `aiterm claude hooks create <name>` - Interactive hook creator
- [ ] `aiterm claude hooks validate` - Check hook syntax and behavior
- [ ] `aiterm claude hooks test <name>` - Dry-run hook with sample data
- [ ] `aiterm claude hooks enable/disable <name>` - Toggle hooks

**Hook Template Library:**
- **PreToolUse Hooks:**
  - block-sensitive-files (prevent .env, credentials access)
  - validate-bash-commands (security checks)
  - cost-estimator (warn before expensive operations)
- **SessionStart Hooks:**
  - quota-display (show API quota on startup)
  - project-context (detect project type, show info)
  - git-status-check (warn if uncommitted changes)
- **PostToolUse Hooks:**
  - test-runner (auto-run tests after edits)
  - backup-creator (save versions before changes)
  - changelog-updater (track file modifications)
- **UserPromptSubmit Hooks:**
  - ✅ **@smart prompt optimizer v1.0** (AUTO-ENHANCE MODE - ACTIVE!)
    - Detects `@smart` or `[refine]` in prompts
    - **Automatically** adds project context (type, git, recent files)
    - **Non-interactive** - instant enhancement, zero friction
    - Works with existing `/workflow:*` commands
    - Location: `~/.claude/hooks/prompt-optimizer.sh`
    - Status: Production-ready ✅
  - 🔮 **@smart v2.0** (Future: INTERACTIVE MODE)
    - Build `/smart` slash command with menu
    - Options: Submit/Revise/Delegate/Cancel
    - Works alongside auto-enhance hook
    - See "Command Templates" section below
  - context-injector (add project-specific context)
  - style-enforcer (ensure consistency)
- **PermissionRequest Hooks:**
  - auto-approve-reads (safe operations)
  - block-destructive (prevent rm, dangerous ops)

#### 2. Command Templates (Enhanced with Frontmatter)
- [ ] `aiterm claude commands list` - Show all custom commands
- [ ] `aiterm claude commands create --template <type>` - From library
- [ ] `aiterm claude commands validate` - Check frontmatter syntax
- [ ] `aiterm claude commands migrate` - Convert old commands to new format
- [ ] `aiterm claude commands namespace <category>` - Create namespaced commands

**Template types with full frontmatter:**
- **Smart Prompting** (`/smart`) - 🔮 PLANNED (v2.0)
  - `/smart [prompt]` - Interactive menu for prompt optimization
    - Gathers project context (like @smart hook)
    - Shows interactive menu: Submit/Revise/Delegate/Cancel
    - Allows editing in $EDITOR before submission
    - Background agent delegation via Task tool
    - Complements auto-enhance @smart hook
  - Implementation: Interactive slash command (not hook)
  - Priority: Week 2-3 after core CLI is stable
- **Research** (`/research:*`):
  - `/research:literature` (with Zotero MCP integration)
  - `/research:cite` (format citations)
  - `/research:methods` (statistical methods templates)
  - `/research:tables` (LaTeX table generation)
- **Workflow** (`/workflow:*`):
  - `/workflow:recap` (your existing command)
  - `/workflow:next` (your existing command)
  - `/workflow:focus` (your existing command)
  - `/workflow:brainstorm` (your existing command)
- **Teaching** (`/teaching:*`):
  - `/teaching:grade` (with rubric)
  - `/teaching:feedback` (constructive comments)
  - `/teaching:rubric` (create grading rubrics)
- **Dev** (`/dev:*`):
  - `/dev:review` (code review standards)
  - `/dev:test` (run test suite)
  - `/dev:deploy` (deployment checklist)
- **R Package** (`/rpkg:*`):
  - `/rpkg:check` (devtools::check())
  - `/rpkg:document` (devtools::document())
  - `/rpkg:test` (devtools::test())
  - `/rpkg:build` (full build pipeline)

#### 3. MCP Server Management (Comprehensive)
- [ ] `aiterm mcp list` - Show configured servers with status
- [ ] `aiterm mcp search <keyword>` - Search mcp.run, glama.ai
- [ ] `aiterm mcp install <server>` - Install + configure interactively
- [ ] `aiterm mcp test <server>` - Test connection and tools
- [ ] `aiterm mcp config <server>` - Edit configuration
- [ ] `aiterm mcp credentials <server>` - Secure credential management
- [ ] `aiterm mcp recommend` - Suggest servers based on project type
- [ ] `aiterm mcp oauth <server>` - OAuth 2.0 authentication setup
- [ ] `aiterm mcp validate` - Validate .mcp.json syntax
- [ ] `aiterm mcp export/import` - Team configuration sharing

**MCP Server Categories:**
- **Research & Data:**
  - zotero-mcp (your existing Statistical Research MCP!)
  - postgres-mcp, sqlite-mcp (database access)
  - jupyter-mcp (notebook interaction)
  - r-execution (execute R code)
- **Development:**
  - filesystem (you already use this!)
  - github (issues, PRs)
  - gitlab
  - docker-mcp
- **Productivity:**
  - slack-mcp
  - google-drive-mcp
  - notion-mcp
  - calendar-mcp

**Special Feature - Context-Aware Installation:**
```bash
cd ~/projects/r-packages/medfit
aiterm mcp recommend

# Suggests:
# - r-execution (run R code)
# - github (for package releases)
# - filesystem (local file access)
```

#### 4. Skills Management (NEW - Oct 2025 Feature!)
- [ ] `aiterm skills list` - Show installed skills
- [ ] `aiterm skills create <name>` - Interactive skill creator
- [ ] `aiterm skills install <name>` - Install from template library
- [ ] `aiterm skills validate <name>` - Check SKILL.md format
- [ ] `aiterm skills test <name>` - Test skill invocation
- [ ] `aiterm skills share <name>` - Export for team
- [ ] `aiterm skills import <file>` - Install from export

**Skill Template Library:**
- **Research Skills:**
  - statistical-analysis-workflow (data → analysis → tables → plots)
  - literature-review (search → read → cite → summarize)
  - methods-writing (statistical methods documentation)
  - sensitivity-analysis (robustness checks)
- **R Package Skills:**
  - r-package-workflow (check → test → document → build)
  - cran-submission (pre-CRAN checklist)
  - pkgdown-site (build documentation site)
  - vignette-creation (create package vignettes)
- **Teaching Skills:**
  - assignment-grading (consistent grading workflow)
  - feedback-generation (constructive comments)
  - rubric-creation (grading rubrics)
  - course-materials (lecture/homework templates)
- **Code Quality Skills:**
  - code-review-standards (your project-specific standards)
  - test-coverage (ensure adequate testing)
  - documentation (docstrings, comments)
  - refactoring (safe refactoring patterns)

**Skill Features:**
- Automatic invocation (Claude detects when to use)
- Supporting files (scripts, templates)
- Path-based rules (`.claude/rules/` for conditional activation)
- Allowed-tools restrictions
- Progressive disclosure (lazy loading)

---

## Phase 2.5: Advanced Claude Code Features (v0.2.5)

**Goal:** Leverage newly discovered capabilities

### Features

#### 1. Subagent Management
- [ ] `aiterm agents list` - Show configured subagents
- [ ] `aiterm agents create <name>` - Interactive subagent creator
- [ ] `aiterm agents test <name>` - Test subagent behavior
- [ ] `aiterm agents validate` - Check agent config

**Subagent Templates:**
- **research-agent** (tools: Read, WebFetch, focused on research)
- **coding-agent** (tools: all, focused on implementation)
- **review-agent** (tools: Read, Grep, Glob, focused on code review)
- **statistical-agent** (tools: Bash, Read, focused on R/stats)

#### 2. Memory System Management
- [ ] `aiterm memory hierarchy` - Show precedence order
- [ ] `aiterm memory validate` - Check CLAUDE.md files
- [ ] `aiterm memory create` - Interactive CLAUDE.md creator
- [ ] `aiterm memory rules add` - Add path-specific rules
- [ ] `aiterm memory migrate` - Convert old format to new

**Memory Templates:**
- Research project CLAUDE.md
- R package CLAUDE.md
- Teaching course CLAUDE.md
- Dev tools CLAUDE.md

#### 3. Output Styles
- [ ] `aiterm styles list` - Show available output styles
- [ ] `aiterm styles create <name>` - Create custom style
- [ ] `aiterm styles preview <name>` - Preview style changes
- [ ] `aiterm styles set <name>` - Set default style

**Custom Styles:**
- academic-writing (formal, citation-focused)
- teaching-materials (student-friendly)
- code-documentation (developer-focused)
- statistical-reports (results presentation)

#### 4. Plugin Management
- [ ] `aiterm plugins list` - Show installed plugins
- [ ] `aiterm plugins search <keyword>` - Search marketplaces
- [ ] `aiterm plugins install <name>` - Install plugin
- [ ] `aiterm plugins create` - Initialize new plugin
- [ ] `aiterm plugins package` - Package for distribution
- [ ] `aiterm plugins validate` - Check plugin.json

**Plugin Components:**
- Commands bundled together
- Agents pre-configured
- Skills included
- Hooks packaged
- MCP servers integrated

#### 5. GitHub Actions Integration
- [ ] `aiterm ci generate` - Generate GitHub Actions workflow
- [ ] `aiterm ci test` - Test workflow locally
- [ ] `aiterm ci validate` - Check workflow syntax

**Workflow Templates:**
- R package CI (check, test, coverage)
- Research paper CI (compile LaTeX, run analysis)
- Documentation CI (build site, deploy)

---

## Phase 3: Gemini & Multi-Tool (v0.3.0)

**Goal:** Support multiple AI tools

### Features

#### 1. Gemini CLI Integration
- [ ] Gemini-specific profiles
- [ ] Gemini triggers
- [ ] `aiterm gemini init`
- [ ] `aiterm switch claude|gemini`

#### 2. Context-Aware Features
- [ ] `aiterm context detect` - Show current context
- [ ] `aiterm context history` - Where you've been today
- [ ] `aiterm context export` - Export for other tools
- [ ] Context-based recommendations
  - Suggest Claude for coding
  - Suggest Gemini for research

#### 3. Status Bar Builder
- [ ] Interactive status bar designer
- [ ] Component library (icon, name, branch, quota, time)
- [ ] `aiterm statusbar build`
- [ ] `aiterm statusbar preview`
- [ ] Theme variants (cool-blues, forest-greens, purple-charcoal)

---

## Phase 4: Advanced & Polish (v1.0.0)

**Goal:** Production-ready public release

### Features

#### 1. Multi-Terminal Support
- [ ] iTerm2 (full support)
- [ ] Warp (basic support)
- [ ] Alacritty (config file)
- [ ] Kitty (config file)
- [ ] Terminal capability detection
- [ ] Graceful degradation

#### 2. Workflow Templates
- [ ] Template system architecture
- [ ] `aiterm workflow install <name>`
- [ ] Built-in workflows:
  - research (R, Quarto, literature)
  - teaching (courses, grading)
  - dev-tools (current DT setup)
  - web-dev
  - data-science
- [ ] Export/import workflows
- [ ] Community template sharing

#### 3. Session Management
- [ ] `aiterm record session` - Track context switches
- [ ] `aiterm sessions list`
- [ ] `aiterm sessions show <id>`
- [ ] Session analytics
  - Time per project
  - Quota usage patterns
  - Context switch frequency

#### 4. Web UI (Optional)
- [ ] Streamlit-based config builder
- [ ] Visual profile editor
- [ ] Template browser
- [ ] Usage dashboard

---

## Future Ideas (Post-v1.0)

### AI Workflow Optimizer
- Analyze usage patterns
- Suggest optimal settings
- Auto-tune based on behavior
- Compare Claude vs Gemini performance

### Context-Aware Quota System
- Different quotas per project type
- Warn before expensive operations
- Integrate with existing `qu` command
- Budget tracking per context

### Cross-Tool Intelligence
- Task-based AI selection
  - Code → Claude
  - Research → Gemini
  - Brainstorming → Both
- Side-by-side comparison mode
- Response quality tracking

### Teaching Mode
- Student-safe profiles
- Limited quotas
- Session recording for grading
- Assignment-specific contexts

### Integration Ecosystem
- VSCode extension
- Raycast extension
- Alfred workflow
- Slack status sync
- Calendar integration

### Advanced Terminal Features
- Custom keyboard shortcuts
- Hotkey window management
- Multi-pane layouts
- Terminal multiplexer integration

---

## Technical Debt & Improvements

### Code Quality
- [ ] Comprehensive test coverage (>80%)
- [ ] Type hints throughout
- [ ] Documentation (docstrings)
- [ ] CI/CD pipeline
- [ ] Pre-commit hooks

### Performance
- [ ] Fast startup (<100ms)
- [ ] Lazy loading modules
- [ ] Cache terminal detection
- [ ] Optimize context detection

### User Experience
- [ ] Rich CLI output (colors, tables)
- [ ] Progress bars for long operations
- [ ] Better error messages
- [ ] Interactive prompts (questionary)
- [ ] Shell completion (zsh, bash)

### Distribution
- [ ] PyPI package
- [ ] Homebrew formula
- [ ] Docker image
- [ ] Documentation site (MkDocs)

---

## Community Features

### Sharing & Collaboration
- [ ] Template marketplace
- [ ] User configs repository
- [ ] GitHub discussions
- [ ] Example gallery

### Documentation
- [ ] Quickstart guide
- [ ] Video tutorials
- [ ] Recipe book (common patterns)
- [ ] API documentation
- [ ] Contributing guide

---

## Non-Goals (Explicitly Out of Scope)

- Full IDE replacement
- Windows primary support (nice-to-have only)
- Non-AI terminal optimization
- Shell customization (use oh-my-zsh/powerlevel10k)
- Git workflow management (use existing tools)

---

## Success Metrics

### MVP (v0.1)
- DT uses daily for 1 week
- Faster setup than manual config
- No regressions from current aiterm

### v1.0
- 10+ external users
- <5 GitHub issues
- Documentation complete
- Install time <5 minutes

### Long-term
- 100+ stars on GitHub
- Community templates
- Integration with other tools
- Featured in Claude Code docs
