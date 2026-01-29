# StatusLine Spacing Comparison

Visual side-by-side comparison of spacing options for StatusLine v0.7.0.

---

## Current Implementation (Cramped)

```
╭─ ░▒▓ 🐍 aiterm (venv: py3.14) main 📦1 🔗origin/main ▓▒░
╰─ Sonnet 4.5 │ 11:46 🌅 │ ⏱ 1h48m │ +123/-45 │ [learning]
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   Issue: Separators touch content, hard to scan quickly
```

**Line 2 character-by-character:**
```
S o n n e t   4 . 5   │   1 1 : 4 6   🌅   │   ⏱   1 h 4 8 m   │   + 1 2 3 / - 4 5
                      ^               ^               ^               ^
                      1 space         1 space         1 space         1 space
```

---

## Proposed Option A: Standard Spacing (2 spaces)

```
╭─ ░▒▓ 🐍 aiterm (venv: py3.14)  main 📦1 🔗origin/main ▓▒░
╰─ Sonnet 4.5  │  11:46 🌅  │  ⏱ 1h48m  │  +123/-45  │  [learning]
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   Better: Clear visual separation, easier to parse
```

**Line 2 character-by-character:**
```
S o n n e t   4 . 5     │     1 1 : 4 6   🌅     │     ⏱   1 h 4 8 m     │     + 1 2 3 / - 4 5
                        ^                 ^                 ^                 ^
                        2 spaces          2 spaces          2 spaces          2 spaces
```

**Character count:**
- Current: 68 characters
- Standard: 75 characters (+7)
- Terminal width: Usually 80+ (fits comfortably)

---

## Proposed Option C: Grouped Segments (3-4 spaces)

```
╭─ ░▒▓ 🐍 aiterm (venv: py3.14)  main 📦1 🔗origin/main ▓▒░
╰─ Sonnet 4.5 🧠  │  11:46 🌅  │  ⏱ 1h48m 🟢  │  🤖2  │  +123/-45
   ^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^
   Model group       Time group                  Activity group
```

**Visual hierarchy:**
- **Group 1 (Model):** Identity + thinking state
- **Group 2 (Time):** Clock + duration + productivity
- **Group 3 (Activity):** Agents + code changes

**Character count:**
- Grouped: 82 characters (+14 from current)
- May wrap on 80-char terminals
- Perfect for 100+ char terminals (modern default)

---

## Worktree Display Options

### Current (No worktree info)

```
╭─ 🐍 aiterm  main
```

### Option A: Count Only

```
╭─ 🐍 aiterm  main 🌳3
                   ^^^^
                   3 worktrees total
```

### Option C: Hybrid (Count + Marker)

**In main working directory:**
```
╭─ 🐍 aiterm  main 🌳3
```

**In a worktree:**
```
╭─ 🐍 aiterm (wt)  feature-auth 🌳3
                ^^^^
                Worktree marker
```

### Option E: Full Info (Compact)

```
╭─ 🐍 aiterm  feature-auth 🌳2/3
                           ^^^^
                           Worktree 2 of 3
```

---

## Real-World Examples

### Python Project (Main Directory)

**Current:**
```
╭─ 🐍 aiterm (venv: py3.14) main 📦1 🔗origin/main
╰─ Sonnet 4.5 │ 11:46 🌅 │ ⏱ 1h48m │ +123/-45 │ [learning]
```

**Standard Spacing:**
```
╭─ 🐍 aiterm (venv: py3.14)  main 📦1 🔗origin/main
╰─ Sonnet 4.5  │  11:46 🌅  │  ⏱ 1h48m  │  +123/-45  │  [learning]
```

**Grouped + Worktree:**
```
╭─ 🐍 aiterm (venv: py3.14)  main 🌳3 📦1 🔗origin/main
╰─ Sonnet 4.5 🧠  │  11:46 🌅  │  ⏱ 1h48m 🟢  │  🤖2  │  +123/-45
```

---

### R Package (Worktree, Clean)

**Current:**
```
╭─ 📦 rmediation v1.2.3  bugfix-123
╰─ Sonnet 4.5 │ 09:15 🌅 │ ⏱ 23m │ +45/-12
```

**Standard Spacing + Worktree:**
```
╭─ 📦 rmediation v1.2.3  bugfix-123 🌳2
╰─ Sonnet 4.5  │  09:15 🌅  │  ⏱ 23m  │  +45/-12
```

**Grouped + Worktree:**
```
╭─ 📦 rmediation v1.2.3 (wt)  bugfix-123 🌳2/3
╰─ Sonnet 4.5  │  09:15 🌅  │  ⏱ 23m 🟢  │  +45/-12
```

---

### Node.js (Worktree, Busy Session)

**Current:**
```
╭─ 📦 examify  dt/oauth-flow 📦3 🔗origin/dt/oauth-flow
╰─ Sonnet 4.5 │ 14:22 ☀️ │ ⏱ 2h15m │ 🤖3 │ +567/-234 │ [verbose]
```

**Standard Spacing:**
```
╭─ 📦 examify  dt/oauth-flow 📦3 🔗origin/dt/oauth-flow
╰─ Sonnet 4.5  │  14:22 ☀️  │  ⏱ 2h15m  │  🤖3  │  +567/-234  │  [verbose]
```

**Grouped + Worktree (Main):**
```
╭─ 📦 examify  dt/oauth-flow 🌳4 📦3 🔗origin/dt/oauth-flow
╰─ Sonnet 4.5  │  14:22 ☀️  │  ⏱ 2h15m 🟡  │  🤖3  │  +567/-234  │  [verbose]
```

**Grouped + Worktree (In worktree):**
```
╭─ 📦 examify (wt)  dt/oauth-flow 🌳4 📦3 🔗origin/dt/oauth-flow
╰─ Sonnet 4.5  │  14:22 ☀️  │  ⏱ 2h15m 🟡  │  🤖3  │  +567/-234  │  [verbose]
```

---

## Readability Analysis

### Eye Tracking Patterns

**Current (Cramped):**
```
Sonnet 4.5│11:46 🌅│⏱ 1h48m│+123/-45
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Continuous scan, no natural pauses
```

**Standard Spacing:**
```
Sonnet 4.5  │  11:46 🌅  │  ⏱ 1h48m  │  +123/-45
^^^^^^^^^^^    ^^^^^^^^^^    ^^^^^^^^^^    ^^^^^^^^^
Natural grouping, easier to jump to specific info
```

**Grouped:**
```
Sonnet 4.5 🧠  │  11:46 🌅  │  ⏱ 1h48m 🟢  │  🤖2  │  +123/-45
^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^
Clear semantic groups, fastest to scan
```

---

## Terminal Width Considerations

### 80-Column Terminal (Minimum)

**Current:**
```
╰─ Sonnet 4.5 │ 11:46 🌅 │ ⏱ 1h48m │ +123/-45 │ [learning]
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ (68 chars)
   ✅ Fits comfortably
```

**Standard:**
```
╰─ Sonnet 4.5  │  11:46 🌅  │  ⏱ 1h48m  │  +123/-45  │  [learning]
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ (75 chars)
   ✅ Still fits with margin
```

**Grouped:**
```
╰─ Sonnet 4.5 🧠  │  11:46 🌅  │  ⏱ 1h48m 🟢  │  🤖2  │  +123/-45
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ (82 chars)
   ⚠️ May wrap on 80-char terminals
```

### 100-Column Terminal (Modern Default)

All options fit comfortably:
- Current: 68 chars (32 chars margin)
- Standard: 75 chars (25 chars margin)
- Grouped: 82 chars (18 chars margin)

### 120-Column Terminal (IDE Default)

All options fit with plenty of room:
- Current: 68 chars (52 chars margin)
- Standard: 75 chars (45 chars margin)
- Grouped: 82 chars (38 chars margin)

---

## Accessibility Considerations

### Visual Clarity

**Current:**
- ❌ Low contrast between segments
- ❌ Hard to distinguish separator from content
- ❌ Difficult for users with visual impairments

**Standard Spacing:**
- ✅ Clear visual breaks
- ✅ Easier to focus on individual segments
- ✅ Better for dyslexic users (chunking)

**Grouped:**
- ✅ Strongest visual hierarchy
- ✅ Semantic grouping aids comprehension
- ✅ Best for ADHD users (reduced cognitive load)

### Screen Reader Support

**Current:**
```
"Sonnet four point five pipe eleven forty-six sunrise pipe..."
```

**Standard:**
```
"Sonnet four point five [pause] eleven forty-six sunrise [pause]..."
```

Extra spacing → natural pauses → better comprehension

---

## Recommendation

### ✅ **Immediate:** Implement Standard Spacing (Option A)

**Reasons:**
1. ✅ Minimal code change (1-2 lines)
2. ✅ Significant readability improvement
3. ✅ Fits all terminal widths (80+)
4. ✅ No breaking changes
5. ✅ Better accessibility

**Implementation time:** 30 minutes
**Risk:** Very low
**User impact:** High positive

---

### 🔧 **Next:** Add Worktree Count (Option C Hybrid)

**Reasons:**
1. ✅ Fills gap in current feature set
2. ✅ Minimal space usage (+4-6 chars)
3. ✅ High value for worktree users
4. ✅ Modular (can be toggled off)

**Implementation time:** 1-2 hours
**Risk:** Low
**User impact:** High for multi-worktree workflows

---

### 🚀 **Future:** Grouped Segments (Option C)

**Reasons:**
1. ⚠️ Requires refactoring segment assembly
2. ⚠️ May not fit 80-char terminals
3. ✅ Best visual hierarchy
4. ✅ Most accessible

**Implementation time:** 2-3 hours
**Risk:** Medium (breaking change)
**User impact:** Very high (if terminal width allows)

**Recommendation:** Make optional via config:
```json
{
  "display": {
    "segment_grouping": false  // Default: false for compatibility
  }
}
```

---

## Testing Checklist

- [ ] Test on 80-column terminal
- [ ] Test on 100-column terminal
- [ ] Test on 120-column terminal
- [ ] Test with all segments enabled
- [ ] Test with minimal segments
- [ ] Test with worktree count
- [ ] Test with long project names
- [ ] Test with long branch names
- [ ] Test color contrast ratios
- [ ] Get user feedback (5+ users)

---

**Created:** 2025-12-31
**Purpose:** Visual reference for spacing decision
**Related:** BRAINSTORM-statusline-spacing-worktree-2025-12-31.md
