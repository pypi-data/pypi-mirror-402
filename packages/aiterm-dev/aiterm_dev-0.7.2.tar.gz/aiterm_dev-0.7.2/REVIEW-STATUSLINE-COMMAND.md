# Review: aiterm StatusLine Command Structure

**Date:** 2026-01-17
**Scope:** `ait statusline` CLI and integration with Claude Code
**Status:** Production v0.7.2 (Ghostty 1.2.x support)

---

## Executive Summary

The `ait statusline` command provides a well-architected, user-friendly system for managing Claude Code status line configuration. The design follows good CLI principles with clear separation of concerns and a progressive disclosure approach for users.

**Overall Assessment:** ✅ **Well-designed** with minor UX opportunities

---

## Architecture Overview

### Command Structure

```
ait statusline
├── install              # Update Claude Code settings.json
├── test                 # Preview with mock data
├── doctor               # Validate setup
├── render               # Render output (called by Claude Code)
├── config               # Configuration management
│   ├── list             # Show all settings
│   ├── get              # Get single value
│   ├── set              # Set value (interactive or direct)
│   ├── reset            # Reset to defaults
│   ├── edit             # Open in $EDITOR
│   ├── wizard           # Interactive setup
│   ├── validate         # Check config validity
│   ├── preset           # Apply presets (minimal/default)
│   └── spacing          # Gap spacing presets
└── theme                # Theme management
    ├── list             # Show available themes
    ├── set              # Activate theme
    └── show             # Display theme colors
```

### Data Flow

```
Claude Code (stdin/JSON)
         ↓
[render command]  ← Called by statusLine.command in settings.json
         ↓
StatusLineRenderer
         ↓
[reads config] → StatusLineConfig → ~/.config/aiterm/statusline.json
         ↓
[renders output]
         ↓
stdout (ANSI-formatted statusLine)
```

---

## Strengths

### 1. **Progressive Disclosure** ✅

The command hierarchy allows users to:
- **Start simple:** `ait statusline install` → 2-step setup
- **Explore:** `ait statusline test` → See what it looks like
- **Customize:** `ait statusline config` → Multiple approaches
- **Debug:** `ait statusline doctor` → Diagnose issues

This follows the "learn by doing" principle.

### 2. **Multiple Configuration Modes** ✅

Users can configure via:
- **Direct CLI:** `ait statusline config set display.show_git false`
- **Interactive:** `ait statusline config` (opens menu)
- **fzf-based:** `ait statusline config set --interactive` (fuzzy search)
- **Wizard:** `ait statusline config wizard` (questionnaire)
- **Editor:** `ait statusline config edit` (raw JSON)
- **Presets:** `ait statusline config preset minimal`

**Benefit:** Accommodates different user preferences (CLI-native vs interactive)

### 3. **XDG Compliance** ✅

- Config location: `~/.config/aiterm/statusline.json` (standard)
- Not cluttering home directory or `~/.claude/`
- Discoverable by config management tools

### 4. **Comprehensive Validation** ✅

```python
ait statusline doctor
```

Checks:
- Claude Code settings.json configuration ✓
- StatusLine config file validity ✓
- Theme configuration ✓
- Dependency availability (git) ✓
- Renderer functionality (test execution) ✓

This is excellent for troubleshooting.

### 5. **Error Handling** ✅

- Graceful degradation when config is invalid
- Backup creation before modifications
- Validation on file edits with undo option
- Clear error messages with actionable suggestions

### 6. **Installation Workflow** ✅

The `install` command:
- ✅ Checks for Claude Code installation
- ✅ Creates timestamped backup
- ✅ Validates JSON before writing
- ✅ Detects if already installed (no double-install)
- ✅ Shows configuration diff

---

## Areas for Improvement

### 1. **Discoverability Gap** ⚠️

**Issue:** New users may not know where to start after installation.

Currently:
```bash
ait statusline install
# → Shows brief next steps
```

**Recommendation:**
```
ait statusline install
→ Creates backup: ~/.claude/settings.backup-2026-01-17...
→ Updates ~/.claude/settings.json
→ Shows:

  [green]✓[/] StatusLine installed!

  [bold]Next steps:[/]
  1. [cyan]Preview:[/] ait statusline test
  2. [cyan]Customize:[/] ait statusline config
     - ait statusline config preset minimal
     - ait statusline config wizard
     - ait statusline config list
  3. [cyan]Start Claude Code:[/] Your new session will use statusLine
  4. [cyan]Verify:[/] ait statusline doctor

  [dim]Docs: https://Data-Wise.github.io/aiterm/guide/statusline.md[/]
```

**Benefit:** Users know exactly what to do next without guessing.

### 2. **Config Schema Discovery** ⚠️

**Issue:** `ait statusline config list` shows all 32 settings at once—overwhelming for newcomers.

**Current:**
```
ait statusline config list
→ Shows table with all 32 settings and 6 categories
```

**Recommendation:** Add preset-aware listing
```bash
# Show only settings affected by active preset
ait statusline config list --preset minimal
→ Shows only 6 settings changed by minimal preset

# Group by category
ait statusline config list --category display
→ Shows only display-related settings

# New: Show recommended settings for common tasks
ait statusline config list --common
→ Shows 5-7 most important settings to customize
```

### 3. **Test Mode Customization** ⚠️

**Issue:** `ait statusline test` uses fixed mock data. Can't test with actual project context.

**Recommendation:**
```bash
# Test with current project context
ait statusline test --live
→ Uses actual git status, project detection, current time

# Test with specific theme
ait statusline test --theme cool-blues  # Already exists ✓

# Test different terminal widths
ait statusline test --width 80
ait statusline test --width 200
```

### 4. **Configuration Editing UX** ⚠️

**Issue:** `ait statusline config edit` validates after closing editor, but if there are errors, it resets everything.

**Current behavior:**
```bash
ait statusline config edit
# User makes typo
# → Closes editor
# → Validation fails
# → Asks: "Reset to last valid config?"
# → If yes, ALL changes lost
```

**Recommendation:** Better error recovery
```bash
# Show what's invalid
[red]Configuration errors detected:[/]
  • display.show_git: expected bool, got "yes"
  • theme.name: unknown theme "cool"

[bold]Options:[/]
1. [cyan]Fix in editor again[/] (opens editor with error hints)
2. [yellow]Keep invalid config[/] (editor closes, file not saved)
3. [red]Reset to last valid[/] (discard all changes)
```

### 5. **Spacing Preset UX** ⚠️

**Issue:** `ait statusline config spacing` works well but isn't discoverable from main config menu.

**Current:**
- Separate command: `ait statusline config spacing <preset>`
- Not listed in `ait statusline config list`
- Not part of `wizard` flow

**Recommendation:**
```bash
# Option A: Integrate into config list
ait statusline config list
→ Shows spacing.mode in display category

# Option B: Add to wizard
ait statusline config wizard
→ Includes spacing question:
  "How much space between left/right segments?"
  • minimal (15% gap)
  • standard (20% gap)
  • spacious (30% gap)

# Option C: Smart detection
ait statusline config preset minimal
→ Also suggests: "Try spacing minimal? (15% gap)"
→ User says yes/no to apply together
```

### 6. **Theme Preview Gap** ⚠️

**Issue:** `ait statusline theme show` displays color codes, but user can't see how it looks in actual statusLine.

**Current:**
```bash
ait statusline theme show
→ Shows color table with ANSI codes
```

**Recommendation:**
```bash
# Option A: Inline preview
ait statusline theme show
→ Shows color table
→ PLUS: Renders sample statusLine with all theme colors

# Option B: Side-by-side theme comparison
ait statusline theme compare cool-blues forest-greens
→ Shows two statusLine previews side-by-side
```

### 7. **Installation Verification Gap** ⚠️

**Issue:** After `ait statusline install`, user must manually restart Claude Code.

**Current:**
```bash
ait statusline install
→ Says: "Restart Claude Code to see changes"
```

**Enhancement options:**
```bash
# Option A: Verify before returning
ait statusline install
→ Modifies settings.json
→ Tests that 'ait statusline render' works
→ Shows: "[green]✓[/] Installation verified!"

# Option B: Optional auto-restart on macOS
ait statusline install --restart
→ Installs and asks: "Restart Claude Code?"
→ Uses: osascript to quit/reopen Claude Code app
```

---

## Code Quality Assessment

### Configuration System ✅

```python
class StatusLineConfig:
    def load(self)      # Load with defaults
    def save()          # Persist to disk
    def get()           # Dot notation access
    def set()           # Type-checked setter
    def validate()      # Schema validation
    def reset()         # Restore defaults
```

**Strengths:**
- Proper separation of schema and data
- Type validation before saving
- Graceful degradation on parse errors
- Deep merge for defaults

**Minor note:** Schema is large (32 settings × 6 categories). Consider:
```python
# Current: schema in __init__ (lots of code)
# Suggestion: Move to separate schemas.py
from aiterm.statusline.schemas import STATUSLINE_SCHEMA
```

### Error Messages ✅

Examples of good error handling:
```python
# From config_set() - type conversion with clear feedback
if schema_def['type'] == 'int':
    try:
        value = int(value)
    except ValueError:
        console.print(f"[red]Invalid integer: {value}[/]")
        raise typer.Exit(1)

# From config_edit() - validation with options
if not is_valid:
    console.print("[red]Configuration errors detected:[/]")
    for error in errors:
        console.print(f"  [red]•[/] {error}")
```

---

## Security Considerations ✅

### Settings Modification
- ✅ Backups created before changes
- ✅ Validation before write
- ✅ User confirmation for destructive operations
- ✅ All changes to `~/.claude/settings.json`

### Render Command
- ✅ Reads from stdin (safe)
- ✅ Renders to stdout (safe)
- ✅ No arbitrary code execution
- ✅ Graceful error handling with fallback output

### No Security Issues Identified ✅

---

## Testing Coverage

From `tests/test_statusline_*.py`:
- ✅ `test_statusline_config.py` - Config get/set/validate (331 tests)
- ✅ `test_statusline_renderer.py` - Rendering logic (1207 tests)
- ✅ `test_statusline_themes.py` - Theme validation (314 tests)
- ✅ `test_statusline_agents.py` - Agent detection (159 tests)
- ✅ `test_statusline_worktree.py` - Worktree support (385 tests)

**Total: 2,396 tests focused on statusline**

**Assessment:** Excellent coverage for a new system.

---

## Documentation

### Strengths ✅
- Complete user guide (`docs/guide/statusline.md`)
- Visual examples with terminal output
- Clear display breakdown for all elements
- Spacing presets guide (`docs/guides/statusline-spacing.md`)
- Minimal design guide (`docs/guides/statusline-minimal.md`)

### Gaps ⚠️
- Missing: Troubleshooting guide (what if statusline doesn't appear?)
- Missing: Configuration examples by use case
- Missing: Theme customization (can't create custom themes)

---

## Workflow Recommendations

### For First-Time Users
```bash
# Current flow (works but could be clearer):
1. ait statusline install
2. ait statusline test
3. Restart Claude Code

# Suggested improved flow:
1. ait statusline install        # With better next-steps
2. ait statusline test           # Preview
3. ait statusline doctor         # Verify
4. ait statusline config wizard  # Optional customization
5. Restart Claude Code
```

### For Power Users
```bash
# These users will use:
ait statusline config set key value
ait statusline theme set cool-blues
ait statusline config spacing spacious

# They benefit from: --dry-run / preview flags (could add)
```

---

## Recommendations Summary

### High Priority (Usability)
1. **Improve install output** - Show clear next steps after installation
2. **Add --live flag to test** - Test with actual project context
3. **Integrate spacing into main config menu** - Reduce discoverability gap

### Medium Priority (UX Enhancement)
4. **Better error recovery in editor** - Show errors and allow fixing
5. **Theme preview in CLI** - Show actual statusLine with theme colors
6. **Config listing improvements** - Filter by category/preset/common

### Low Priority (Nice-to-Have)
7. **Auto-restart Claude Code** - Optional flag to restart after install
8. **Theme comparison tool** - Side-by-side preview
9. **Move schema to separate file** - Code organization

---

## Example: Enhanced Install Output

**Current:**
```
[green]✓[/] StatusLine installed successfully!

Configuration:
{
  "type": "command",
  "command": "ait statusline render"
}

Next steps:
  1. Restart Claude Code to see the new statusLine
  2. Run 'ait statusline config' to customize display
  3. Run 'ait statusline theme list' to see available themes
```

**Recommended:**
```
[green]✓[/] StatusLine installed successfully!

Configuration:
  type: command
  command: ait statusline render

[bold cyan]Next Steps[/]

1. [cyan]Preview:[/]
   ait statusline test

2. [cyan]Customize (choose one):[/]
   ait statusline config preset minimal  # Clean look
   ait statusline config wizard          # Interactive setup
   ait statusline config list            # View all options

3. [cyan]Themes:[/]
   ait statusline theme list             # See all themes
   ait statusline theme set cool-blues   # Try a theme

4. [cyan]Verify Setup:[/]
   ait statusline doctor                 # Health check

5. [cyan]Start Claude Code:[/]
   Your new session will use the statusLine

[dim]Documentation: https://Data-Wise.github.io/aiterm/guide/statusline.md[/]
[dim]Issues? Run: ait statusline doctor[/]
```

---

## Conclusion

The `ait statusline` command is a **well-designed, production-ready system** with:

✅ Clear architecture
✅ Multiple configuration modes
✅ Comprehensive validation
✅ Good error handling
✅ Excellent test coverage
✅ XDG-compliant storage

**Opportunities for improvement** are mostly in UX/discoverability rather than core functionality. The suggestions above would enhance the user experience, especially for newcomers, without changing the underlying architecture.

**Recommended next iteration focus:**
1. Better post-install guidance (guides users through next steps)
2. Live test mode (real project context in preview)
3. Integrated spacing configuration (reduce menu complexity)

---

## References

- **Command code:** `src/aiterm/cli/statusline.py` (1,016 lines)
- **Config system:** `src/aiterm/statusline/config.py`
- **Rendering:** `src/aiterm/statusline/renderer.py` (420 lines)
- **Tests:** `tests/test_statusline_*.py` (2,396 tests total)
- **Documentation:** `docs/guide/statusline.md`, `docs/guides/statusline-*.md`
