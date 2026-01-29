# Brainstorm: Improving `ait statusline` Command UX

**Date:** 2026-01-17
**Focus:** Simplify command structure + reduce configuration complexity
**User Feedback:** Too many ways to configure (CLI/wizard/editor/preset)
**Preference:** Interactive exploration over direct CLI flags
**Claude Code v2.1:** Support hooks templates, auto-register, validation

---

## Current State Analysis

### The Problem: Configuration Paradox

Users have **too many ways** to configure statusline:

```bash
# Way 1: Direct CLI (requires knowing all keys)
ait statusline config set display.show_git false

# Way 2: Interactive fzf menu (hard to discover)
ait statusline config set --interactive

# Way 3: Wizard (limited scope, 5 questions)
ait statusline config wizard

# Way 4: Raw editor (risky, complex JSON)
ait statusline config edit

# Way 5: Presets (only 2 options: minimal/default)
ait statusline config preset minimal

# Way 6: Spacing (separate command, inconsistent)
ait statusline config spacing standard

# Way 7: Themes (different pattern than config)
ait statusline theme set cool-blues
```

**Result:** New users don't know where to start. Power users find it scattered.

**Why it happened:** Features added incrementally without unified mental model.

---

## Quick Wins (< 30 min each)

### 1. ⚡ Create Unified Config Gateway Command

**What:** Single entry point that routes to best tool for the task

**Current:** Multiple commands (config, theme, spacing) with no discovery

**Proposed:**
```bash
ait statusline setup
→ Smart gateway that asks: "What do you want to do?"
  • Customize display (git, time, etc.)
  • Change theme
  • Adjust spacing
  • Apply preset (minimal/standard/spacious)
  • See what's available
  • Edit raw config

→ Routes to appropriate subcommand or wizard
```

**Why this works:**
- Single entry point (`setup` is intuitive)
- Discovers all options
- No guessing which command to use
- Progressive disclosure (simple Q → specific tool)

**Implementation:**
```python
@app.command("setup")
def statusline_setup():
    """Quick gateway to statusline customization.

    Single command for:
    - Visual customization (display options)
    - Theme selection
    - Spacing adjustment
    - Preset application
    - Advanced editing
    """
    console.print("[bold]StatusLine Configuration[/]\n")

    AskUserQuestion(
        question="What would you like to customize?",
        options=[
            "Display options (git, time, session info)",
            "Color theme",
            "Spacing between left/right",
            "Apply a preset (minimal/standard/spacious)",
            "View all settings",
            "Edit raw config file"
        ]
    )
    # Route to appropriate subcommand based on choice
```

**Effort:** 30 min
**Impact:** High (major UX improvement)
**Files:** Add 1 new command in statusline.py (40 lines)

---

### 2. ⚡ Add Hook Templates for StatusLine

**What:** Pre-built hook examples for statusline customization (Claude Code v2.1)

**Current:** No hooks support, statusline is static

**Proposed:**
```bash
ait statusline hooks list
→ Shows available hook templates:
  • On-theme-change: Auto-update colors on terminal theme change
  • On-remote-session: Auto-enable remote indicator for /teleport
  • On-error: Show alert when statusline rendering fails

ait statusline hooks add on-theme-change
→ Installs hook to ~/.claude/hooks/statusline-theme-watch.sh
→ Registers in claude settings
→ Validates syntax
```

**Why v2.1 hooks matter:**
- Hooks can watch for statusline errors
- Hooks can auto-detect remote sessions
- Hooks can trigger on model changes
- Opens door for "smart statusline"

**Implementation:**
```python
# New file: src/aiterm/statusline/hooks.py
class StatusLineHooks:
    TEMPLATES = {
        "on-theme-change": {
            "description": "Auto-update statusline when terminal theme changes",
            "hook_type": "PostToolUse",
            "content": "...bash script..."
        },
        "on-remote-session": {
            "description": "Enable remote indicator when using /teleport",
            "hook_type": "PreToolUse",
            "content": "...bash script..."
        },
        "on-error": {
            "description": "Alert when statusline rendering fails",
            "hook_type": "PostToolUse",
            "content": "...bash script..."
        }
    }

@app.command("hooks")
def statusline_hooks():
    """Manage statusline hooks (Claude Code v2.1+)."""
```

**Effort:** 1 hour
**Impact:** High (leverages v2.1 features)
**Files:** New hooks.py (150 lines) + CLI in statusline.py (50 lines)

---

### 3. ⚡ Improved Help Discovery

**What:** Better `ait statusline help` and inline hints

**Current:**
```bash
ait statusline help
→ Shows basic help, doesn't guide users
```

**Proposed:**
```bash
ait statusline help
→ Shows interactive help with:
  1. Quick start (3 steps)
  2. Common tasks (organize by goal, not command)
  3. Advanced features (hooks, presets)
  4. Troubleshooting

ait statusline help --task "change theme"
→ Shows theme setup steps
```

**Why this works:**
- Organized by user goals, not commands
- Reduces command memorization
- Examples for each task

**Implementation:**
```python
HELP_TOPICS = {
    "quick-start": ["install", "test", "done"],
    "change-theme": ["theme list", "theme set cool-blues", "theme show"],
    "customize-display": ["config wizard", "config preset minimal"],
    "advanced": ["config edit", "hooks list", "doctor"],
}

@app.command("help")
def statusline_help(
    task: Optional[str] = typer.Option(None, "--task", "-t")
):
    """Interactive help system."""
```

**Effort:** 30 min
**Impact:** Medium (documentation, not code)
**Files:** New help.py (100 lines) + reference in CLI

---

## Medium Effort (1-2 hours)

### 4. 🔧 Consolidate Theme + Config + Spacing into Single Menu

**What:** Single "customize" command that handles all display options

**Current:** 3 separate command families
```bash
ait statusline config spacing ...
ait statusline theme set ...
ait statusline config set ...
```

**Proposed:**
```bash
ait statusline customize
→ Opens interactive menu with all options:

  [Display Settings]
  ☐ Show git status (enabled)
  ☐ Show session time (disabled)
  ☐ Show lines changed (enabled)
  ...

  [Theme]
  Current: purple-charcoal
  Available: cool-blues, forest-greens, ...

  [Spacing]
  Current: standard (20% gap)
  Presets: minimal, standard, spacious

  [Advanced]
  Edit raw | Reset defaults | Load preset
```

**Why single menu:**
- Everything visible in one place
- No jumping between commands
- Progressive disclosure (details on demand)
- Matches user's mental model: "customize statusline"

**Implementation:**
```python
class StatusLineCustomizeMenu:
    """Unified customization interface."""

    def __init__(self, config: StatusLineConfig):
        self.config = config
        self.sections = [
            DisplaySection(config),
            ThemeSection(config),
            SpacingSection(config),
            AdvancedSection(config)
        ]

    def run(self):
        """Show all options, let user browse and change."""
```

**Effort:** 1-2 hours
**Impact:** High (major UX simplification)
**Files:** New customize.py (250 lines) + integration in CLI

---

### 5. 🔧 Smart Help Inline During Setup

**What:** Context-aware hints while configuring

**Current:**
```bash
ait statusline config wizard
Q: "Do you want to show git status?"
User: [confused]
```

**Proposed:**
```bash
ait statusline setup  # OR: customize
Q: "Show git information in statusline?"

   💡 Tip: Displays branch, ahead/behind, stash count
   This is useful if you frequently switch branches

   ○ Yes (Recommended)
   ○ No
   ○ Learn more (explains each git indicator)
```

**Why inline hints:**
- Users understand what each option does
- No need to read docs separately
- "Learn more" link for details
- Progressive disclosure

**Implementation:**
- Add `description` and `hint` to schema
- Display hints in wizard/customize flow

**Effort:** 1 hour
**Impact:** Medium (UX improvement)
**Files:** Update config.py schema + CLI

---

### 6. 🔧 Add Hook Validation in Install

**What:** Warn if hooks exist and could conflict with statusline

**Current:**
```bash
ait statusline install
→ Installs, doesn't check for existing hooks
```

**Proposed:**
```bash
ait statusline install

[Checking hooks compatibility...]
  ⚠ Found: session-register.sh (CloudCode hook - OK)
  ⚠ Found: my-custom-hook.sh (could interfere with statusline)

[green]✓[/] Installation ready!

Hooks detected: 2 (no conflicts)
```

**Why validation:**
- Prevents subtle conflicts
- Users understand hook impact
- Safe auto-register of statusline hooks

**Implementation:**
```python
def validate_hooks_compat() -> Tuple[List[str], List[str]]:
    """Returns (safe_hooks, conflicting_hooks)."""
```

**Effort:** 1 hour
**Impact:** Medium (safety/education)
**Files:** Update install command + new validation.py

---

## Long-term (Future sessions)

### 7. 🏗️ Command Aliases for Power Users

**What:** Short aliases for common operations

```bash
# Current
ait statusline config set display.show_git false

# Proposed aliases
ait statusline git off        # Toggle git
ait statusline time on        # Toggle time
ait statusline theme blues    # Set theme
ait statusline space tight    # Set spacing
```

**Why defer:**
- Phase 1 should focus on discovery/simplification
- Aliases benefit power users after core UX is solid
- Can add later without breaking existing commands

---

### 8. 🏗️ Settings Profiles (Situation-Based)

**What:** Save/load configs for different contexts

```bash
ait statusline profile save teaching
→ Saves current config as "teaching" profile

ait statusline profile load teaching
→ Restores "teaching" config

ait statusline profile list
→ Shows available profiles
```

**Use cases:**
- teaching: Minimal, clean for demos
- deep-work: Full info, verbose
- pair-programming: Show extra collaboration signals
- remote: Remote-optimized indicators

**Why defer:**
- Requires profile storage infrastructure
- Better to add after core UX solidified

---

## Updated Review Recommendations

Based on command UX analysis:

### **Highest Priority (Add These)**

1. **⚡ Unified Config Gateway (`ait statusline setup`)**
   - Single entry point
   - Routes to appropriate tool
   - Solves discovery problem
   - 30 min effort

2. **⚡ Hook Templates (v2.1 Integration)**
   - Pre-built hooks for statusline
   - Auto-register during install
   - Validate syntax
   - Leverage new Claude Code features

3. **⚡ Interactive Menu Consolidation (`ait statusline customize`)**
   - Unified display/theme/spacing menu
   - Everything in one place
   - Replace scattered commands
   - 1-2 hours effort

### **Remove These (Reduce Complexity)**

- `ait statusline config spacing` → Move into unified menu
- Separate `theme` commands → Move into unified menu
- Multiple config methods → Route through `setup` gateway

### **Keep These (They Work)**

- `ait statusline install` → Still needed
- `ait statusline test` → Useful for previewing
- `ait statusline doctor` → Good for debugging
- `ait statusline render` → Internal, still needed

---

## Architecture Pattern: Gateway Pattern

**Problem:** Multiple ways to do the same thing
**Solution:** Single gateway that routes to specialized tools

```
User: ait statusline setup
        ↓
    [Gateway]
        ↓
    ┌───┴───────┬────────┬────────┐
    ↓           ↓        ↓        ↓
  Display     Theme    Spacing  Advanced
  Settings    Menu     Menu      Menu
    ↓           ↓        ↓        ↓
  wizard      set     preset    editor
```

**Benefits:**
- Single entry point
- User doesn't need to know all commands
- Easy to discover
- Can route to best tool for task

---

## Implementation Priority

### Phase 1: Command Unification (This sprint)
- [ ] Add `ait statusline setup` gateway
- [ ] Add `ait statusline customize` unified menu
- [ ] Improve `ait statusline help`
- **Effort:** 2 hours
- **Impact:** Solves "too many ways to configure" problem

### Phase 2: v2.1 Integration (Next sprint)
- [ ] Add hook templates
- [ ] Add hook validation in install
- [ ] Auto-register hooks
- **Effort:** 2 hours
- **Impact:** Leverage Claude Code v2.1 features

### Phase 3: Advanced Features (Later)
- [ ] Settings profiles
- [ ] Command aliases for power users
- **Effort:** TBD
- **Impact:** Power user features

---

## Command Mapping: Old → New

This helps preserve discoverability while unifying UX:

| Old Command | Behavior | Migration |
|---|---|---|
| `ait statusline config preset X` | Apply preset | Still works + routed through setup/customize |
| `ait statusline config set K V` | Set value | Still works + accessible via customize menu |
| `ait statusline config wizard` | Interactive setup | Integrated into setup → customize flow |
| `ait statusline theme set X` | Change theme | Moved into customize menu |
| `ait statusline config spacing X` | Change spacing | Moved into customize menu |

**All old commands still work** (backward compatible), but `setup` is the recommended path.

---

## Visual Mockup: New Flow

```
ait statusline
├── install          # First time: get statusline in Claude Code
├── setup            # NEW: Gateway to all customization
│   ├── → customize  # Unified interactive menu
│   ├── → help       # Interactive help
│   └── → hooks      # NEW: Manage hooks
├── test             # Preview with mock data
├── doctor           # Diagnose issues
└── render           # Internal (called by Claude Code)

# Legacy (still work, but users guided to setup)
├── config.*         # All still work for backward compat
├── theme.*          # Routes to setup/customize
└── hooks.*          # NEW family of commands
```

---

## User Journey: Before vs After

### BEFORE (Confusing)

```
User: I want to change my statusline

"Should I use 'ait statusline config'?
Or 'ait statusline wizard'?
Or 'ait statusline theme set'?
Or 'ait statusline config spacing'?"

→ Tries 'ait statusline help'
→ Shows all commands but no guidance
→ Gets confused, gives up
```

### AFTER (Clear)

```
User: I want to change my statusline

$ ait statusline setup

[Menu]
What would you like to do?
• Customize display (git, time, etc.)
• Change theme
• Adjust spacing
• See presets
• Advanced

→ User selects "Customize display"
→ Opens friendly menu with options
→ Saves changes
→ Done
```

---

## Conclusion

The statusline command has **too many entry points** for a simple task. The solution isn't more commands—it's **fewer, smarter entry points**.

**Three changes solve the core problem:**

1. **`ait statusline setup`** - Single gateway
2. **`ait statusline customize`** - Unified menu
3. **Hook templates** - Leverage v2.1

This reduces the mental model from:
- "Which command should I use?" (7 options)

To:
- "Use `setup`, it guides you" (1 option)

---

## Files to Modify

| File | Change | Effort |
|---|---|---|
| `src/aiterm/cli/statusline.py` | Add setup, customize, help commands | 2 hours |
| `src/aiterm/statusline/hooks.py` | NEW: Hook templates | 1 hour |
| `src/aiterm/statusline/interactive.py` | Enhance menu system | 1 hour |
| `src/aiterm/statusline/config.py` | Add hints/descriptions | 30 min |
| `tests/test_statusline_cli.py` | Add 15+ new tests | 1 hour |
| `docs/guide/statusline.md` | Update with setup/customize | 30 min |

**Total Phase 1 Effort:** 5-6 hours

---

## Success Metrics

✅ New users can configure statusline in < 2 minutes (vs 10+ now)
✅ Help system answers "what should I do?" (not just "what commands exist?")
✅ Hooks integration enables smart statusline features
✅ Command count visible to users: reduced from 7 to 2-3
✅ All old commands still work (backward compatible)

