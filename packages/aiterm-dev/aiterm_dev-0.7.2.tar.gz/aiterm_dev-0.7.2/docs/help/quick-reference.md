# aiterm Quick Reference

**Complete command reference for aiterm v0.7.2**

> [!TIP]
> **New to aiterm?** Start with [Get Started](../QUICK-START.md) | **Need help?** See [Help Center](index.md)

---

## Essential Commands

```
┌─────────────────────────────────────────────────────────────┐
│ CORE COMMANDS                                               │
├─────────────────────────────────────────────────────────────┤
│ ait doctor              Check installation                  │
│ ait detect              Show project context                │
│ ait switch              Apply context to terminal           │
│ ait hello               Diagnostic greeting                 │
│ ait info                System diagnostics (--json)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Ghostty Terminal

```
┌─────────────────────────────────────────────────────────────┐
│ GHOSTTY COMMANDS (v0.7.2 - Ghostty 1.2.x Support)          │
├─────────────────────────────────────────────────────────────┤
│ ait ghostty status        Show config and detection status  │
│ ait ghostty config        Display config file location      │
│ ait ghostty theme list    List 14 built-in themes           │
│ ait ghostty theme apply   Apply a theme (auto-reload)       │
│ ait ghostty font set      Set font family and/or size       │
│ ait ghostty set           Set any config key=value          │
│ ait ghostty profile       Manage profiles (list/create/apply)│
│ ait ghostty backup        Create timestamped backup         │
└─────────────────────────────────────────────────────────────┘
```

**See:** [Ghostty Complete Guide](terminals/ghostty.md) | [Ghostty Tutorial](tutorials/ghostty-setup.md)

---

## StatusLine (Claude Code)

```
┌─────────────────────────────────────────────────────────────┐
│ STATUSLINE COMMANDS (v0.7.2)                                │
├─────────────────────────────────────────────────────────────┤
│ ait statusline install    Install into Claude Code          │
│ ait statusline test       Test with mock data               │
│ ait statusline config     Manage 32 configuration options   │
│ ait statusline theme      Switch themes (3 built-in)        │
│ ait statusline spacing    Set gap spacing (minimal/standard)│
└─────────────────────────────────────────────────────────────┘
```

**See:** [StatusLine Guide](../guide/statusline.md) | [StatusLine Tutorial](tutorials/statusline-setup.md)

---

## Claude Code Integration

```
┌─────────────────────────────────────────────────────────────┐
│ CLAUDE CODE COMMANDS                                        │
├─────────────────────────────────────────────────────────────┤
│ ait claude settings       View current settings             │
│ ait claude backup         Create timestamped backup         │
│ ait claude approvals      Manage auto-approvals             │
│   approvals list          Show current approvals            │
│   approvals add <preset>  Add approval preset               │
│   approvals presets       List available presets            │
└─────────────────────────────────────────────────────────────┘
```

**Presets:** `safe` | `moderate` | `git` | `npm` | `python` | `full`

**See:** [Claude Code Integration](integrations/claude-code.md)

---

## MCP Servers

```
┌─────────────────────────────────────────────────────────────┐
│ MCP COMMANDS                                                │
├─────────────────────────────────────────────────────────────┤
│ ait mcp list              List configured servers           │
│ ait mcp status            Check server health               │
│ ait mcp test <name>       Test specific server              │
└─────────────────────────────────────────────────────────────┘
```

**See:** [MCP Integration](integrations/mcp.md)

---

## Context Detection & Profiles

```
┌─────────────────────────────────────────────────────────────┐
│ CONTEXT & PROFILE COMMANDS                                  │
├─────────────────────────────────────────────────────────────┤
│ ait context detect        Detect project type               │
│ ait context show          Alias for detect                  │
│ ait context apply         Apply profile to terminal         │
│ ait profile list          List available profiles           │
│ ait profile show          Show current profile              │
└─────────────────────────────────────────────────────────────┘
```

**See:** [Context Detection](../guide/context-detection.md) | [Profiles](../guide/profiles.md)

---

## Feature Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ FEATURE WORKFLOW COMMANDS (v0.6.2+)                         │
├─────────────────────────────────────────────────────────────┤
│ ait feature status        Show feature pipeline             │
│ ait feature list          List features with worktree paths │
│ ait feature start         Create feature branch + worktree  │
│ ait feature promote       Create PR to dev (uses gh CLI)    │
│ ait feature release       Create PR dev→main (uses gh CLI)  │
│ ait feature cleanup       Remove merged feature branches    │
└─────────────────────────────────────────────────────────────┘
```

**See:** [Feature Workflow Guide](../guide/feature-workflow.md)

---

## Configuration

```
┌─────────────────────────────────────────────────────────────┐
│ CONFIG COMMANDS                                             │
├─────────────────────────────────────────────────────────────┤
│ ait config path           Show config directory             │
│ ait config show           Display current configuration     │
│ ait config init           Create default config.toml        │
│ ait config edit           Open config in $EDITOR            │
└─────────────────────────────────────────────────────────────┘
```

**Config Locations:**

- `~/.config/aiterm/config.toml` - aiterm config
- `~/.claude/settings.json` - Claude Code settings
- `~/.config/ghostty/config` - Ghostty terminal config

---

## Tutorials & Learning

```
┌─────────────────────────────────────────────────────────────┐
│ INTERACTIVE TUTORIALS (v0.6.0)                              │
├─────────────────────────────────────────────────────────────┤
│ ait learn start           Start interactive tutorial        │
│ ait learn list            List available tutorials          │
│ ait learn progress        Show learning progress            │
│ ait learn reset           Reset tutorial progress           │
└─────────────────────────────────────────────────────────────┘
```

**See:** [All Tutorials](tutorials/index.md)

---

## Release Management

```
┌─────────────────────────────────────────────────────────────┐
│ RELEASE COMMANDS (v0.5.0)                                   │
├─────────────────────────────────────────────────────────────┤
│ ait release check         Validate release readiness        │
│ ait release status        Show version & pending changes    │
│ ait release pypi          Build and publish to PyPI         │
│ ait release homebrew      Update Homebrew formula           │
│ ait release tag           Create annotated git tag          │
│ ait release notes         Generate release notes            │
│ ait release full          Full workflow: check→tag→pypi     │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Workflows

### First-Time Setup

```bash
# Install and configure
ait doctor && ait config init

# Setup Claude Code approvals
ait claude backup && ait claude approvals add safe
```

### Ghostty Setup

```bash
# Apply theme and configure
ait ghostty theme apply catppuccin-mocha
ait ghostty font set "JetBrains Mono" 14
ait ghostty set macos-titlebar-style tabs
```

### StatusLine Setup

```bash
# Install and test
ait statusline install
ait statusline test
```

### Feature Development

```bash
# Start new feature
ait feature start my-feature

# Promote to dev
ait feature promote

# Release to main
ait feature release
```

---

## Shell Aliases

| Alias | Command | Description |
|-------|---------|-------------|
| `ait` | `aiterm` | Main CLI |
| `oc` | `opencode` | OpenCode CLI |
| `tm` | terminal manager | flow-cli dispatcher |

---

## Documentation

- **Home:** [aiterm Documentation](https://data-wise.github.io/aiterm/)
- **Help Center:** [All Help Topics](index.md)
- **Tutorials:** [Interactive Tutorials](tutorials/index.md)
- **GitHub:** [Data-Wise/aiterm](https://github.com/Data-Wise/aiterm)

---

## Version

**aiterm v0.7.2** - Updated 2026-01-17

**Latest Features:**

- Ghostty 1.2.x support (macos-titlebar-style, background-image, mouse-scroll-multiplier)
- StatusLine OSC 9;4 native progress bars
- Enhanced documentation and tutorials
