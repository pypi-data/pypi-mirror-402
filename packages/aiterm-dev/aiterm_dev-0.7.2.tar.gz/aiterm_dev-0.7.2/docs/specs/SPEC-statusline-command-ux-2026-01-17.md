# SPEC: StatusLine Command UX Improvements

**Status:** Draft
**Created:** 2026-01-17
**Author:** Claude Code (from brainstorm analysis)
**Related:** SPEC-statusline-config-ux-2025-12-31.md, SPEC-statusline-integration-2025-12-31.md
**Branch:** feat/statusline-command-ux-improvements
**Phase:** Implementation Phase 1-3

---

## 1. Overview

### 1.1 Purpose

This specification defines improvements to the `ait statusline` command structure to reduce complexity and improve discoverability. The current system has 7+ ways to accomplish the same tasks, creating a "Configuration Paradox" where users are overwhelmed by choice.

### 1.2 Goals

- **Single Entry Point** - One intuitive command (`ait statusline setup`) routes to appropriate tools
- **Unified Configuration Menu** - Consolidate display/theme/spacing into single interactive experience
- **v2.1 Integration** - Leverage Claude Code v2.1 hooks (templates, auto-register, validation)
- **Reduced Cognitive Load** - Users should know: "Use `setup`, it guides you"
- **Backward Compatibility** - All existing commands continue to work
- **Progressive Disclosure** - Simple path for new users, advanced options for power users

### 1.3 Goals

- Eliminate Configuration Paradox (7 ways → 1-2 clear paths)
- Improve first-time user experience (10+ min → < 2 min setup)
- Support Claude Code v2.1 features (hooks, session awareness)
- Maintain all existing functionality

### 1.4 Non-Goals

- Create GUI interface
- Add web-based configuration
- Remove any existing commands (backward compatibility)
- Create new display features (only UX improvements to existing features)

---

## 2. Problem Statement

### Current State: Configuration Paradox

Users have **too many ways** to configure statusline with inconsistent patterns:

```bash
# 7 Different Commands
ait statusline config set display.show_git false    # Direct CLI
ait statusline config set --interactive              # fzf menu
ait statusline config wizard                         # Questionnaire
ait statusline config edit                           # Raw editor
ait statusline config preset minimal                 # Presets
ait statusline config spacing standard               # Spacing (separate!)
ait statusline theme set cool-blues                  # Themes (different pattern!)
```

**Impact:**
- New users: "Which command should I use?" (guessing, confusion)
- Power users: "Why is spacing separate?" (fragmented mental model)
- Documentation: Unclear guidance on recommended path

**Root Cause:** Features added incrementally without unified command structure.

---

## 3. User Stories

### 3.1 New User - First Time Setup

**As a** new aiterm user
**I want to** configure statusline without reading docs
**So that** I can have a working statusline in < 2 minutes

**Acceptance Criteria:**
- `ait statusline setup` shows friendly menu with 5-6 options
- Each option is self-explanatory (no jargon)
- Selection routes to appropriate tool automatically
- Help/tips available at each step
- Process completes in < 2 minutes

**Current Behavior:** 10+ minutes, multiple commands, confusion
**Target:** < 2 minutes, single entry point, clear path

---

### 3.2 Experienced User - Full Customization

**As a** user familiar with statusline
**I want to** see all display/theme/spacing options in one place
**So that** I can explore and compare options without jumping between commands

**Acceptance Criteria:**
- `ait statusline customize` opens unified menu
- Menu shows:
  - Display options (git, time, project, etc.)
  - Theme selection (live preview if possible)
  - Spacing presets (minimal/standard/spacious)
  - Advanced settings (edit raw config)
- All changes visible before applying
- Can save and test changes

---

### 3.3 Power User - Quick Tweaks

**As a** power user
**I want to** quickly change one setting from CLI
**So that** I don't need interactive menu for simple changes

**Acceptance Criteria:**
- `ait statusline config set` still works (backward compatible)
- `ait statusline theme set` still works (backward compatible)
- `ait statusline config spacing` still works (backward compatible)
- New: These commands documented as "Advanced" not default path

---

### 3.4 v2.1 Integration - Hook Templates

**As a** Claude Code v2.1 user
**I want to** use hooks for statusline customization
**So that** statusline can automatically adapt to my environment

**Acceptance Criteria:**
- `ait statusline hooks list` shows available hook templates
- `ait statusline hooks add <hook>` installs pre-built hook
- Hooks auto-validated during install
- Works with: on-theme-change, on-remote-session, on-error
- Documentation shows how to create custom hooks

---

## 4. Solution Architecture

### 4.1 Gateway Pattern

Single entry point that routes to appropriate tools:

```
User: ait statusline setup
        ↓
    [Gateway Menu]
        ↓
    ┌───┴──────┬────────┬──────────┐
    ↓          ↓        ↓          ↓
  Display    Theme    Spacing   Advanced
  Settings   Menu     Menu      Menu
    ↓          ↓        ↓          ↓
  wizard    set theme preset    editor
```

### 4.2 Command Structure (New)

```bash
ait statusline setup                    # NEW: Gateway to customization
├── Routes to: customize/theme/spacing based on selection

ait statusline customize                # NEW: Unified menu
├── Display settings
├── Theme selection
├── Spacing adjustment
└── Advanced (edit raw)

ait statusline hooks                    # NEW: v2.1 hook management
├── list                                # Show available hooks
├── add <hook-name>                     # Install hook
└── validate                            # Check hook syntax
```

### 4.3 Command Structure (Existing - Preserved)

All existing commands continue to work:
```bash
ait statusline config set key value     # Still works (backward compat)
ait statusline theme set name           # Still works (backward compat)
ait statusline config spacing preset    # Still works (backward compat)
ait statusline install                  # Still works (unchanged)
ait statusline test                     # Still works (unchanged)
ait statusline doctor                   # Still works (unchanged)
```

---

## 5. Implementation Plan

### Phase 1: Gateway + Unified Menu (5-6 hours)

**Deliverables:**
- `ait statusline setup` - Gateway command
- `ait statusline customize` - Unified interactive menu
- Hook templates module (foundation)
- 25+ new unit/integration tests
- Updated documentation

**Files to Create/Modify:**
| File | Change | Effort |
|------|--------|--------|
| `src/aiterm/cli/statusline.py` | Add setup, customize commands | 2 hours |
| `src/aiterm/statusline/hooks.py` | NEW: Hook template system | 1 hour |
| `src/aiterm/statusline/interactive.py` | Enhance menu system | 1 hour |
| `src/aiterm/statusline/config.py` | Add hints/descriptions | 30 min |
| `tests/test_statusline_*.py` | 25+ new tests | 1 hour |
| `docs/guide/statusline.md` | Update setup flow | 30 min |

**Estimated Total:** 5-6 hours

---

### Phase 2: Install/Wizard Enhancements (2-3 hours)

**Deliverables:**
- Remote session auto-detection (v2.1 `/teleport`)
- Workspace context in wizard
- Hook validation in install
- 10+ new tests

**Features:**
- Auto-enable remote indicators when `/teleport` detected
- Show monorepo path in setup suggestions
- Warn about conflicting hooks

---

### Phase 3: Advanced Features (Future)

**Deliverables:**
- Settings profiles (teaching/deep-work/remote/pair)
- Command aliases for power users
- Theme comparison tool

**Timeline:** Next sprint or later

---

## 6. Technical Specification

### 6.1 Gateway Command (`setup`)

```python
@app.command("setup")
def statusline_setup():
    """Quick gateway to statusline customization."""
    # AskUserQuestion with 6 options:
    # 1. Customize display options
    # 2. Change color theme
    # 3. Adjust spacing
    # 4. Apply a preset
    # 5. View all settings
    # 6. Edit raw config

    # Route to appropriate subcommand based on selection
```

**Flow:**
1. Show menu with 6 clear options
2. User selects option
3. Route to: `customize`/`theme set`/`config spacing`/`config list`/`config edit`
4. Complete action and return to menu (loop until done)

### 6.2 Unified Menu (`customize`)

```python
class StatusLineCustomizeMenu:
    """Unified customization interface."""

    def __init__(self, config: StatusLineConfig):
        self.sections = [
            DisplaySection(config),      # git, time, session, etc.
            ThemeSection(config),        # theme selection
            SpacingSection(config),      # gap presets
            AdvancedSection(config)      # edit raw/reset
        ]

    def run(self):
        """Show all options, let user browse and change."""
        # Interactive menu with all display/theme/spacing options
        # Changes applied immediately with preview
```

**Sections:**
- **Display:** Checkboxes for git, time, session, lines, usage, etc.
- **Theme:** Radio buttons for available themes with preview
- **Spacing:** Radio buttons for minimal/standard/spacious
- **Advanced:** Options to edit raw config or reset to defaults

### 6.3 Hook Templates

```python
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
```

---

## 7. Acceptance Criteria

### User Experience

- ✅ New user can configure statusline in < 2 minutes
- ✅ `ait statusline setup` clearly shows all options
- ✅ `ait statusline customize` shows display/theme/spacing in one place
- ✅ Power users: existing commands still work (backward compatible)
- ✅ Help/tips available at each step

### Technical

- ✅ Gateway pattern reduces visible commands from 7 to 2-3
- ✅ All 3+ hook templates available and documented
- ✅ 25+ new tests (unit + integration)
- ✅ No breaking changes to existing commands
- ✅ Install/doctor commands updated to mention new features
- ✅ Documentation updated with new flow

### Metrics

- ✅ First-time setup: 10+ min → < 2 min (80% reduction)
- ✅ Command discoverability: "Which command?" → "Use setup"
- ✅ Hook integration: 3 pre-built templates, auto-register working
- ✅ Backward compatibility: All existing scripts/workflows unchanged

---

## 8. Testing Strategy

### Unit Tests (15+)

- Setup command routing (3 tests)
- Customize menu sections (4 tests)
- Hook template validation (3 tests)
- Config with hints/descriptions (3 tests)
- Backward compat (2 tests)

### Integration Tests (10+)

- Full setup → customize flow (2 tests)
- Hook template installation (2 tests)
- Install with hook validation (2 tests)
- Rendering with all sections (2 tests)
- v2.1 feature detection (2 tests)

### Manual Testing

- Test in actual terminal with statusline running
- Test hook installation and execution
- Verify /teleport detection works
- Confirm backward compatibility

---

## 9. Documentation Updates

### User Guide (`docs/guide/statusline.md`)

Add new "Setup Workflow" section:

```markdown
## Quick Setup (New - Start Here)

1. Run: ait statusline setup
2. Follow the menu (< 2 minutes)
3. Restart Claude Code

For more control, see "Advanced Configuration" section.

## Advanced Configuration

For power users who want direct CLI control:
- ait statusline config set key value
- ait statusline theme set name
- ait statusline config spacing preset
```

### Reference Updates

- Update command reference to highlight `setup` as entry point
- Add "Gateway Pattern" explanation
- Document hook templates
- Show before/after command structure

---

## 10. Migration Path (Backward Compatibility)

| Old Path | Still Works? | New Recommendation |
|----------|-------------|-------------------|
| `ait statusline config set` | ✅ Yes | Use setup/customize |
| `ait statusline theme set` | ✅ Yes | Use setup/customize |
| `ait statusline config spacing` | ✅ Yes | Use setup/customize |
| `ait statusline config wizard` | ✅ Yes | Use setup/customize |
| `ait statusline install` | ✅ Yes | Unchanged |
| `ait statusline test` | ✅ Yes | Unchanged |
| `ait statusline doctor` | ✅ Yes | Unchanged |

**All existing workflows continue to function.** New recommendations guide users toward simpler paths.

---

## 11. Success Criteria

### Phase 1 Complete When:

- ✅ `ait statusline setup` routes to all customization options
- ✅ `ait statusline customize` shows unified menu with all options
- ✅ Hook templates available (at least 2)
- ✅ 25+ tests passing
- ✅ Documentation updated
- ✅ Backward compatibility verified
- ✅ User feedback: "This is much clearer than before"

### Launch Criteria:

- ✅ All tests passing
- ✅ Doctor command detects new features
- ✅ Real-world testing with actual users
- ✅ Documentation reviewed and approved

---

## 12. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Users prefer old commands | Medium | Both paths work, docs guide to new |
| Hook conflicts | Low | Validation in install, doctor checks |
| Menu too complex | Low | Start with 5-6 simple options |
| v2.1 features not available | Low | Graceful degradation if v2.1 not detected |

---

## 13. History

| Date | Author | Status | Notes |
|------|--------|--------|-------|
| 2026-01-17 | Claude Code | Draft | Created from brainstorm analysis |
| | | | Phase 1-3 roadmap defined |
| | | | User stories + acceptance criteria |
| | | | Hook templates specified |

---

## 14. Appendix: Existing SPEC References

**Related Specifications:**
- SPEC-statusline-config-ux-2025-12-31.md - Configuration options
- SPEC-statusline-integration-2025-12-31.md - Claude Code integration
- SPEC-statusline-redesign-2026-01-01.md - Minimal redesign
- SPEC-statusline-spacing-2026-01-02.md - Spacing presets

**Related Brainstorms:**
- BRAINSTORM-statusline-command-improvements-2026-01-17.md
- BRAINSTORM-statusline-v2.1-integration-2026-01-17.md
- REVIEW-STATUSLINE-COMMAND.md
