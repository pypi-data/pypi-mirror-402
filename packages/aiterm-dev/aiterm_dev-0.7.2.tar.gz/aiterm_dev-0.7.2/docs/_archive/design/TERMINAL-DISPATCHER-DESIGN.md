# Terminal Dispatcher Design Document

**Created:** 2025-12-29
**Status:** Draft
**Topic:** Naming, research, and sync mechanism for aiterm ↔ flow-cli integration

---

## 1. Naming Alternatives to `t`

### Analysis of flow-cli Existing Dispatchers

| Dispatcher | Length | Pattern |
|------------|--------|---------|
| `cc` | 2 | Initials (Claude Code) |
| `wt` | 2 | Abbreviation (worktree) |
| `qu` | 2 | Abbreviation (Quarto) |
| `g` | 1 | Single letter (git) |
| `r` | 1 | Single letter (R language) |
| `mcp` | 3 | Acronym |
| `ai` | 2 | Already used (flow_ai) |

### Two-Letter Alternatives

| Name | Meaning | Pros | Cons |
|------|---------|------|------|
| **`tm`** | Terminal | Familiar (like tmux) | Conflicts with tmux muscle memory |
| **`te`** | Terminal Emulator | Clear meaning | Less intuitive |
| **`ti`** | Terminal Integration | Descriptive | Not memorable |
| **`tx`** | Terminal eXtension | Unique | Arbitrary 'x' |
| **`at`** | **aiterm** | Matches project name! | Conflicts with `at` scheduler? |

### Recommendation: `tm` or `at`

**Option 1: `tm` (terminal)**
```bash
tm                    # Help
tm title "Working"    # Set title
tm ghost theme        # Ghostty theme
tm switch             # Apply context
```

**Option 2: `at` (aiterm)**
```bash
at                    # Help
at title "Working"    # Set title
at ghost theme        # Ghostty theme
at switch             # Apply context
```

### Conflict Check

```bash
# Check if 'at' conflicts with anything
which at              # /usr/bin/at (job scheduler)
which tm              # (nothing - safe!)
```

**Verdict:** `tm` is safer (no conflicts). `at` is more memorable but shadows the `at` scheduler.

### Final Recommendation: **`tm`**

- **Mnemonic:** "Terminal Manager" or "Terminal Mode"
- **No conflicts** with existing commands
- **Two letters** as requested
- **Consistent** with `wt`, `cc`, `qu` pattern

---

## 2. Research: Shell Integration Patterns

### 2.1 Oh-My-Zsh Plugin Architecture

**Source:** [Oh-My-Zsh GitHub](https://github.com/ohmyzsh/ohmyzsh)

**Key patterns:**
- Plugins live in `~/.oh-my-zsh/custom/plugins/<name>/`
- Entry point: `<name>.plugin.zsh`
- Plugins are sourced in order from `plugins=()` array
- Custom plugins require manual `git pull` for updates

**Lesson for flow-cli:**
- flow-cli already follows a similar pattern with `plugins/` directory
- Use `plugin-loader.zsh` for managed loading

### 2.2 Zim Framework (Performance-Focused)

**Source:** [Zim Framework](https://github.com/zimfw/zimfw)

**Key patterns:**
- Modules are installed via `zimfw install`
- Generates static `init.zsh` to minimize startup
- Async loading for heavy modules

**Lesson for flow-cli:**
- Consider pre-generating dispatcher list for faster startup
- Async loading not needed (dispatchers are lightweight)

### 2.3 iTerm2 Shell Integration

**Source:** [iTerm2 Escape Codes](https://iterm2.com/documentation-escape-codes.html)

**Key escape sequences:**

| Sequence | Purpose |
|----------|---------|
| `OSC 1337;SetProfile=NAME ST` | Switch profile |
| `OSC 1337;SetUserVar=key=BASE64 ST` | Set status bar variable |
| `OSC 2;TITLE ST` | Set window/tab title |
| `OSC 7;file://HOST/PATH ST` | Report CWD |
| `OSC 133;A ST` through `D` | FinalTerm prompt marking |

**Lesson for aiterm:**
- Use standardized escape sequences where possible
- iTerm2-specific features should degrade gracefully

### 2.4 Ghostty Shell Integration

**Source:** [Ghostty Shell Integration](https://ghostty.org/docs/features/shell-integration)

**Key features:**
- Auto-injects shell integration for bash/zsh/fish/elvish
- Uses `GHOSTTY_SHELL_FEATURES` environment variable
- OSC 133 for semantic prompt markup
- OSC 7 for CWD reporting (kitty-shell-cwd protocol)
- OSC 2 for window title

**Lesson for aiterm:**
- Check `GHOSTTY_SHELL_FEATURES` before setting title
- Use OSC 2 (cross-terminal) instead of iTerm2-specific
- Respect tmux detection (wrap sequences appropriately)

### 2.5 VS Code Terminal Shell Integration

**Source:** [VS Code Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration)

**Key patterns:**
- Conditional sourcing: `[[ "$TERM_PROGRAM" == "vscode" ]] && source ...`
- Exit code detection via escape sequences
- Command history navigation

**Lesson for flow-cli:**
- Check `TERM_PROGRAM` before applying terminal-specific features

---

## 3. Sync Mechanism: aiterm ↔ flow-cli

### 3.1 Options Analysis

| Approach | Complexity | Sync Effort | Versioning |
|----------|------------|-------------|------------|
| **Git submodule** | High | Manual `git pull` | Pinned to commit |
| **Symlink** | Low | Automatic | Always latest |
| **Package (Homebrew)** | Medium | `brew upgrade` | Versioned |
| **Copy + release** | Low | Manual copy | Versioned |
| **flow-cli plugin** | Medium | `flow plugin update` | Plugin version |

### 3.2 Recommended: Symlink + Homebrew Fallback

**Primary mechanism: Symlink**

```
flow-cli/
└── zsh/functions/
    └── aiterm-integration.zsh → ~/projects/dev-tools/aiterm/flow-integration/aiterm.zsh
```

flow-cli already supports this pattern (line 62-66 of `flow.plugin.zsh`):
```zsh
# Load symlinked integrations if they exist and resolve
for fn_file in "$FLOW_PLUGIN_DIR/zsh/functions/"*.zsh(N); do
  if [[ -L "$fn_file" ]] && [[ -e "$fn_file" ]]; then
    source "$fn_file"
  fi
done
```

**Fallback: Homebrew dependency**

```ruby
# In flow-cli Homebrew formula (future)
depends_on "data-wise/tap/aiterm" => :optional
```

### 3.3 Implementation: Symlink Setup

**File to create in aiterm:**
```
aiterm/
└── flow-integration/
    ├── aiterm.zsh            # Main integration (tm dispatcher)
    └── install-symlink.sh    # Setup script
```

**aiterm.zsh content:**
```zsh
# flow-integration/aiterm.zsh
# Terminal dispatcher for flow-cli
# Symlink to: flow-cli/zsh/functions/aiterm-integration.zsh

# Check aiterm is installed
if ! command -v ait &>/dev/null; then
    _tm_not_installed() {
        echo "aiterm not installed. Install: brew install data-wise/tap/aiterm"
    }
    alias tm='_tm_not_installed'
    return
fi

# Main dispatcher
tm() {
    case "$1" in
        title|t)  shift; printf '\033]2;%s\007' "$*" ;;
        profile|p) shift; _tm_profile "$@" ;;
        ghost|g)  shift; command ait ghostty "$@" ;;
        switch|s) shift; command ait switch "$@" ;;
        detect|d) command ait detect ;;
        doctor)   command ait terminals doctor ;;
        help|--help|-h|"") _tm_help ;;
        *)        command ait "$@" ;;
    esac
}

_tm_profile() {
    local profile="${1:-Default}"
    case "$TERM_PROGRAM" in
        iTerm.app)
            printf '\033]1337;SetProfile=%s\007' "$profile"
            ;;
        ghostty)
            echo "Ghostty: Use 'tm ghost theme <name>' instead"
            ;;
        *)
            echo "Profile switching not supported for $TERM_PROGRAM"
            ;;
    esac
}

_tm_help() {
    echo "
╔════════════════════════════════════════════════════════════╗
║  TM - Terminal Manager (aiterm integration)                 ║
╚════════════════════════════════════════════════════════════╝

💡 QUICK:
  tm                     Show this help
  tm detect              Detect current terminal
  tm switch              Apply context to terminal

🔧 SHELL-NATIVE (instant):
  tm title <text>        Set tab title
  tm profile <name>      Switch iTerm2 profile

🐍 AITERM DELEGATION:
  tm ghost status        Ghostty status
  tm ghost theme         List/set Ghostty themes
  tm doctor              Check terminal health

See: ait --help for full documentation
"
}

# Aliases
alias tmt='tm title'
alias tmp='tm profile'
alias tmg='tm ghost'
alias tms='tm switch'
```

**install-symlink.sh:**
```bash
#!/bin/bash
# Install aiterm integration into flow-cli

AITERM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLOW_DIR="${FLOW_PLUGIN_DIR:-$HOME/projects/dev-tools/flow-cli}"

if [[ ! -d "$FLOW_DIR" ]]; then
    echo "flow-cli not found at $FLOW_DIR"
    echo "Set FLOW_PLUGIN_DIR to your flow-cli location"
    exit 1
fi

TARGET="$FLOW_DIR/zsh/functions/aiterm-integration.zsh"
SOURCE="$AITERM_DIR/flow-integration/aiterm.zsh"

mkdir -p "$(dirname "$TARGET")"
ln -sf "$SOURCE" "$TARGET"
echo "✓ Symlinked: $TARGET → $SOURCE"
echo "Restart shell or run: source ~/.zshrc"
```

### 3.4 Keeping Up with flow-cli Changes

**Option A: Watch for releases (manual)**
```bash
# In aiterm, check flow-cli version compatibility
FLOW_MIN_VERSION="3.6.0"
if [[ "$FLOW_VERSION" < "$FLOW_MIN_VERSION" ]]; then
    echo "Warning: flow-cli $FLOW_VERSION may not support aiterm integration"
fi
```

**Option B: GitHub Actions notification**
```yaml
# .github/workflows/check-flow-cli.yml
name: Check flow-cli compatibility
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check flow-cli releases
        run: |
          LATEST=$(gh release list -R Data-Wise/flow-cli -L1 --json tagName -q '.[0].tagName')
          echo "Latest flow-cli: $LATEST"
          # Compare with FLOW_MIN_VERSION in aiterm
```

**Option C: Version pinning in aiterm**
```zsh
# In aiterm.zsh
AITERM_FLOW_TESTED_VERSION="3.7.0"

if [[ -n "$FLOW_VERSION" ]]; then
    if [[ "$FLOW_VERSION" != "$AITERM_FLOW_TESTED_VERSION" ]]; then
        _flow_log_debug "aiterm: tested with flow-cli $AITERM_FLOW_TESTED_VERSION, found $FLOW_VERSION"
    fi
fi
```

### 3.5 Recommended Sync Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYNC STRATEGY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DEVELOPMENT (symlink)                                          │
│  ─────────────────────                                          │
│  flow-cli/zsh/functions/aiterm-integration.zsh                  │
│       ↓ symlink                                                 │
│  aiterm/flow-integration/aiterm.zsh                             │
│                                                                  │
│  • Changes in aiterm immediately available in flow-cli          │
│  • No copy/sync needed during development                       │
│  • Version check warns on mismatch                              │
│                                                                  │
│  DISTRIBUTION (Homebrew)                                        │
│  ───────────────────────                                        │
│  1. User installs: brew install flow-cli aiterm                 │
│  2. aiterm post-install creates symlink                         │
│  3. Updates: brew upgrade aiterm                                │
│                                                                  │
│  COMPATIBILITY                                                   │
│  ─────────────                                                  │
│  • aiterm.zsh checks FLOW_VERSION                               │
│  • Warns if flow-cli is too old                                 │
│  • Falls back gracefully (just uses ait directly)               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Cross-Terminal Escape Sequence Reference

### 4.1 Universal Sequences (Work Everywhere)

| Sequence | Purpose | Terminals |
|----------|---------|-----------|
| `\033]2;TITLE\007` | Set window/tab title | All |
| `\033]0;TITLE\007` | Set icon + window title | All |
| `\033]7;file://HOST/PATH\007` | Report CWD | iTerm2, Ghostty, kitty |

### 4.2 iTerm2-Specific

| Sequence | Purpose |
|----------|---------|
| `\033]1337;SetProfile=NAME\007` | Switch profile |
| `\033]1337;SetUserVar=key=BASE64\007` | Status bar variable |
| `\033]1337;File=...` | Inline images |

### 4.3 Ghostty-Specific

| Sequence | Purpose |
|----------|---------|
| Uses standard OSC 2, 7, 133 | No proprietary sequences |
| `GHOSTTY_SHELL_FEATURES` env | Feature detection |

### 4.4 Detection Pattern

```zsh
_tm_detect_terminal() {
    case "$TERM_PROGRAM" in
        iTerm.app)     echo "iterm2" ;;
        ghostty)       echo "ghostty" ;;
        WezTerm)       echo "wezterm" ;;
        Apple_Terminal) echo "terminal" ;;
        vscode)        echo "vscode" ;;
        *)
            if [[ -n "$KITTY_WINDOW_ID" ]]; then
                echo "kitty"
            elif [[ -n "$ALACRITTY_WINDOW_ID" ]]; then
                echo "alacritty"
            else
                echo "unknown"
            fi
            ;;
    esac
}
```

---

## 5. Implementation Checklist

### Phase 1: Create Integration (aiterm side)

- [ ] Create `aiterm/flow-integration/` directory
- [ ] Create `aiterm.zsh` with `tm` dispatcher
- [ ] Create `install-symlink.sh`
- [ ] Add version compatibility check
- [ ] Test with flow-cli v3.6.0

### Phase 2: Documentation

- [ ] Add installation instructions to aiterm docs
- [ ] Create man page (`man flow-tm`)
- [ ] Update CLAUDE.md in both repos

### Phase 3: Distribution

- [ ] Update aiterm Homebrew formula with post-install symlink
- [ ] Add `tm` to flow-cli's dispatcher list documentation
- [ ] Release aiterm v0.4.0 with flow-cli integration

### Phase 4: Maintenance

- [ ] Set up GitHub Action to check flow-cli releases
- [ ] Document version compatibility matrix
- [ ] Add integration tests

---

## References

- [Oh-My-Zsh](https://github.com/ohmyzsh/ohmyzsh) - Plugin architecture
- [Zim Framework](https://github.com/zimfw/zimfw) - Performance patterns
- [iTerm2 Escape Codes](https://iterm2.com/documentation-escape-codes.html) - Proprietary sequences
- [Ghostty Shell Integration](https://ghostty.org/docs/features/shell-integration) - Modern terminal patterns
- [VS Code Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration) - IDE integration
- [Git Submodules Guide](https://www.aviator.co/blog/managing-repositories-with-git-submodules/) - Dependency management
- [5 Ways to Share Code](https://medium.com/hackernoon/5-practical-ways-to-share-code-from-npm-to-lerna-and-bit-732f2a4db512) - Code sharing patterns

---

*Document: TERMINAL-DISPATCHER-DESIGN.md*
*Version: 1.0*
*Author: Claude + DT*
