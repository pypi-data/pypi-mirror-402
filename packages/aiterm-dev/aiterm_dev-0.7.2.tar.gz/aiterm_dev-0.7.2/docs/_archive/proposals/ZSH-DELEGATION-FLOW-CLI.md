# ZSH Delegation to flow-cli - Brainstorm Proposal

**Generated:** 2025-12-29
**Context:** aiterm v0.3.9 / flow-cli integration
**Topic:** Delegate zsh implementation from aiterm to flow-cli

---

## Overview

aiterm currently has a legacy zsh file (`zsh/iterm2-integration.zsh`, 186 lines) that duplicates functionality flow-cli already provides. This proposal outlines how to delegate zsh/shell functionality to flow-cli while keeping aiterm focused on rich CLI features.

---

## Current State Analysis

### aiterm's zsh/iterm2-integration.zsh (186 lines)

| Function | Lines | Purpose |
|----------|-------|---------|
| `_iterm_switch_profile()` | 5 | Profile switching via escape sequence |
| `_iterm_set_title()` | 5 | Tab title via OSC 2 |
| `_iterm_set_user_var()` | 3 | Status bar variables via base64 |
| `_iterm_set_status_vars()` | 5 | Set multiple status vars |
| `_iterm_git_info()` | 15 | Git branch + dirty detection |
| `_iterm_type_to_profile()` | 8 | Map project type → profile name |
| `_iterm_detect_context()` | 70 | Main context detection logic |
| `iterm_session_start()` | 10 | Focus session start |
| `iterm_session_end()` | 12 | Focus session restore |
| Hook registration | 8 | chpwd hook setup |

### flow-cli's Existing Capabilities

| flow-cli File | Provides |
|---------------|----------|
| `lib/project-detector.zsh` | Project type detection (10 types) |
| `hooks/chpwd.zsh` | Directory change hook |
| `_flow_project_icon()` | Type → emoji mapping |
| `_flow_detect_project_type()` | Type detection logic |

### Overlap Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                    FUNCTIONALITY OVERLAP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FLOW-CLI ALREADY HAS              AITERM DUPLICATES            │
│  ─────────────────────              ──────────────────           │
│  Project type detection        ←→  _iterm_detect_context()      │
│  Project icons                 ←→  icon assignment              │
│  chpwd hook                    ←→  chpwd registration           │
│  10 project types              ←→  8 project types              │
│                                                                  │
│  AITERM-SPECIFIC (Terminal integration)                          │
│  ───────────────────────────────────────                         │
│  _iterm_switch_profile()      - iTerm2 escape sequences         │
│  _iterm_set_title()           - OSC 2 title                     │
│  _iterm_set_user_var()        - iTerm2 status bar               │
│  Session focus mode           - Profile save/restore            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Options

### Option A: Full Delegation (Recommended)

**Effort:** 🔧 Medium (2-3 hours)

**Approach:** Remove aiterm's zsh file, use flow-cli's project detection, add thin terminal wrapper.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DELEGATION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  flow-cli                          aiterm                        │
│  ────────                          ──────                        │
│  Project detection          ────►  (imports detection)          │
│  chpwd hook                 ────►  (registers callback)         │
│  Icons & type names         ────►  (uses directly)              │
│                                                                  │
│                                    Terminal integration:         │
│                                    - Profile switching           │
│                                    - Title setting               │
│                                    - Status bar vars             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:**

1. **flow-cli: Add hook callback API**
   ```zsh
   # In flow-cli/hooks/chpwd.zsh
   typeset -ga FLOW_CHPWD_CALLBACKS

   flow_register_chpwd_callback() {
     FLOW_CHPWD_CALLBACKS+=("$1")
   }

   # In _flow_chpwd_hook, call registered callbacks:
   for callback in "${FLOW_CHPWD_CALLBACKS[@]}"; do
     "$callback" "$project_root" "$project_name" "$project_type"
   done
   ```

2. **aiterm: Create thin zsh wrapper (new file)**
   ```zsh
   # ~/.config/aiterm/shell.zsh (30 lines)
   _aiterm_terminal_callback() {
     local project_root="$1" project_name="$2" project_type="$3"

     # Call Python CLI for terminal updates
     ait switch --quiet --type "$project_type" --name "$project_name"
   }

   # Register with flow-cli if available
   if type flow_register_chpwd_callback &>/dev/null; then
     flow_register_chpwd_callback _aiterm_terminal_callback
   fi
   ```

3. **Delete:** `aiterm/zsh/iterm2-integration.zsh`

**Pros:**
- Single source of truth for project detection
- Cleaner separation of concerns
- flow-cli gets callback extensibility (useful for other tools)
- aiterm's Python CLI remains authoritative for terminal control

**Cons:**
- Requires flow-cli update first
- Two-way dependency (soft - just registration)

---

### Option B: Shared Library Extraction

**Effort:** 🏗️ Large (4-5 hours)

**Approach:** Extract common code to shared library that both tools import.

```
~/projects/dev-tools/shared-shell/
├── lib/
│   ├── project-detector.zsh
│   └── terminal-integration.zsh
└── README.md
```

**Pros:**
- Maximum code reuse
- Independent versioning

**Cons:**
- Another repo to maintain
- More complex dependency chain
- Overkill for two tools

---

### Option C: Keep Separate, Sync Manually

**Effort:** ⚡ Quick (30 min)

**Approach:** Keep aiterm's zsh file, periodically sync with flow-cli patterns.

```bash
# When flow-cli adds a new project type, add to aiterm too
```

**Pros:**
- No coordination needed
- Works standalone

**Cons:**
- Duplication (186 lines × 2)
- Sync drift inevitable
- Two places to fix bugs

---

### Option D: aiterm Consumes flow-cli

**Effort:** 🔧 Medium (2 hours)

**Approach:** aiterm sources flow-cli's detection, adds terminal-specific overlay.

```zsh
# In aiterm's shell integration
source "$HOME/projects/dev-tools/flow-cli/lib/project-detector.zsh"

_aiterm_on_chpwd() {
  local type=$(_flow_detect_project_type)
  local icon=$(_flow_project_icon "$type")
  _aiterm_apply_terminal "$type" "$icon"
}
```

**Pros:**
- One-way dependency (aiterm → flow-cli)
- No flow-cli changes needed
- Works immediately

**Cons:**
- Tight coupling to flow-cli's internals
- Breaks if flow-cli refactors

---

## Recommended: Option A + Quick Win

Start with **Option A** (full delegation with callback API) because:

1. **Clean separation:** flow-cli handles shells, aiterm handles terminals
2. **Callback API** is a flow-cli enhancement anyway
3. **Reduces aiterm complexity** by 186 lines

### Quick Win First (15 min)

Before full delegation, apply a quick fix:

```zsh
# In aiterm/zsh/iterm2-integration.zsh, near the top:
# Use flow-cli's detection if available
if [[ -f "$HOME/projects/dev-tools/flow-cli/lib/project-detector.zsh" ]]; then
  source "$HOME/projects/dev-tools/flow-cli/lib/project-detector.zsh"
  # Override local detection with flow-cli's
  _iterm_detect_project() {
    _flow_detect_project_type
  }
fi
```

This gets immediate benefit while planning full delegation.

---

## Implementation Plan

### Phase 1: Quick Win (Now - 15 min)
- [ ] Source flow-cli's project-detector in aiterm's zsh
- [ ] Test context detection still works
- [ ] Commit: "refactor(zsh): use flow-cli project detection"

### Phase 2: flow-cli Callback API (1 hour)
- [ ] Add `FLOW_CHPWD_CALLBACKS` array
- [ ] Add `flow_register_chpwd_callback()` function
- [ ] Update `_flow_chpwd_hook()` to call registered callbacks
- [ ] Add docs and tests
- [ ] Release flow-cli update

### Phase 3: aiterm Migration (1 hour)
- [ ] Create `~/.config/aiterm/shell.zsh` (thin wrapper)
- [ ] Register callback with flow-cli
- [ ] Delete `aiterm/zsh/iterm2-integration.zsh`
- [ ] Update installation docs
- [ ] Release aiterm update

### Phase 4: Documentation (30 min)
- [ ] Update aiterm docs to reference flow-cli
- [ ] Add "Terminal Integration" section to flow-cli docs
- [ ] Update CLAUDE.md in both projects

---

## Files to Modify

| File | Action | Lines |
|------|--------|-------|
| `aiterm/zsh/iterm2-integration.zsh` | Delete | -186 |
| `flow-cli/hooks/chpwd.zsh` | Add callback API | +20 |
| `flow-cli/lib/callbacks.zsh` | New file | +50 |
| `~/.config/aiterm/shell.zsh` | New file | +30 |
| aiterm CLAUDE.md | Update | ~10 |
| flow-cli CLAUDE.md | Update | ~10 |

**Net change:** -186 + 110 = **-76 lines** (less code!)

---

## Ownership Split After Delegation

| Responsibility | Owner | Implementation |
|----------------|-------|----------------|
| Project type detection | flow-cli | `lib/project-detector.zsh` |
| Directory change hooks | flow-cli | `hooks/chpwd.zsh` |
| Shell aliases (`gfs`, `wt*`) | flow-cli | `lib/dispatchers/` |
| Terminal profile switching | aiterm | `ait switch` CLI |
| Terminal themes | aiterm | `ait ghostty theme` CLI |
| Tab titles | aiterm | Python via OSC sequences |
| Status bar integration | aiterm | iTerm2 user variables |

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Duplicate detection code | 2 | 1 |
| Lines in aiterm/zsh/ | 186 | 0 |
| Project types supported | 8 (aiterm) | 10 (flow-cli) |
| Time to add new type | 2 files | 1 file |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| flow-cli not installed | Medium | Fallback to basic detection in aiterm CLI |
| Breaking changes in flow-cli | Low | Version pin in aiterm docs |
| Performance regression | Low | Callback is async, non-blocking |

---

## Next Steps

→ **Immediate:** Apply Quick Win (source flow-cli detector)
→ **This Week:** Add callback API to flow-cli
→ **After:** Complete aiterm migration
→ **v0.4.0:** Remove legacy zsh file, document integration

---

*Status: Proposal*
*Target: v0.3.10 (quick win) → v0.4.0 (full delegation)*
*Integration: aiterm + flow-cli*
