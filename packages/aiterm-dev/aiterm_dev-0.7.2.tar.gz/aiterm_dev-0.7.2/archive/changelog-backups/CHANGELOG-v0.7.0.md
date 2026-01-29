# Changelog - v0.7.0 (2026-01-01)

## Minimal StatusLine Redesign

This release streamlines the statusLine by removing visual clutter and adding adaptive Powerlevel10k-style worktree display on the right side.

---

## 🎉 New Features

### 1. Minimal Preset Command

**Quick declutter:**
```bash
ait statusline config preset minimal
```

**Disables:**
- Session duration (`⏱ 12m`)
- Current time (`14:32`)
- Lines changed (`+123/-45`)
- Session usage stats
- Weekly usage stats
- Usage reset timer

**Result:** Clean, focused statusLine with only essential context.

---

### 2. Right-Side Worktree Display

**Adaptive layout:**
- **Main branch:** Minimal display (no right side)
- **Worktree:** Right-side segment shows `░▒▓ (wt) <name> ▓▒░`

**Visual:**
```text
Main:     ╭─ ░▒▓ 📁 aiterm  main ▓▒░
          ╰─ Sonnet 4.5

Worktree: ╭─ ░▒▓ 📁 aiterm  feature-auth ▓▒░          ░▒▓ (wt) feature-auth ▓▒░
          ╰─ Sonnet 4.5
```

**Features:**
- Powerlevel10k reversed segments (`░▒▓`)
- Auto-detects worktree context
- Shows worktree count in main branch (when > 1)
- Terminal width auto-detection with fallback

---

### 3. Smart Branch Truncation

**Before (simple truncation):**
```
feature/authentication-sy...
```

**After (smart truncation):**
```
feature/...stem-oauth2
```

**How it works:**
- Preserves first 10 chars (e.g., `feature/`)
- Preserves last N chars (e.g., `oauth2`)
- Inserts `...` in middle
- Result: Both prefix AND suffix visible

**Config:**
```bash
ait statusline config set git.truncate_branch_length 32
```

---

## 🗑️ Removed

### Left-Side Worktree Marker

**Before:** `📁 aiterm (wt)  feature-auth`
**After:** `📁 aiterm  feature-auth`

**Reason:** Worktree context moved to right-side display (no duplication)

---

## 📊 Impact

### Character Count

| Context | Before | After | Reduction |
|---------|--------|-------|-----------|
| Main branch | ~80 chars | ~40 chars | **50%** |
| Worktree | ~80 chars | ~80 chars | 0% (but better layout) |

### Metrics Displayed

| Version | Essential | Bloat | Total |
|---------|-----------|-------|-------|
| v0.6.3 | 3 | 5 | 8 |
| v0.7.0 (minimal) | 3 | 0 | 3 |

**Essential metrics:**
- Model name (Sonnet 4.5)
- Project name/icon (📁 aiterm)
- Git branch (main, feature-auth)

**Removed bloat:**
- Session duration
- Current time
- Lines changed
- Battery %
- Cost data

---

## 🧪 Testing

**New tests:** 24 comprehensive tests (all passing)

**Coverage:**
- Smart branch truncation (5 tests)
- Worktree detection (2 tests)
- Right-side rendering (3 tests)
- ANSI code stripping (5 tests)
- Line alignment (3 tests)
- Adaptive display (3 tests)
- Config preset (1 test)
- Integration tests (2 tests)

**Command:**
```bash
pytest tests/test_statusline_worktree.py -v
# 24 passed in 0.17s ✅
```

---

## 📚 Documentation

### New Files

1. **[docs/guides/statusline-minimal.md](docs/guides/statusline-minimal.md)**
   - Complete user guide
   - Visual examples
   - Configuration options
   - Troubleshooting
   - FAQ

2. **[BRAINSTORM-statusline-redesign-2026-01-01.md](BRAINSTORM-statusline-redesign-2026-01-01.md)**
   - Design brainstorm
   - 11 implementation ideas
   - Architecture diagrams
   - Before/after comparison

3. **[docs/specs/SPEC-statusline-redesign-2026-01-01.md](docs/specs/SPEC-statusline-redesign-2026-01-01.md)**
   - Implementation spec
   - User stories
   - Technical requirements
   - Code examples
   - Review checklist

### Updated Files

- **[CLAUDE.md](CLAUDE.md)** - Added v0.7.0 feature overview

---

## 🔧 Implementation Details

### Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `src/aiterm/cli/statusline.py` | Added `preset` command | +68 |
| `src/aiterm/statusline/segments.py` | Smart truncation + worktree detection | +69 |
| `src/aiterm/statusline/renderer.py` | Right-side rendering architecture | +87 |
| `tests/test_statusline_worktree.py` | Comprehensive test suite | +374 |

### Key Methods Added

**Segments:**
- `_truncate_branch(branch, max_len)` - Smart truncation
- `_get_worktree_name(cwd)` - Extract worktree name
- `_is_worktree(cwd)` - Check if in worktree (already existed, enhanced)

**Renderer:**
- `_build_right_segments(cwd, git_segment)` - Build right-side content
- `_render_right_segment(content)` - Format with P10k style
- `_align_line(left, right)` - Calculate padding
- `_strip_ansi_length(text)` - ANSI code stripping for alignment

---

## 🚀 Usage

### Quick Start

```bash
# Apply minimal preset
ait statusline config preset minimal

# Restart Claude Code
# (StatusLine will update automatically)
```

### Create a Worktree

```bash
# Create worktree
git worktree add ../aiterm-feature feature/auth-system

# Switch to it
cd ../aiterm-feature

# StatusLine shows:
# ╭─ ░▒▓ 📁 aiterm  feature/auth-system ▓▒░          ░▒▓ (wt) feature-auth-system ▓▒░
# ╰─ Sonnet 4.5
```

### Customize

```bash
# Adjust truncation length
ait statusline config set git.truncate_branch_length 40

# Toggle worktree display
ait statusline config set git.show_worktrees false

# Re-enable specific metrics
ait statusline config set display.show_current_time true
```

---

## 🐛 Bug Fixes

None - This is a feature release.

---

## ⚠️ Breaking Changes

None - All changes are backward compatible. Existing configurations continue to work.

**Note:** The minimal preset changes configuration, but users must explicitly apply it (`ait statusline config preset minimal`).

---

## 🔮 Future Enhancements

**Planned for v0.8.0:**

1. **Theme-aware right-side colors**
   - Currently uses fixed dark gray (235/245)
   - Future: Match theme colors

2. **Vertical stacking for narrow terminals**
   - When terminal < 100 cols, stack right segments on line 2
   - Prevents truncation

3. **Worktree color coding**
   - Different background colors for main vs worktree
   - Visual distinction to prevent accidental commits

4. **Worktree branch comparison**
   - Show ahead/behind relative to main (e.g., `↑3 ↓1`)

---

## 📦 Installation

```bash
# Homebrew (macOS)
brew upgrade data-wise/tap/aiterm

# PyPI
pip install --upgrade aiterm-dev

# Curl installer
curl -fsSL https://raw.githubusercontent.com/Data-Wise/aiterm/main/install.sh | bash
```

---

## 🙏 Acknowledgments

Design inspired by:
- **Powerlevel10k** - Right-side segment styling
- **ADHD-friendly workflows** - Minimal clutter philosophy
- **Git worktree workflows** - Adaptive context display

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

**Full Changelog:** <https://github.com/Data-Wise/aiterm/compare/v0.6.3...v0.7.0>
