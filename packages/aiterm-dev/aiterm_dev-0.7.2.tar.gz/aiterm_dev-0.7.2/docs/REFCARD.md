# aiterm Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ AITERM v0.7.1 - Terminal Optimizer for AI Development      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ESSENTIAL                                                   │
│ ──────────                                                  │
│ ait doctor              Check installation                  │
│ ait detect              Show project context                │
│ ait switch              Apply context to terminal           │
│ ait hello               Diagnostic greeting                 │
│ ait info                System diagnostics (--json)         │
│                                                             │
│ INTERACTIVE TUTORIALS (v0.6.0)                              │
│ ──────────────────────────────                              │
│ ait learn start         Start interactive tutorial          │
│ ait learn list          List available tutorials            │
│ ait learn progress      Show learning progress              │
│ ait learn reset         Reset tutorial progress             │
│                                                             │
│ RELEASE MANAGEMENT (v0.5.0)                                 │
│ ───────────────────────────                                 │
│ ait release check       Validate release readiness          │
│ ait release status      Show version & pending changes      │
│ ait release pypi        Build and publish to PyPI           │
│ ait release homebrew    Update Homebrew formula             │
│ ait release tag         Create annotated git tag            │
│ ait release notes       Generate release notes              │
│ ait release full        Full workflow: check→tag→pypi       │
│                                                             │
│ CONFIGURATION                                               │
│ ──────────────────────────────                              │
│ ait config path         Show config directory               │
│ ait config path --all   Show all paths with status          │
│ ait config show         Display current configuration       │
│ ait config init         Create default config.toml          │
│ ait config edit         Open config in $EDITOR              │
│                                                             │
│ CLAUDE CODE                                                 │
│ ──────────                                                  │
│ ait claude settings     View current settings               │
│ ait claude backup       Backup settings file                │
│ ait claude approvals    Manage auto-approvals               │
│   approvals list        Show current approvals              │
│   approvals add <cmd>   Add approval rule                   │
│   approvals preset      Apply preset (safe/moderate/full)   │
│                                                             │
│ CONTEXT DETECTION                                           │
│ ─────────────────                                           │
│ ait context detect      Detect project type                 │
│ ait context show        Alias for detect                    │
│ ait context apply       Apply profile to terminal           │
│                                                             │
│ PROFILES                                                    │
│ ─────────                                                   │
│ ait profile list        List available profiles             │
│ ait profile show        Show current profile                │
│                                                             │
│ MCP SERVERS                                                 │
│ ───────────                                                 │
│ ait mcp list            List configured servers             │
│ ait mcp status          Check server health                 │
│ ait mcp test <name>     Test specific server                │
│                                                             │
│ HOOKS & COMMANDS                                            │
│ ────────────────                                            │
│ ait hooks list          List installed hooks                │
│ ait commands list       List command templates              │
│                                                             │
│ DOCUMENTATION                                               │
│ ─────────────                                               │
│ ait docs check          Validate documentation              │
│ ait docs serve          Preview docs locally                │
│                                                             │
│ TERMINALS                                                   │
│ ─────────                                                   │
│ ait terminals list      List supported terminals            │
│ ait terminals detect    Detect current terminal             │
│ ait terminals features  Show terminal features              │
│ ait terminals compare   Compare terminal capabilities       │
│                                                             │
│ GHOSTTY (v0.3.9+)                                           │
│ ─────────────────                                           │
│ ait ghostty status      Show Ghostty configuration          │
│ ait ghostty config      Display config file location        │
│ ait ghostty theme       List or set themes (14 built-in)    │
│ ait ghostty font        Get or set font configuration       │
│ ait ghostty set         Set any config value                │
│                                                             │
│ FEATURE WORKFLOW (v0.6.2+)                                  │
│ ──────────────────────────                                  │
│ ait feature status      Show feature pipeline visualization │
│ ait feature list        List features with worktree paths   │
│ ait feature start       Create feature branch + worktree    │
│ ait feature promote     Create PR to dev (uses gh CLI)      │
│ ait feature release     Create PR dev→main (uses gh CLI)    │
│ ait feature cleanup     Remove merged feature branches      │
│ ait recipes             Alias for workflow templates        │
│                                                             │
│ STATUSLINE (v0.7.1) 🆕                                      │
│ ──────────────────────                                      │
│ ait statusline render   Display statusLine output           │
│ ait statusline config   Manage 32 configuration options     │
│   config list           Show all config options             │
│   config get KEY        Get config value                    │
│   config set KEY VAL    Set config value                    │
│   config reset [KEY]    Reset to defaults                   │
│   config preset <name>  Apply preset (minimal)              │
│   config spacing <mode> Set gap spacing (minimal/standard)  │
│                                                             │
│ Spacing Presets (v0.7.1):                                   │
│   • minimal   - 15% gap (5-20 chars)  - Compact             │
│   • standard  - 20% gap (10-40 chars) - Balanced [default]  │
│   • spacious  - 30% gap (15-60 chars) - Wide                │
│   • Optional centered separator (…) in gap                  │
│                                                             │
│ StatusLine Features:                                        │
│   • 6 categories: display, git, project, usage, theme, time │
│   • Worktree display (🌳N count, (wt) marker)               │
│   • Smart gap spacing with presets (v0.7.1)                 │
│   • Git status (branch, dirty, ahead/behind, worktrees)     │
│   • Minimal preset removes bloat (v0.7.0)                   │
│   • 3 built-in themes (cool-blues, forest-greens, custom)   │
│                                                             │
│ FLOW-CLI INTEGRATION (v0.3.10+)                             │
│ ───────────────────────────────                             │
│ tm title <text>         Set tab title (instant)             │
│ tm profile <name>       Switch iTerm2 profile               │
│ tm which                Show detected terminal              │
│ tm detect               Detect project context              │
│ tm switch               Apply context to terminal           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ COMMON WORKFLOWS                                            │
│ ────────────────                                            │
│                                                             │
│ Quick install:                                              │
│   curl -fsSL .../install.sh | bash                          │
│                                                             │
│ First-time setup:                                           │
│   ait doctor && ait config init                             │
│                                                             │
│ Switch context when entering project:                       │
│   cd ~/my-project && ait switch                             │
│                                                             │
│ Backup before changes:                                      │
│   ait claude backup && ait claude approvals preset safe     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ SHELL ALIASES                                               │
│ ─────────────                                               │
│ ait          aiterm (main CLI)                              │
│ oc           opencode (OpenCode CLI)                        │
│ tm           terminal manager (flow-cli dispatcher)         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ CONFIG LOCATIONS                                            │
│ ────────────────                                            │
│ ~/.config/aiterm/config.toml    aiterm config (v0.3.11+)    │
│ ~/.claude/settings.json         Claude Code settings        │
│ ~/.config/opencode/config.json  OpenCode settings           │
│ ~/.config/ghostty/config        Ghostty terminal config     │
│                                                             │
│ Environment: AITERM_CONFIG_HOME overrides config path       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Docs: https://data-wise.github.io/aiterm/                   │
│ Repo: https://github.com/Data-Wise/aiterm                   │
└─────────────────────────────────────────────────────────────┘
```

## Domain-Specific Reference Cards

| Topic | File |
|-------|------|
| Claude Code | [REFCARD-CLAUDE.md](reference/REFCARD-CLAUDE.md) |
| Context Detection | [REFCARD-CONTEXT.md](reference/REFCARD-CONTEXT.md) |
| Craft Plugin | [REFCARD-CRAFT.md](reference/REFCARD-CRAFT.md) |
| Feature Workflow | [REFCARD-FEATURE.md](reference/REFCARD-FEATURE.md) |
| Ghostty Terminal | [REFCARD-GHOSTTY.md](reference/REFCARD-GHOSTTY.md) |
| Hooks | [REFCARD-HOOKS.md](reference/REFCARD-HOOKS.md) |
| IDE Integration | [REFCARD-IDE.md](reference/REFCARD-IDE.md) |
| MCP Servers | [REFCARD-MCP.md](reference/REFCARD-MCP.md) |
| OpenCode | [REFCARD-OPENCODE.md](reference/REFCARD-OPENCODE.md) |
| Sessions | [REFCARD-SESSIONS.md](reference/REFCARD-SESSIONS.md) |
| Tutorials | [REFCARD-TUTORIALS.md](reference/REFCARD-TUTORIALS.md) |

## Print Version

For a printer-friendly version without markdown formatting:

```bash
# Print to terminal
ait --help

# Save to file
ait --help > aiterm-help.txt
```
