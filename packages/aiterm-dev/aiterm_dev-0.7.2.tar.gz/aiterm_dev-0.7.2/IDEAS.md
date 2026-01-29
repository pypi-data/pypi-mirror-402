# Ideas for aiterm

**Last Updated:** 2025-12-29
**Current Version:** v0.3.8
**Status:** 🟢 Active Development - Ghostty + flow-cli Integration

---

## 🚀 HIGH PRIORITY - Quick Wins (Dec 29, 2025)

### 1. Ghostty Aliases & Shortcuts

**Problem:** `ait ghostty status` is verbose for daily use.

**Solution:** Add shortcuts:

```bash
ait ghost           # → ait ghostty status
ait ghost theme     # → ait ghostty theme list
ait ghost config    # → ait ghostty config
```

**Implementation:** Add alias routing in `cli/main.py`

**Effort:** 15 min

---

### 2. Terminal-Aware Context Switching

**Problem:** `ait switch` should auto-detect terminal and use the right backend.

**Solution:**

```bash
ait switch          # Auto-detects iTerm2/Ghostty, applies best profile
ait switch --force iterm2   # Override detection
```

**Implementation:** Modify `cli/context.py` to call terminal detection first.

**Effort:** 30 min

---

### 3. Add `ait terminals doctor`

**Problem:** No easy way to check terminal integration health.

**Solution:**

```bash
ait terminals doctor           # Check all terminal configs
ait terminals doctor ghostty   # Check specific terminal
ait terminals doctor --fix     # Attempt auto-fix (like flow doctor)
```

**Checks:**
- Config file exists and is valid
- Required settings present
- Theme files accessible
- Escape sequences working

**Effort:** 1 hour

---

### 4. Match flow-cli Help Style

**Problem:** aiterm uses standard typer `--help`, flow-cli has ADHD-friendly format.

**flow-cli pattern:**
```
╭─────────────────────────────────────────────────╮
│  🎯 COMMAND NAME                                │
╰─────────────────────────────────────────────────╯

MOST COMMON:
  command arg     Description of what it does

QUICK EXAMPLES:
  $ command foo   Do the foo thing
  $ command bar   Do the bar thing

See also: man command, related-command
```

**Solution:** Add custom epilog to all commands with flow-cli style formatting.

**Effort:** 1-2 hours (19 commands)

---

## 📋 MEDIUM PRIORITY - flow-cli Integration

### M1: Cross-Terminal Context Sync

**Problem:** Context detection works per-terminal, but users might have multiple terminals open.

**Solution:**

```bash
ait context sync       # Broadcast context to all open terminals
ait context --global   # Set system-wide context
```

**Implementation:** Write to `~/.config/aiterm/context.json`, terminals poll or watch.

**Effort:** 2 hours

---

### M2: flow-cli Complement Commands

**Add aiterm commands that enhance flow-cli workflows:**

| aiterm command | flow-cli equivalent | Purpose |
|----------------|---------------------|---------|
| `ait work <project>` | `work <project>` | Visual terminal setup |
| `ait finish` | `finish` | Terminal cleanup + reset |
| `ait hop <project>` | `hop <project>` | Quick switch with terminal context |

**Implementation:** Call flow-cli, then apply terminal profile.

**Effort:** 2 hours

---

### M3: Terminal Recipe Templates

**Idea:** Let users define terminal presets for workflows.

```yaml
# ~/.config/aiterm/recipes/deep-work.yml
name: Deep Work
terminal:
  theme: dracula
  font_size: 16
  opacity: 0.95
context:
  profile: ai-session
  title_prefix: "🎯"
triggers:
  - pattern: "*/research/*"
  - pattern: "*/writing/*"
```

```bash
ait recipes apply deep-work
ait recipes list
ait recipes create
```

**Effort:** 3 hours

---

### M4: Extend Doctor for Terminals

**Add terminal-specific health checks to `ait doctor`:**

```bash
ait doctor --terminal ghostty    # Check Ghostty config
ait doctor --terminal iterm2     # Check iTerm2 profiles
ait doctor --all                 # Full system check including terminals
```

**Effort:** 1.5 hours

---

## 🔮 FUTURE - Long-term Vision

### L1: Unified Shell Integration

**Vision:** Single `work` command that does everything:

```bash
work aiterm    # flow-cli: session start
               # aiterm: terminal profile + tab title
               # Claude Code: auto-launch if configured
```

**Implementation in flow-cli (work.zsh):**
```zsh
# At end of work() function
if command -v ait &>/dev/null; then
  ait switch --quiet  # Apply terminal context
fi
```

**Dependencies:** Requires coordination with flow-cli maintainer (same person!)

---

### L2: Man Pages for aiterm

**Follow flow-cli pattern:**

| Man Page | Content |
|----------|---------|
| `man ait` | Main command overview |
| `man ait-ghostty` | Ghostty-specific documentation |
| `man ait-claude` | Claude Code integration |
| `man ait-context` | Context detection details |

**Location:** `man/man1/`

**Effort:** 4 hours

---

### L3: Interactive TUI Mode

**Like flow-cli's `dash -i` but for terminal management:**

```bash
ait tui        # Interactive terminal management
```

**Features:**
- Theme picker with live preview
- Font size slider
- Context quick-switch grid
- Session overview panel
- Keyboard shortcuts (vim-style)

**Tech:** textual or blessed

**Effort:** 8+ hours

---

### L4: Workflow Enforcement Integration

**Sync with flow-cli Priority 0 (Workflow Enforcement):**

| flow-cli | aiterm | Purpose |
|----------|--------|---------|
| `g feature <name>` | `ait workflows branch-status` | Visual branch position |
| `_g_check_workflow()` | `ait workflows violations` | View violation history |
| pre-push hook | `ait workflows enforce --install` | Install shared hook |

**Status:** Phase 1d in V0.4.0-PLAN.md (waiting for flow-cli)

---

## ✅ COMPLETED

### Ghostty Terminal Support (Dec 29, 2025)

- [x] Terminal detection (6 terminals)
- [x] Ghostty backend (250 lines)
- [x] Ghostty CLI commands (280 lines)
- [x] 14 built-in themes
- [x] Config parsing and writing
- [x] Tab title support
- [x] 19 tests passing
- [x] Documentation (terminals.md)

---

## Implementation Priority

### Phase 1: Quick Wins (v0.3.9)
1. ⚡ Ghost aliases (15 min)
2. ⚡ Terminal-aware switch (30 min)
3. ⚡ Terminals doctor (1 hour)
4. ⚡ Help style update (2 hours)

### Phase 2: flow-cli Integration (v0.4.0)
1. 📋 Doctor --terminal extension
2. 📋 flow-cli complement commands
3. 📋 Terminal recipe templates

### Phase 3: Long-term (v0.5.0+)
1. 🔮 Unified shell integration
2. 🔮 Man pages
3. 🔮 Interactive TUI
4. 🔮 Workflow enforcement

---

## flow-cli Patterns to Adopt

Based on analysis of `~/projects/dev-tools/flow-cli/`:

1. **Help format**: Box-drawing chars, "MOST COMMON" section, colored output
2. **Doctor pattern**: Category checks, `--fix` flag, `--ai` troubleshooting
3. **Dispatcher model**: Single-letter shortcuts (`g`, `r`, `cc`)
4. **Command structure**: Clear argument parsing with `while [[ $# -gt 0 ]]`
5. **Man pages**: Comprehensive documentation in `man/man1/`

---

## Links

- **Repo:** https://github.com/Data-Wise/aiterm
- **Docs:** https://Data-Wise.github.io/aiterm/
- **flow-cli:** https://github.com/Data-Wise/flow-cli
