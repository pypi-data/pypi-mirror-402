# Claude Code Integration

Complete guide to using **aiterm** with Claude Code CLI.

---

## Overview

**aiterm** helps you manage Claude Code configuration:

- ✅ View and backup `~/.claude/settings.json`
- ✅ Manage auto-approval permissions with curated presets
- ✅ Quick setup with safe, production-tested configurations
- ✅ Hook management (`ait hooks list`)
- ✅ MCP server integration (`ait mcp list`)

---

## Quick Setup (5 Minutes)

### 1. Check Current Configuration

```bash
# View current settings
ait claude settings

# List current auto-approvals
ait claude approvals list
```

### 2. Backup Before Changes

```bash
# Create timestamped backup
ait claude backup
# → Creates: ~/.claude/settings.backup-20241218-153045.json
```

### 3. Add Safe Permissions

```bash
# Start with safe read-only operations
ait claude approvals add safe-reads

# Add git operations (no destructive commands)
ait claude approvals add git-ops

# Add your primary dev tools
ait claude approvals add python-dev  # or node-dev, r-dev
```

### 4. Verify

```bash
# Check what was added
ait claude approvals list
```

**Done!** Claude Code can now execute approved commands without prompting.

---

## Auto-Approval Presets

### safe-reads (5 permissions)

**Purpose:** Read-only file and directory operations

**Permissions:**
```bash
Read(/Users/youruser/**)     # Read any file
Glob(**/*.py)                 # Search for files
Grep(*)                       # Search file contents
Bash(ls:*)                    # List directories
Bash(cat:*)                   # View file contents
```

**Use when:**
- Starting with Claude Code
- Maximum safety
- Exploration and learning

**Add:**
```bash
ait claude approvals add safe-reads
```

---

### git-ops (12 permissions)

**Purpose:** Git workflow commands (no destructive operations)

**Permissions:**
```bash
Bash(git status:*)
Bash(git diff:*)
Bash(git log:*)
Bash(git show:*)
Bash(git branch:*)
Bash(git fetch:*)
Bash(git add:*)
Bash(git commit:*)
Bash(git push:*)
Bash(git checkout:*)
Bash(git pull:*)
Bash(git stash:*)
```

**Excluded:** `git reset --hard`, `git push --force`, destructive operations

**Use when:**
- Daily development workflow
- Code reviews
- Branch management

**Add:**
```bash
ait claude approvals add git-ops
```

---

### github-cli (8 permissions)

**Purpose:** GitHub CLI operations

**Permissions:**
```bash
Bash(gh pr list:*)
Bash(gh pr view:*)
Bash(gh pr create:*)
Bash(gh pr checkout:*)
Bash(gh issue list:*)
Bash(gh issue view:*)
Bash(gh repo:*)
Bash(gh api:*)               # Read-only API calls
```

**Excluded:** `gh pr merge`, destructive repo operations

**Use when:**
- Working with pull requests
- Managing issues
- Reviewing code on GitHub

**Add:**
```bash
ait claude approvals add github-cli
```

---

### python-dev (6 permissions)

**Purpose:** Python development tools

**Permissions:**
```bash
Bash(python3:*)
Bash(pip3 install:*)
Bash(pytest:*)
Bash(python -m pytest:*)
Bash(uv:*)                   # UV package manager
Bash(uv pip install:*)
```

**Use when:**
- Python package development
- Running tests
- Installing dependencies

**Add:**
```bash
ait claude approvals add python-dev
```

---

### node-dev (7 permissions)

**Purpose:** Node.js and JavaScript development

**Permissions:**
```bash
Bash(npm install:*)
Bash(npm run:*)
Bash(npx:*)
Bash(bun:*)                  # Bun runtime
Bash(node:*)
Bash(yarn:*)
Bash(pnpm:*)
```

**Use when:**
- JavaScript/TypeScript development
- React/Vue/Angular projects
- npm package development

**Add:**
```bash
ait claude approvals add node-dev
```

---

### r-dev (5 permissions)

**Purpose:** R package development and Quarto

**Permissions:**
```bash
Bash(Rscript:*)
Bash(R CMD:*)
Bash(R:*)
Bash(quarto:*)
Bash(which:*)                # Check R installation
```

**Use when:**
- R package development
- Statistical analysis
- Quarto document rendering

**Add:**
```bash
ait claude approvals add r-dev
```

---

### web-tools (2 permissions)

**Purpose:** Web search and content fetching

**Permissions:**
```bash
WebSearch
WebFetch(domain:*)
```

**Use when:**
- Research tasks
- Documentation lookups
- Finding examples online

**Add:**
```bash
ait claude approvals add web-tools
```

---

### minimal (10 permissions)

**Purpose:** Bare minimum shell commands

**Permissions:**
```bash
Bash(ls:*)
Bash(cat:*)
Bash(echo:*)
Bash(pwd:*)
Bash(cd:*)
Bash(find:*)
Bash(grep:*)
Bash(wc:*)
Bash(head:*)
Bash(tail:*)
```

**Use when:**
- Ultra-conservative approach
- Learning Claude Code
- Shared environments

**Add:**
```bash
ait claude approvals add minimal
```

---

## Recommended Combinations

### For Web Developers

```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add node-dev
ait claude approvals add github-cli
ait claude approvals add web-tools
```

### For Python Developers

```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add python-dev
ait claude approvals add github-cli
```

### For R Package Developers

```bash
ait claude approvals add safe-reads
ait claude approvals add git-ops
ait claude approvals add r-dev
ait claude approvals add github-cli
```

### Conservative Starter

```bash
ait claude approvals add safe-reads
ait claude approvals add minimal
```

---

## Managing Permissions

### View Current Approvals

```bash
# List all approved permissions
ait claude approvals list

# View in Claude Code settings file
ait claude settings
```

### Backup Strategy

```bash
# Before adding new permissions
ait claude backup

# Creates timestamped backup:
# ~/.claude/settings.backup-20241218-153045.json
```

**Restore from backup:**
```bash
cp ~/.claude/settings.backup-TIMESTAMP.json ~/.claude/settings.json
```

### Remove Permissions

Currently, you must manually edit `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Remove this line",
      "Bash(pytest:*)"
    ]
  }
}
```

**Future:** `ait claude approvals remove <preset>` (not yet implemented)

---

## Safety Guidelines

### What Presets DON'T Include

**No destructive operations:**
- ❌ `rm -rf` commands
- ❌ `git reset --hard`
- ❌ `git push --force` to main/master
- ❌ System file modifications
- ❌ Credential/secret exposure

**Always requires confirmation:**
- Permanent deletions
- Force pushes
- Production deployments
- Publishing packages
- Account modifications

### When to Be Cautious

**Don't auto-approve:**
- Commands you don't understand
- Operations on production systems
- Financial transactions
- Credential management
- Package publishing

**Always review:**
- PRs before merging
- Commits before pushing
- Deployments to production

---

## Troubleshooting

### Permissions Not Working

```bash
# 1. Verify permissions are in settings
ait claude approvals list

# 2. Check settings file directly
cat ~/.claude/settings.json | grep -A 20 '"allow"'

# 3. Restart Claude Code CLI
# (close terminal, open new session)
```

### Accidentally Added Wrong Preset

```bash
# Restore from backup
ait claude backup  # First, backup current state
cp ~/.claude/settings.backup-PREVIOUS.json ~/.claude/settings.json

# Verify restoration
ait claude approvals list
```

### Finding the Right Preset

```bash
# List all available presets with descriptions
ait claude approvals presets

# Check what permissions a preset includes
# (view source: src/aiterm/claude/settings.py)
```

---

## Advanced Usage

### Custom Permission Patterns

Edit `~/.claude/settings.json` to add custom patterns:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(mycommand:*)",          // Custom command
      "Read(/specific/path/**)",    // Specific directory
      "Bash(npm run test:unit:*)"   // Specific npm script
    ]
  }
}
```

**Pattern syntax:**
- `*` = wildcard (matches any characters)
- `:*` = matches any arguments after command
- `**` = recursive directory match

### Project-Specific Approvals

Use `.claude/settings.local.json` in project root:

```json
{
  "permissions": {
    "allow": [
      "Bash(make:*)",
      "Bash(docker-compose:*)"
    ]
  }
}
```

Claude Code merges local settings with global settings.

---

## Hooks & MCP Integration

### Hook Management

```bash
# List installed hooks
ait hooks list
```

See [Hooks Reference](../reference/REFCARD-HOOKS.md) for details.

### MCP Server Integration

```bash
# List configured MCP servers
ait mcp list

# Validate MCP configuration
ait mcp validate

# Test a specific server
ait mcp test filesystem
```

See [MCP Reference](../reference/REFCARD-MCP.md) for details.

---

## Resources

- **Claude Code Docs:** [https://code.claude.com/docs](https://code.claude.com/docs)
- **Settings Reference:** `~/.claude/settings.json`
- **Command Reference:** [CLI Commands](../reference/commands.md)
- **Workflows:** [Common Workflows](workflows.md)
# Claude Code Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ AITERM - Claude Code Commands                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ SETTINGS                                                    │
│ ─────────                                                   │
│ ait claude settings        View current settings            │
│ ait claude backup          Create timestamped backup        │
│                                                             │
│ AUTO-APPROVALS                                              │
│ ──────────────                                              │
│ ait claude approvals list     Show current approvals        │
│ ait claude approvals presets  List available presets        │
│ ait claude approvals add <p>  Add preset to approvals       │
│                                                             │
│ PRESETS                                                     │
│ ────────                                                    │
│ safe       Read-only commands (git status, ls, cat)         │
│ moderate   Safe file edits + git operations                 │
│ git        Git-specific operations                          │
│ npm        Node.js package commands                         │
│ python     Python dev commands (pytest, pip)                │
│ full       All common permissions                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ COMMON WORKFLOWS                                            │
│ ────────────────                                            │
│                                                             │
│ First-time setup:                                           │
│   ait claude backup && ait claude approvals add safe        │
│                                                             │
│ Add development permissions:                                │
│   ait claude approvals add moderate                         │
│                                                             │
│ Check what's approved:                                      │
│   ait claude approvals list                                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ CONFIG FILE                                                 │
│ ───────────                                                 │
│ Location: ~/.claude/settings.json                           │
│ Backup:   ~/.claude/settings.json.backup-YYYYMMDD-HHMMSS    │
│                                                             │
│ Structure:                                                  │
│   {                                                         │
│     "permissions": {                                        │
│       "allow": ["Bash(git:*)", "Read(*)"],                  │
│       "deny": []                                            │
│     }                                                       │
│   }                                                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ PERMISSION PATTERNS                                         │
│ ───────────────────                                         │
│ Bash(cmd:*)         Allow command with any args             │
│ Bash(cmd:arg)       Allow specific command + arg            │
│ Read(*)             Allow reading any file                  │
│ Write(path/*)       Allow writing to path                   │
│ Edit(*)             Allow editing any file                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SEE ALSO                                                    │
│ ─────────                                                   │
│ Main REFCARD:  docs/REFCARD.md                              │
│ MCP REFCARD:   docs/reference/REFCARD-MCP.md                │
│ Hooks REFCARD: docs/reference/REFCARD-HOOKS.md              │
└─────────────────────────────────────────────────────────────┘
```
# Claude Code & Desktop Capabilities

**Research Date:** December 15, 2025
**Purpose:** Understanding enhancement possibilities for aiterm

---

## Executive Summary

**Three Pillars of Claude Ecosystem:**

1. **MCP (Model Context Protocol)** - Connect AI to external services (GitHub, Slack, databases)
2. **Desktop Extensions (.mcpb)** - 1-click MCP server installation (replaces manual config)
3. **Skills** - Reusable AI workflows with instructions + optional code

**All three work in:**
- Claude Desktop UI
- Claude Code CLI
- Claude API (with code execution)

**Status:** MCP is now industry standard (Linux Foundation), actively growing, NOT deprecated.

---

## Enhancement Opportunities for aiterm

### 🎯 What aiterm Can Optimize

#### 1. MCP Server Management
**Current Pain Points:**
- Manual `.mcp.json` editing
- Finding servers (scattered across GitHub, mcp.run, glama.ai)
- Testing configurations
- Managing credentials

**aiterm Opportunities:**
```bash
# Phase 2-3 features
aiterm mcp list                    # Show installed servers
aiterm mcp search <keyword>        # Search registry
aiterm mcp install <server>        # Install + configure
aiterm mcp test <server>          # Test connection
aiterm mcp config <server>        # Interactive config
aiterm mcp credentials <server>   # Secure credential mgmt
```

#### 2. Skills Management
**Current Pain Points:**
- Manual SKILL.md creation
- No discovery mechanism
- Sharing requires copy/paste
- No versioning

**aiterm Opportunities:**
```bash
# Phase 2-3 features
aiterm skills list                 # Show available skills
aiterm skills create <name>        # Interactive skill creator
aiterm skills install <name>       # From template library
aiterm skills share <name>         # Export for team
aiterm skills validate <name>      # Check SKILL.md format
```

**Skill Templates aiterm Could Provide:**
- **Research workflows** - Literature search, citation formatting
- **R package workflows** - Test → check → document → build
- **Code review standards** - Your project-specific review process
- **Data analysis** - Standard analysis patterns
- **Teaching** - Assignment grading, feedback templates

#### 3. Desktop Extensions Discovery
**Current State:**
- Must browse in app
- No CLI access
- No batch installation

**aiterm Opportunities:**
```bash
# Phase 3-4 features
aiterm ext list                    # Show available extensions
aiterm ext search <keyword>        # Search directory
aiterm ext recommend              # Based on project type
aiterm ext info <name>            # Show details
```

#### 4. Command System Enhancement
**Current Capabilities:**
- Custom slash commands in `.claude/commands/*.md`
- Simple argument passing
- No validation, no discovery

**aiterm Opportunities:**
```bash
# Phase 2 features
aiterm claude commands list                  # Show all commands
aiterm claude commands create <name>         # Interactive creator
aiterm claude commands template <type>       # From library
aiterm claude commands validate             # Check syntax
aiterm claude commands test <name>          # Dry run

# Command templates
aiterm claude commands template workflow     # /recap, /next, /focus
aiterm claude commands template research     # /literature, /cite
aiterm claude commands template dev          # /review, /test, /deploy
```

#### 5. Hooks System (Discovered Capability!)
**Current State:** Documented but underused

**Hook Types Available:**
- `SessionStart` - When Claude Code starts
- `SessionEnd` - When Claude Code exits
- `ToolUse` - Before/after tool use
- `UserPrompt` - Before user prompt processed

**aiterm Opportunities:**
```bash
# Phase 2 features
aiterm claude hooks list                     # Show available hooks
aiterm claude hooks install <name>           # From template library
aiterm claude hooks create <name>            # Interactive creator
aiterm claude hooks enable/disable <name>    # Toggle hooks

# Hook templates
aiterm claude hooks install session-start    # Show quota on startup
aiterm claude hooks install pre-commit       # Run tests before commit
aiterm claude hooks install cost-tracker     # Monitor API costs
aiterm claude hooks install context-aware    # Detect project, set vars
```

**Hook Template Library:**
```yaml
# session-start.yaml
name: "Quota Display"
trigger: SessionStart
script: |
  #!/bin/bash
  # Show quota status
  ~/.claude/statusline-p10k.sh --quota-only

  # Show project context
  aiterm context show
```

#### 6. Settings Management
**Current Pain Points:**
- Manual JSON editing
- No validation
- No presets
- Auto-approvals hard to manage

**aiterm Already Planned:**
```bash
aiterm claude settings show
aiterm claude settings backup
aiterm claude settings validate
aiterm claude approvals add-preset <name>
aiterm claude approvals list
```

**Additional Opportunities:**
```bash
# Phase 2-3
aiterm claude settings diff              # Compare with default
aiterm claude settings migrate           # Upgrade format
aiterm claude settings export            # For team sharing
aiterm claude settings import <file>     # Load team config
```

---

## Integration Patterns

### Pattern 1: Context-Aware Skills
**Idea:** aiterm detects project type, auto-suggests relevant skills

```bash
cd ~/projects/r-packages/medfit
aiterm context detect

# aiterm responds:
📦 R Package detected: medfit

💡 Recommended skills:
  1. r-package-workflow (test → check → document)
  2. statistical-methods (analysis templates)
  3. cran-submission (prepare for CRAN)

Install? (y/n)
```

### Pattern 2: MCP + Context Integration
**Idea:** Auto-configure MCP servers based on project

```bash
cd ~/projects/research/paper
aiterm context detect

# aiterm responds:
📝 Research project detected

💡 Recommended MCP servers:
  1. zotero-mcp (bibliography management)
  2. filesystem (local file access)
  3. r-execution (run R code)

Install? (y/n)
```

### Pattern 3: Workflow Automation
**Idea:** Combine hooks + skills + context

```yaml
# .claude/workflows/r-package-dev.yaml
name: "R Package Development"
triggers:
  - context: rpkg

hooks:
  SessionStart:
    - show-quota
    - check-git-status
    - display-test-coverage

skills:
  - r-package-workflow
  - code-review-standards

mcp_servers:
  - filesystem
  - github

commands:
  - /check (runs devtools::check())
  - /test (runs devtools::test())
  - /document (runs devtools::document())
```

Usage:
```bash
aiterm workflow install r-package-dev
cd ~/projects/r-packages/medfit
# Workflow auto-activates!
```

---

## MCP Server Ecosystem (Relevant to DT)

### Statistical/Research
- **zotero-mcp** - Bibliography management
- **r-mcp** - Execute R code (your existing Statistical Research MCP!)
- **python-mcp** - Execute Python
- **jupyter-mcp** - Notebook interaction

### Development
- **filesystem** - Local file access ✅ (you use this)
- **github** - Issues, PRs, repos
- **gitlab** - Similar for GitLab
- **git-mcp** - Advanced git operations

### Data
- **postgres-mcp** - Database queries
- **sqlite-mcp** - Local databases
- **mongodb-mcp** - NoSQL
- **csv-mcp** - CSV file operations

### Productivity
- **slack-mcp** - Send messages, search
- **google-drive-mcp** - Access Drive
- **notion-mcp** - Database queries
- **calendar-mcp** - Calendar integration

---

## Skills Use Cases for DT

### Research Skills
```markdown
# .claude/skills/statistical-analysis/SKILL.md
---
name: "Statistical Analysis Workflow"
description: "Standard analysis pipeline for research projects"
---

When analyzing data:
1. Load with {readr} or {haven}
2. Check assumptions (normality, homoscedasticity)
3. Descriptive statistics table (Table 1)
4. Main analysis with sensitivity
5. Generate publication-quality plots
6. Export results to LaTeX tables
```

### Teaching Skills
```markdown
# .claude/skills/grade-assignment/SKILL.md
---
name: "Assignment Grading"
description: "Consistent grading workflow for student submissions"
---

Grading criteria:
1. Code runs without errors (40%)
2. Correct statistical method (30%)
3. Interpretation clarity (20%)
4. Code style and documentation (10%)

Provide:
- Numeric grade
- 2-3 sentence feedback
- 1 suggestion for improvement
```

### Package Development Skills
```markdown
# .claude/skills/r-package-release/SKILL.md
---
name: "R Package Release Checklist"
description: "Pre-release checks for R packages"
---

Before releasing:
1. Run devtools::check() - must pass
2. Update NEWS.md with changes
3. Update version in DESCRIPTION
4. Run pkgdown::build_site()
5. Update README with new version
6. Create GitHub release
7. Submit to CRAN (if public)
```

---

## Enhancement Priority Matrix

### High Priority (Phase 2)
- ✅ Hook management system
- ✅ Command template library
- ✅ Skills creation workflow
- ✅ MCP server installation helper

### Medium Priority (Phase 3)
- MCP server discovery/search
- Skills marketplace/sharing
- Workflow automation system
- Team config sharing

### Low Priority (Phase 4)
- Desktop Extension CLI access
- Advanced hook orchestration
- Multi-project workflows
- Integration with other tools

---

## Technical Implementation Notes

### File Locations
```
~/.claude/                          # Personal config
├── settings.json                   # Main settings
├── skills/                         # Personal skills
│   └── my-skill/
│       └── SKILL.md
├── commands/                       # Custom commands
│   └── my-command.md
└── hooks/                          # Hooks (if supported)
    └── session-start.sh

.claude/                            # Project config
├── CLAUDE.md                       # Project context
├── skills/                         # Project-specific skills
├── commands/                       # Project commands
└── .mcp.json                      # MCP servers
```

### Settings.json Structure
```json
{
  "autoApprove": [
    "Bash(ls:*)",
    "Read(*)"
  ],
  "statusLine": {
    "type": "command",
    "command": "/path/to/script.sh"
  },
  "hooks": {
    "SessionStart": "/path/to/hook.sh"
  }
}
```

### .mcp.json Structure
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

---

## Integration with Existing DT Setup

### Current Setup
- ✅ Statistical Research MCP (14 tools, 17 skills) - **Already using MCP!**
- ✅ Shell MCP server - **Already using MCP!**
- ✅ Filesystem MCP - **Already using MCP!**
- ✅ StatusLine script (`~/.claude/statusline-p10k.sh`)
- ✅ Quota tracking (`qu` command)
- ✅ Workflow commands (`/recap`, `/next`, `/focus`)

### aiterm Enhancements
```bash
# Migrate workflow commands to official Claude Code commands
aiterm claude commands migrate-from ~/.claude/commands/

# Create skills from your workflow
aiterm skills create research-workflow
aiterm skills create teaching-workflow

# Manage your MCP servers
aiterm mcp list
# Shows: statistical-research, shell, filesystem

aiterm mcp config statistical-research
# Interactive config editor

# Create hooks for quota display
aiterm claude hooks install session-start
# Uses your existing qu + statusline scripts
```

---

## References

- **MCP Spec**: https://modelcontextprotocol.io
- **MCP Registry**: https://mcp.run
- **Skills Docs**: https://docs.claude.com/en/docs/claude-code/skills
- **Claude Code Docs**: https://code.claude.com/docs
- **Awesome Claude Code**: https://github.com/hesreallyhim/awesome-claude-code

---

**Next Steps for aiterm:**
1. Update IDEAS.md with specific MCP/Skills/Hooks features
2. Add to ROADMAP.md (Phase 2 priorities)
3. Design CLI commands for MCP/Skills management
4. Create template library structure

**Key Insight:** We're not just optimizing terminal profiles—we're building a **Claude Code power-user toolkit** that manages the entire ecosystem (MCP + Skills + Hooks + Commands + Context).
