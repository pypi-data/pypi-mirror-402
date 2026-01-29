# Brainstorm: aiterm StatusLine Integration with Claude Code v2.1

**Date:** 2026-01-17
**Context:** aiterm statusline review + Claude Code v2.1.0 features (Jan 7, 2026)
**Use Case:** Personal development (solo coding)
**Priorities:** Remote session awareness, Workspace context

---

## Overview

Claude Code v2.1.0 introduces powerful new capabilities:
- **Session teleportation** (`/teleport`) - Move work between terminal and web
- **Hooks for agents/skills** - Fine-grained control via frontmatter
- **Hot reload for skills** - Skills update without restart
- **Multilingual output** - Configure language per session

These features enable **enhanced session awareness** in statusline, especially for remote and multi-context workflows.

---

## Quick Wins (< 30 min each)

### 1. ⚡ Remote Session Indicator

**What:** Show local vs remote session in statusline (right side)

**Current:** Only shows worktree info
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░          ░▒▓ (wt) feature ▓▒░
╰─ Sonnet 4.5
```

**Proposed:**
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░          ░▒▓ (wt) feature | 🌐 remote ▓▒░
╰─ Sonnet 4.5
```

**Implementation:**
- Check `SESSION_TELEPORT_URL` env var (set by `/teleport`)
- Add `🌐 remote` badge when remote
- Local sessions show nothing (clean display)
- Priority: **High** (immediate value)

**Files to modify:**
- `src/aiterm/statusline/segments.py` → Add remote session detection
- `src/aiterm/statusline/config.py` → Add `display.show_remote_indicator` setting
- Tests: Add 4-5 tests for remote detection

---

### 2. ⚡ Session Workspace Context

**What:** Show active workspace/monorepo context in statusline

**Current:** Shows project name only (dirname)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░
```

**Proposed (Monorepo example):**
```
╭─ ░▒▓ 📁 dev-tools/aiterm  main ▓▒░
```

**Implementation:**
- Check for monorepo markers:
  - Root level: `lerna.json`, `pnpm-workspace.yaml`, `workspace.members` (Rust)
  - Claude Code: Check `.claude/` directory for multi-project config
- Show path relative to workspace root (max 30 chars)
- Smart truncation: `dev-tools/aiterm` vs `dev-tools/mcp-servers/statistical-research`
- Priority: **High** (better context awareness)

**Files to modify:**
- `src/aiterm/context/detector.py` → Add monorepo detection
- `src/aiterm/statusline/segments.py` → Show workspace path
- Tests: Add 6-8 tests for monorepo detection

---

### 3. ⚡ Hook Status Indicator

**What:** Show if agent/skill hooks are active in current session

**Current:** No hook visibility
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░
```

**Proposed:**
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░ 🎣 hooks:2
```

**Implementation:**
- Check Claude Code settings for active hooks:
  - Count PreToolUse, PostToolUse, Stop hooks
  - Show count when > 0
  - Optional: Show hook names on hover (if supported)
- Hook badge: `🎣 hooks:N` (emoji + count)
- Priority: **High** (indicates session customization)

**Files to modify:**
- `src/aiterm/claude/hooks.py` → New module for hook detection
- `src/aiterm/statusline/segments.py` → Add hook status
- Tests: Add 5-6 tests for hook detection

---

## Medium Effort (1-2 hours)

### 4. 🔧 Workspace Awareness in Config Menu

**What:** Show monorepo context in statusline config wizard

**Current:**
```
ait statusline config wizard
→ Asks about display options (git, time, etc.)
```

**Proposed:**
```
ait statusline config wizard
→ Detects monorepo automatically
→ Proposes: "Show workspace context? (dev-tools/aiterm)"
→ Option to enable/disable workspace display
```

**Implementation:**
- Enhance `config_wizard()` in `src/aiterm/cli/statusline.py`
- Auto-detect monorepo in wizard flow
- Add `display.show_workspace_context` setting
- Show preview: what statusline will look like with workspace
- Priority: **Medium** (UX enhancement)

**Changes:**
- `src/aiterm/cli/statusline.py` → Update wizard flow
- `src/aiterm/statusline/config.py` → Add new schema setting
- Tests: Add 4-5 wizard tests

---

### 5. 🔧 Remote Session Auto-Detection in Install

**What:** Detect if installing in remote session and suggest remote-aware config

**Current:**
```
ait statusline install
→ Installs to ~/.claude/settings.json
→ No special handling for remote
```

**Proposed:**
```
ait statusline install
[detects /teleport URL in environment]
→ "You're in a remote session!"
→ Suggests: "Enable remote indicator? (🌐 remote badge)"
→ Auto-applies recommended settings for remote work
```

**Implementation:**
- In `statusline_install()`, check for teleport markers
- Auto-enable `display.show_remote_indicator` if remote
- Show confirmation: "Remote mode enabled"
- Priority: **Medium** (improves first-time experience)

**Changes:**
- `src/aiterm/cli/statusline.py` → Enhance install command
- `src/aiterm/statusline/config.py` → Add remote detection helper

---

### 6. 🔧 Skills Hot-Reload Integration

**What:** Show visual indicator when aiterm skills are hot-reloaded

**Current:** No indicator for skill changes
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░
```

**Proposed:**
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░ ♻️ reload
```

**Implementation:**
- Monitor `~/.claude/plugins/` for file changes
- When statusline.py or config.py changes, show reload indicator
- Indicator: `♻️ reload` (appears for 10 seconds then fades)
- Background task: Watch for changes every 2 seconds
- Priority: **Medium** (developer experience)

**Changes:**
- `src/aiterm/statusline/interactive.py` → Add file watcher
- Tests: Add 3-4 watcher tests

---

## Long-term (Future sessions)

### 7. 🏗️ Collaboration Signals (Team Workflows)

**What:** Show if multiple Claude Code instances are active in same workspace

**Why defer:** Requires:
- Session registry (currently per-user)
- Multi-session coordination protocol
- Team/org configuration
- Works better after Claude Code adds native session sharing

**Future possibility:**
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░          ░▒▓ users:2 | feature ▓▒░
```

**Research needed:**
- Claude Code v2.2+ session sharing API
- Team workspace protocol
- Security implications (which info to share)

---

### 8. 🏗️ Output Language Indicator

**What:** Show configured output language when non-English

**Why defer:** Lower priority for solo dev
- Would appear rarely (most sessions are English)
- Better to add when team collaboration signals added
- Requires language detection from Claude Code config

**Future possibility:**
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░          ░▒▓ 日本語 | feature ▓▒░
```

---

### 9. 🏗️ Advanced Monorepo Navigation

**What:** Package picker in statusline (jump between packages)

**Why defer:** Requires:
- Mouse hover interaction (interactive statusline)
- Pop-up menu rendering in terminal
- Complex state management

**Future possibility:**
```
ait statusline jump
→ fzf menu of monorepo packages
→ Jump to that package's directory
```

---

## Recommended Implementation Path

### Phase 1: Core Session Awareness (This week)
**Focus:** Remote session + workspace context
**Effort:** 4-6 hours
**Impact:** High (directly addresses priorities)

1. ⚡ **Remote Session Indicator** (30 min)
   - Detect `/teleport` URL in environment
   - Add `display.show_remote_indicator` setting
   - Show `🌐 remote` badge on right side

2. ⚡ **Workspace Context** (30 min)
   - Detect monorepo root (lerna.json, pnpm-workspace.yaml, etc.)
   - Show workspace path in project name
   - Smart truncation for long paths

3. ⚡ **Hook Status** (30 min)
   - Count active hooks in Claude Code settings
   - Show `🎣 hooks:N` when hooks > 0
   - Optional: Allow hiding via config

### Phase 2: UX Enhancements (Next session)
**Focus:** Better configuration experience
**Effort:** 2-3 hours
**Impact:** Medium (improves usability)

4. 🔧 **Wizard Enhancement**
   - Auto-detect and display monorepo context
   - Ask user about workspace display preference

5. 🔧 **Install Enhancement**
   - Detect remote sessions automatically
   - Apply remote-aware defaults

6. 🔧 **Skills Hot-Reload**
   - File watcher for skill changes
   - Visual indicator when changes detected

### Phase 3: Future Enhancements (Backlog)
- Collaboration signals (requires team features)
- Language indicator (add with collab signals)
- Advanced monorepo navigation (requires interactive statusline)

---

## Updated Review Recommendations

Based on Claude Code v2.1.0:

### High Priority (Updated)

**Original:** Better install output
**Updated to:** ✅ **Remote session indicator** (leverages `/teleport`)
- Install already good; focus on using v2.1 features

**Original:** Add `--live` flag to test
**Status:** ✅ Keep (orthogonal to v2.1)

**Original:** Integrate spacing into main config
**Updated to:** ✅ **Workspace context in wizard** (monorepo awareness)
- More valuable than spacing integration

### Medium Priority (New)

**New:** Hook status indicator (v2.1 hooks feature)
- Show active hooks in statusline
- Helps understand session customization

**New:** Remote session auto-detection (v2.1 `/teleport`)
- Auto-enable remote indicators when needed
- Better first-time experience

---

## Configuration Schema Changes

New settings to add to `StatusLineConfig`:

```python
{
  "display": {
    # Existing
    "show_git": true,
    "show_thinking_indicator": true,

    # NEW
    "show_remote_indicator": true,      # Show 🌐 remote badge
    "show_workspace_context": true,     # Show monorepo path
    "show_hook_status": true,           # Show 🎣 hooks:N
    "workspace_max_length": 30,         # Truncate workspace path
    "hook_count_threshold": 1,          # Show count when >= this
  },

  "remote": {
    "indicator_text": "remote",         # Text to show (instead of 🌐)
    "indicator_emoji": "🌐",            # Emoji option
  },

  "workspace": {
    "show_root_only": false,            # Show "aiterm" or "dev-tools/aiterm"
    "truncate_from": "start",           # Truncate from start or end
    "separator": "/"                    # Path separator (unicode option)
  },

  "hooks": {
    "show_count": true,                 # Show number of hooks
    "abbreviate": false,                # Show "hooks:2" or "🎣2"
  }
}
```

---

## Files Affected

| File | Changes | Effort |
|------|---------|--------|
| `src/aiterm/statusline/segments.py` | Add remote, workspace, hook segments | 1 hour |
| `src/aiterm/statusline/config.py` | Add new schema settings | 30 min |
| `src/aiterm/cli/statusline.py` | Enhance install, wizard | 1 hour |
| `src/aiterm/context/detector.py` | Monorepo detection | 30 min |
| `src/aiterm/claude/hooks.py` | NEW: Hook detection | 30 min |
| `tests/test_statusline_*.py` | Add 25+ new tests | 1 hour |
| `docs/guide/statusline.md` | Document new features | 30 min |

**Total Estimated Effort:** 5-6 hours

---

## Testing Strategy

### Unit Tests (20+ tests)
- Remote session detection (3 tests)
- Monorepo detection (5 tests)
- Hook counting (3 tests)
- Truncation logic (4 tests)
- Config schema validation (3 tests)

### Integration Tests (5+ tests)
- Install with remote detection (1 test)
- Wizard with monorepo (2 tests)
- Full rendering with new segments (2 tests)

### Manual Testing
- Install in actual remote session (via `/teleport`)
- Test in monorepo project (aiterm itself)
- Verify rendering in different terminal widths

---

## Documentation Updates

### User Guide (`docs/guide/statusline.md`)

Add new section:
```markdown
## v2.1 Integration Features

### Remote Session Indicator
When using Claude Code `/teleport` to work remotely, statusline shows:
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░          ░▒▓ 🌐 remote | feature ▓▒░
```

Enable/disable:
```bash
ait statusline config set display.show_remote_indicator true
```

### Workspace Context
In monorepo projects, statusline shows relative path:
```
╭─ ░▒▓ 📁 dev-tools/aiterm  main ▓▒░
```

Works with:
- Lerna (`lerna.json`)
- pnpm (`pnpm-workspace.yaml`)
- Cargo (`Cargo.workspace`)
- Custom Claude Code workspace

Enable/disable:
```bash
ait statusline config set display.show_workspace_context true
```

### Hook Status Indicator
Shows when agent/skill hooks are active:
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░ 🎣 hooks:2
```

This indicates:
- 2 active hooks (PreToolUse, PostToolUse, or Stop)
- Session has customized behavior
- Hooks may add latency to operations
```

### New Quick Start

Update install step:
```
1. Run: ait statusline install
   - Auto-detects remote sessions
   - Applies appropriate defaults

2. Check features: ait statusline doctor
   - Shows remote status
   - Shows monorepo context
   - Shows hook count
```

---

## GitHub Issues to Create

1. **Feature: Remote session indicator** (High)
   - Link to `/teleport` documentation
   - Mention: env var detection, badge design

2. **Feature: Monorepo workspace awareness** (High)
   - Support: lerna, pnpm, Cargo, Claude Code workspace
   - Include: truncation logic, path detection

3. **Feature: Hook status in statusline** (Medium)
   - Show active hook count
   - Optional hook names

4. **Enhancement: Wizard workspace context** (Medium)
   - Auto-detect monorepo in wizard
   - Suggest enabling workspace display

5. **Enhancement: Remote-aware install** (Medium)
   - Auto-enable remote indicator for `/teleport` sessions
   - Show remote detection in doctor

---

## Success Metrics

**What we're measuring:**
- ✅ Remote session visibility (80% of remote users find indicator helpful)
- ✅ Monorepo awareness (accuracy of workspace detection)
- ✅ Configuration discoverability (wizard mentions new features)

**How we know it's working:**
- `ait statusline doctor` shows workspace + remote status
- `ait statusline test` renders all new segments correctly
- Install wizard offers monorepo/remote options
- No regression in existing features

---

## Conclusion

Claude Code v2.1.0 enables **three high-value statusline enhancements** that directly address the key gap: **session context awareness** for remote and monorepo workflows.

**Recommended:** Implement Phase 1 (Remote + Workspace + Hooks) this week while they're fresh. These features work together to give users complete visibility into their session context.

**Key insight:** The features unlock a **"personal context layer"** in statusline that wasn't possible before v2.1.0. Users will understand at a glance:
- Where they are: `dev-tools/aiterm` (workspace)
- How they're connected: `🌐 remote` (session type)
- What's customized: `🎣 hooks:2` (session configuration)

---

## Implementation Checklist (Phase 1)

- [ ] Add remote session detection to segments.py
- [ ] Add workspace monorepo detection to context/detector.py
- [ ] Add hook counting to claude/hooks.py
- [ ] Update config schema with new settings
- [ ] Enhance install command for remote detection
- [ ] Add 25+ unit/integration tests
- [ ] Update user documentation
- [ ] Test in actual remote session
- [ ] Test in monorepo (aiterm itself)
- [ ] Create GitHub issues for Phase 2/3
- [ ] Commit and push to dev branch
- [ ] Update CHANGELOG for v0.7.3

