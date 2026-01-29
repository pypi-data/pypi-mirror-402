# aiterm Integration INTO flow-cli Structure

**Generated:** 2025-12-29
**Context:** How aiterm's terminal features should be implemented within flow-cli's architecture
**Question:** Should aiterm shell features become a flow-cli dispatcher/lib?

---

## flow-cli Architecture (Analysis)

```
flow-cli/
├── flow.plugin.zsh          # Entry point - loads everything
├── lib/                      # Core libraries
│   ├── core.zsh              # Logging, colors, utilities
│   ├── config.zsh            # Configuration management
│   ├── project-detector.zsh  # Project type detection
│   ├── tui.zsh               # Terminal UI helpers
│   └── dispatchers/          # Single-letter commands
│       ├── cc-dispatcher.zsh # cc → Claude Code
│       ├── g-dispatcher.zsh  # g → git helpers
│       ├── wt-dispatcher.zsh # wt → worktrees
│       └── mcp-dispatcher.zsh# mcp → MCP servers
├── commands/                  # Main commands
│   ├── work.zsh              # Session management
│   ├── dash.zsh              # Dashboard
│   └── doctor.zsh            # Health checks
└── hooks/
    ├── chpwd.zsh             # Directory change hook
    └── precmd.zsh            # Pre-prompt hook
```

### Key Patterns

| Pattern | Location | Example |
|---------|----------|---------|
| Dispatchers | `lib/dispatchers/<name>.zsh` | `cc`, `g`, `wt` |
| Commands | `commands/<name>.zsh` | `work`, `dash`, `doctor` |
| Libraries | `lib/<name>.zsh` | `project-detector`, `tui` |
| Hooks | `hooks/<event>.zsh` | `chpwd`, `precmd` |

---

## Options for aiterm Integration

### Option A: Terminal Dispatcher in flow-cli (Recommended)

**Effort:** 🔧 Medium (3-4 hours)

**What it means:** Create `t` (or `term`) dispatcher in flow-cli for terminal operations.

```
flow-cli/lib/dispatchers/
├── t-dispatcher.zsh          # NEW: Terminal dispatcher
```

**Implementation:**

```zsh
# lib/dispatchers/t-dispatcher.zsh
# Terminal dispatcher - wraps aiterm Python CLI

t() {
    case "$1" in
        # Quick terminal operations (shell-native, fast)
        title)
            shift
            _t_set_title "$@"
            ;;
        profile)
            shift
            _t_switch_profile "$@"
            ;;
        theme)
            shift
            _t_set_theme "$@"
            ;;

        # Delegate to aiterm CLI for rich features
        ghost|ghostty)
            shift
            ait ghostty "$@"
            ;;
        switch)
            shift
            ait switch "$@"
            ;;
        detect)
            ait detect
            ;;
        doctor)
            ait terminals doctor
            ;;
        *)
            # Default: show help or delegate to ait
            if [[ -z "$1" ]]; then
                _t_help
            else
                ait "$@"
            fi
            ;;
    esac
}

# Shell-native functions (no Python, instant)
_t_set_title() {
    printf '\033]2;%s\007' "$*"
}

_t_switch_profile() {
    local profile="${1:-Default}"
    case "$TERM_PROGRAM" in
        iTerm.app)
            printf '\033]1337;SetProfile=%s\007' "$profile"
            ;;
        ghostty)
            # Ghostty doesn't support runtime profile switching
            echo "Ghostty: Use 't theme <name>' instead"
            ;;
    esac
}
```

**Pros:**
- Fits flow-cli's established dispatcher pattern
- Single-letter shortcut (`t` for terminal)
- Shell-native for speed, delegates to Python for rich features
- No duplicate code - aiterm Python CLI is authoritative

**Cons:**
- Requires coordination between repos
- Two places to document (flow-cli + aiterm)

---

### Option B: aiterm as flow-cli Plugin

**Effort:** 🏗️ Large (4-5 hours)

**What it means:** Use flow-cli's plugin system to load aiterm integration.

```
flow-cli/
└── plugins/
    └── aiterm/
        ├── plugin.json       # Plugin manifest
        └── main.zsh          # Plugin entry point
```

**Plugin manifest:**
```json
{
  "name": "aiterm",
  "version": "0.3.9",
  "description": "Terminal optimization for AI workflows",
  "requires": ["aiterm-dev"],
  "commands": ["t", "term", "ghost"],
  "hooks": ["chpwd"]
}
```

**Pros:**
- Clean separation
- Plugin can be enabled/disabled
- Version-independent updates

**Cons:**
- Plugin system complexity
- Another layer of indirection

---

### Option C: flow-cli lib/terminal.zsh

**Effort:** 🔧 Medium (2-3 hours)

**What it means:** Add `lib/terminal.zsh` library to flow-cli with terminal functions.

```
flow-cli/lib/
├── terminal.zsh              # NEW: Terminal integration library
```

**Implementation:**
```zsh
# lib/terminal.zsh
# Terminal integration - auto-loaded by flow.plugin.zsh

# Detect current terminal
_flow_terminal_detect() {
    case "$TERM_PROGRAM" in
        iTerm.app)     echo "iterm2" ;;
        ghostty)       echo "ghostty" ;;
        WezTerm)       echo "wezterm" ;;
        Apple_Terminal) echo "terminal" ;;
        *)             echo "unknown" ;;
    esac
}

# Set tab title (cross-terminal)
_flow_set_title() {
    printf '\033]2;%s\007' "$*"
}

# Context-aware profile switch
_flow_apply_context() {
    local type="${1:-$(_flow_detect_project_type)}"
    local icon=$(_flow_project_icon "$type")
    local name=$(basename "$PWD")

    # Set title
    _flow_set_title "$icon $name"

    # Terminal-specific profile switching
    case "$(_flow_terminal_detect)" in
        iterm2)
            _flow_iterm_apply "$type"
            ;;
        ghostty)
            # Delegate to aiterm for Ghostty config
            command -v ait &>/dev/null && ait switch --quiet
            ;;
    esac
}

# iTerm2-specific
_flow_iterm_apply() {
    local type="$1"
    local profile="Default"
    case "$type" in
        r-package)  profile="R-Dev" ;;
        python)     profile="Python-Dev" ;;
        node)       profile="Node-Dev" ;;
    esac
    printf '\033]1337;SetProfile=%s\007' "$profile"
}
```

**Pros:**
- Simple library pattern
- No new dispatcher needed
- Integrates with existing chpwd hook

**Cons:**
- Not exposed as user command
- Less discoverable

---

### Option D: Hybrid - Library + Dispatcher

**Effort:** 🏗️ Large (4-5 hours)

**What it means:** Combine Options A and C.

```
flow-cli/
├── lib/
│   └── terminal.zsh          # Core terminal functions
└── lib/dispatchers/
    └── t-dispatcher.zsh      # User-facing `t` command
```

The dispatcher uses the library:
```zsh
# t-dispatcher.zsh
source "$FLOW_PLUGIN_DIR/lib/terminal.zsh"

t() {
    case "$1" in
        detect)  _flow_terminal_detect ;;
        title)   shift; _flow_set_title "$@" ;;
        apply)   _flow_apply_context ;;
        *)       ait "$@" ;;
    esac
}
```

**Pros:**
- Best of both worlds
- Clean separation of concerns
- User command + internal functions

**Cons:**
- More files to maintain

---

## Recommended: Option A (Terminal Dispatcher)

Start with **Option A** because:

1. **Fits existing pattern** - flow-cli already has dispatchers (`cc`, `g`, `wt`)
2. **Minimal code** - Shell-native for fast ops, delegate to aiterm for rich features
3. **Discoverable** - Users learn `t` like they learned `cc`
4. **No duplication** - aiterm Python CLI remains the source of truth

### Implementation Plan

#### Phase 1: Create t-dispatcher (1 hour)

**File:** `flow-cli/lib/dispatchers/t-dispatcher.zsh`

```zsh
# t-dispatcher.zsh - Terminal dispatcher
# Quick terminal operations + aiterm delegation

t() {
    case "$1" in
        # Shell-native (instant, no Python)
        title|t)
            shift
            printf '\033]2;%s\007' "$*"
            ;;
        profile|p)
            shift
            _t_profile "$@"
            ;;

        # Delegate to aiterm Python CLI
        ghost|g|ghostty)
            shift
            command ait ghostty "$@"
            ;;
        switch|s)
            shift
            command ait switch "$@"
            ;;
        detect|d)
            command ait detect
            ;;
        doctor)
            command ait terminals doctor
            ;;
        status)
            command ait terminals detect
            ;;
        compare)
            command ait terminals compare
            ;;

        # Help
        help|--help|-h|"")
            _t_help
            ;;

        # Unknown → try aiterm
        *)
            if command -v ait &>/dev/null; then
                command ait "$@"
            else
                echo "Unknown command: $1"
                echo "Install aiterm: brew install data-wise/tap/aiterm"
                return 1
            fi
            ;;
    esac
}

_t_profile() {
    local profile="${1:-Default}"
    case "$TERM_PROGRAM" in
        iTerm.app)
            printf '\033]1337;SetProfile=%s\007' "$profile"
            ;;
        ghostty)
            echo "Ghostty: Profiles not supported. Use 't ghost theme <name>'"
            ;;
        *)
            echo "Terminal: $TERM_PROGRAM (profile switching not supported)"
            ;;
    esac
}

_t_help() {
    echo "
╔════════════════════════════════════════════════════════════╗
║  T - Terminal Dispatcher                                    ║
╚════════════════════════════════════════════════════════════╝

💡 QUICK START:
  $ t                     Show this help
  $ t detect              Detect current terminal
  $ t switch              Apply context to terminal

🔧 SHELL-NATIVE (instant):
  t title <text>          Set tab title
  t profile <name>        Switch iTerm2 profile

🐍 AITERM DELEGATION (rich features):
  t ghost status          Ghostty status
  t ghost theme           List/set Ghostty themes
  t switch                Apply terminal context
  t doctor                Check terminal health
  t compare               Compare terminal features

💡 SHORTCUTS:
  t = t title, p = profile, g = ghost, s = switch, d = detect

See: ait --help for full aiterm documentation
"
}

# Aliases
alias tt='t title'
alias tp='t profile'
alias tg='t ghost'
alias ts='t switch'
```

#### Phase 2: Hook Integration (30 min)

Modify `flow-cli/hooks/chpwd.zsh` to call terminal context:

```zsh
# In _flow_chpwd_hook, add:
_flow_chpwd_hook() {
    # ... existing code ...

    # Apply terminal context if aiterm available
    if command -v ait &>/dev/null; then
        ait switch --quiet 2>/dev/null
    fi
}
```

#### Phase 3: Delete aiterm's zsh (15 min)

```bash
# Remove legacy zsh from aiterm
rm aiterm/zsh/iterm2-integration.zsh
rmdir aiterm/zsh/
```

#### Phase 4: Documentation (30 min)

- Update flow-cli's README with `t` dispatcher
- Add man page: `man/man1/flow-t.1`
- Update aiterm docs to reference flow-cli integration

---

## Ownership Split After Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    OWNERSHIP AFTER INTEGRATION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FLOW-CLI                          AITERM                        │
│  ────────                          ──────                        │
│  t dispatcher (t-dispatcher.zsh)   Python CLI (ait)             │
│  Shell-native ops (title, profile) Rich terminal features        │
│  chpwd hook integration            Ghostty config management     │
│  Project detection                 Multi-terminal backends       │
│  Single-letter shortcuts           Testing & validation          │
│                                                                  │
│  DELEGATION PATTERN                                              │
│  ──────────────────                                              │
│  t ghost → ait ghostty                                          │
│  t switch → ait switch                                          │
│  t doctor → ait terminals doctor                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference After Integration

```bash
# flow-cli dispatcher (shell-native, instant)
t                    # Help
t title "Working"    # Set tab title
t profile R-Dev      # Switch iTerm2 profile (instant)

# Delegated to aiterm (Python, rich features)
t ghost              # → ait ghostty status
t ghost theme        # → ait ghostty theme list
t switch             # → ait switch
t detect             # → ait detect
t doctor             # → ait terminals doctor

# Direct aiterm (unchanged)
ait doctor           # Full diagnostic
ait claude settings  # Claude Code management
ait mcp list         # MCP server management
```

---

## Files to Create/Modify

| File | Repo | Action |
|------|------|--------|
| `lib/dispatchers/t-dispatcher.zsh` | flow-cli | Create (~100 lines) |
| `hooks/chpwd.zsh` | flow-cli | Add terminal hook (+5 lines) |
| `zsh/iterm2-integration.zsh` | aiterm | Delete (-186 lines) |
| `man/man1/flow-t.1` | flow-cli | Create (docs) |
| `CLAUDE.md` | both | Update integration notes |

**Net change:** +105 - 186 = **-81 lines** (still less code!)

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| zsh files in aiterm | 1 (186 lines) | 0 |
| Terminal dispatcher in flow-cli | 0 | 1 |
| Shell-native shortcuts | 0 | 4 (`tt`, `tp`, `tg`, `ts`) |
| Delegation to aiterm | N/A | 5 commands |

---

## Next Steps

→ **Immediate:** Create `t-dispatcher.zsh` in flow-cli
→ **After:** Add chpwd hook integration
→ **Then:** Delete aiterm's legacy zsh file
→ **v0.4.0:** Full documentation

---

*Status: Proposal*
*Target: flow-cli v3.7.0 + aiterm v0.4.0*
*Pattern: Dispatcher + Delegation*
