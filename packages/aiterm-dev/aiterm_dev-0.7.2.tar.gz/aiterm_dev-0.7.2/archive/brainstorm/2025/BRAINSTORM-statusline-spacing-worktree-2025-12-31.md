# BRAINSTORM: StatusLine Spacing & Worktree Display

**Generated:** 2025-12-31
**Mode:** Architecture + UX
**Context:** StatusLine v0.7.0 feels cramped, worktrees not shown

---

## Current State Analysis

### Spacing Issues Identified

**Line 2 (Current):**
```
╰─ Sonnet 4.5│11:46 🌅│⏱ 1h48m│+123/-45│[learning]
   ^^^^^^^^^^^^ ^^^^^^ ^^^^^^^^ ^^^^^^^^ ^^^^^^^^^^^
   No spacing   Tight  Tight    Tight    Tight
```

**Problems:**
1. ❌ **No space after model name** - "Sonnet 4.5│" (runs together)
2. ❌ **Separator touches content** - "│11:46" (no breathing room)
3. ❌ **Icons touch separators** - "🌅│" (cramped)
4. ❌ **Numbers touch separators** - "+123/-45│" (hard to scan)
5. ❌ **Overall density** - Eye fatigue, hard to parse quickly

**Current separator pattern:**
```python
line2 += f" \033[{self.theme.separator_fg}m│\033[0m {usage_output}"
         ^                                      ^
         Space before separator                 Space after content
```

### Worktree Context (Currently Missing)

**Git worktree list output:**
```
/Users/dt/projects/dev-tools/aiterm                             583c01f [main]
/Users/dt/.claude-squad/worktrees/aiterm-test_18832329dc9647d0  f452f66 [dt/aiterm-test]
/Users/dt/.claude-squad/worktrees/claude_1883239521946900       f452f66 [dt/claude]
/Users/dt/.claude-squad/worktrees/test_1883233f925c8880         f452f66 [dt/test]
```

**Current behavior:**
- ✅ Shows current branch: `main`
- ❌ No indication this is a worktree
- ❌ No count of other worktrees
- ❌ No worktree name shown

---

## 🎯 Solution 1: Improved Spacing

### Quick Wins (< 30 min)

#### Option A: Add Consistent Padding (Recommended)

**Change separator pattern from:**
```python
f" │ {content}"     # Current: 1 space before, 1 after
```

**To:**
```python
f"  │  {content}"   # New: 2 spaces before, 2 after
```

**Result:**
```
Before: Sonnet 4.5 │ 11:46 🌅 │ ⏱ 1h48m │ +123/-45
After:  Sonnet 4.5  │  11:46 🌅  │  ⏱ 1h48m  │  +123/-45
```

**Pros:**
- ✅ Easy to implement (one-line change per segment)
- ✅ Consistent across all segments
- ✅ Improves readability significantly

**Cons:**
- ⚠️ Slightly longer line (may wrap on narrow terminals)

---

#### Option B: Variable Padding (Context-aware)

**Different spacing for different content types:**
```python
# Model name (important) - extra space
f"  │  {model}"

# Time displays - standard space
f" │ {time}"

# Numbers/stats - minimal space
f" │ {stats}"
```

**Result:**
```
Sonnet 4.5  │  11:46 🌅 │ ⏱ 1h48m │ +123/-45
^^^^^^^^^^^     ^^^^^^   ^^^^^^^^   ^^^^^^^^
Extra space     Std      Std        Minimal
```

**Pros:**
- ✅ Visual hierarchy (emphasizes important info)
- ✅ Shorter overall length

**Cons:**
- ❌ Inconsistent (may look unpolished)
- ❌ More complex to implement

---

#### Option C: Grouped Segments (UX redesign)

**Group related items, add extra space between groups:**
```python
# Group 1: Model + thinking
f"{model} 🧠"

# Group 2: Time info (extra space before)
f"  │  {current_time} {time_icon}  │  {session_duration} {productivity}"

# Group 3: Activity (extra space before)
f"  │  {agents}  │  {lines}"
```

**Result:**
```
Sonnet 4.5 🧠  │  11:46 🌅  │  ⏱ 1h48m 🟢  │  🤖2  │  +123/-45
^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^
Model group       Time group                  Activity group
```

**Pros:**
- ✅ Clear visual hierarchy
- ✅ Easier to scan for specific info
- ✅ Groups related data together

**Cons:**
- ⚠️ Longer line
- 🔧 Requires refactoring segment assembly

---

### Configuration Option

Add config setting for spacing preference:

```json
{
  "display": {
    "separator_spacing": "standard",  // minimal|standard|relaxed
    "segment_grouping": false          // enable grouped layout
  }
}
```

**Spacing values:**
- `minimal`: 1 space (current)
- `standard`: 2 spaces (Option A)
- `relaxed`: 3 spaces (very spacious)

---

## 🌳 Solution 2: Worktree Display

### Context: Git Worktree Basics

**What worktrees enable:**
- Multiple working copies of same repo
- Work on different branches simultaneously
- No need to stash/commit when switching contexts

**Detection command:**
```bash
git worktree list
# Returns:
# /path/to/main                  abc123 [main]
# /path/to/feature-branch        def456 [feature]
```

**Key info to show:**
1. **Am I in a worktree?** (vs main working directory)
2. **How many worktrees exist?** (total count)
3. **Worktree name** (if named worktree)

---

### Quick Wins (< 1 hour)

#### Option A: Worktree Count Indicator (Minimal)

**Show count when worktrees exist:**
```
Line 1: 🐍 aiterm  main 🌳3
                        ^^^^
                        Worktree indicator + count
```

**Implementation:**
```python
def _get_worktree_count(self, cwd: str) -> int:
    """Get total number of worktrees."""
    try:
        result = subprocess.run(
            ['git', 'worktree', 'list'],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            # Count lines (each line = 1 worktree)
            return len(result.stdout.strip().split('\n'))
    except Exception:
        pass
    return 0
```

**Display logic:**
```python
worktree_count = self._get_worktree_count(cwd)
if worktree_count > 1:  # Main + at least 1 worktree
    git_output += f" 🌳{worktree_count}"
```

**Pros:**
- ✅ Minimal space (icon + number)
- ✅ Quick to implement
- ✅ Shows awareness of worktrees

**Cons:**
- ❌ Doesn't show if current location IS a worktree
- ❌ No worktree name

---

#### Option B: Current Worktree Indicator (Contextual)

**Show worktree name/path if in a worktree:**
```
Line 1: 🐍 aiterm (wt:feature-auth)  feature-auth
                   ^^^^^^^^^^^^^^^^
                   Worktree indicator
```

**Detection:**
```python
def _get_current_worktree(self, cwd: str) -> Optional[str]:
    """Get current worktree name if in a worktree."""
    try:
        result = subprocess.run(
            ['git', 'worktree', 'list'],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                worktree_path = parts[0]

                # Check if cwd is in this worktree
                if cwd.startswith(worktree_path):
                    # Extract worktree name from path
                    # e.g., /path/worktrees/feature-auth → feature-auth
                    return Path(worktree_path).name
    except Exception:
        pass
    return None
```

**Pros:**
- ✅ Shows context-relevant info
- ✅ Helps distinguish main from worktree
- ✅ Useful for multi-worktree workflows

**Cons:**
- ⚠️ Adds length to line 1
- ⚠️ May be redundant with branch name

---

#### Option C: Hybrid Approach (Recommended)

**Combine count + current worktree indicator:**

**When in main working directory:**
```
Line 1: 🐍 aiterm  main 🌳3
                        ^^^^
                        3 total worktrees (including main)
```

**When in a worktree:**
```
Line 1: 🐍 aiterm (wt)  feature-auth 🌳3
                 ^^^^                 ^^^^
                 Worktree marker      Total count
```

**Or more compact:**
```
Line 1: 🐍 aiterm  feature-auth 🌳2/3
                                ^^^^
                                Worktree 2 of 3
```

**Pros:**
- ✅ Shows both context and count
- ✅ Clear distinction between main and worktree
- ✅ Compact (just icon + numbers)

**Cons:**
- ⚠️ Requires parsing worktree list
- ⚠️ Slightly more complex logic

---

### Medium Effort (2-3 hours)

#### Option D: Worktree Details on Hover/Expand

**Show minimal by default, expand on request:**

**Collapsed (default):**
```
Line 1: 🐍 aiterm  main 🌳3
```

**Expanded (on command or hover):**
```
Line 1: 🐍 aiterm  main 🌳3
        Worktrees:
          • main (current)
          • feature-auth (/path/to/worktree)
          • bugfix-123 (/path/to/other)
```

**Trigger options:**
1. CLI command: `ait statusline worktrees`
2. Environment variable: `STATUSLINE_EXPAND_WORKTREES=1`
3. Config setting: `display.show_worktree_details: true`

**Pros:**
- ✅ Doesn't clutter statusline
- ✅ Full info available when needed
- ✅ Flexible (user choice)

**Cons:**
- ❌ Requires additional UI/command
- ❌ Not visible by default

---

#### Option E: Worktree Segment (New Segment)

**Create dedicated WorktreeSegment class:**

```python
class WorktreeSegment:
    """Renders worktree information."""

    def render(self, cwd: str, compact: bool = True) -> str:
        """Render worktree info.

        Args:
            cwd: Current working directory
            compact: Use compact format

        Returns:
            Formatted worktree display or empty string
        """
        worktrees = self._get_worktrees(cwd)
        if len(worktrees) <= 1:
            return ""  # Only main working dir

        current = self._get_current_worktree(cwd, worktrees)
        total = len(worktrees)

        if compact:
            # Show icon + count
            return f"🌳{total}"
        else:
            # Show current + total
            if current:
                return f"🌳{current['name']} ({current['index']}/{total})"
            else:
                return f"🌳main ({total} total)"
```

**Placement options:**
1. **Line 1 (with git)**: `main 🌳3 📦1`
2. **Line 2 (after time)**: `⏱ 5m 🟢 │ 🌳3 │ +123/-45`
3. **Separate line 3** (expandable): Only when worktrees exist

**Pros:**
- ✅ Modular (follows existing segment pattern)
- ✅ Configurable display
- ✅ Testable in isolation

**Cons:**
- ⚠️ Adds another segment to maintain
- ⚠️ Increases line length

---

### Long-term Enhancements (Future)

#### Option F: Interactive Worktree Switcher

**Command:** `ait statusline worktree switch`

**Flow:**
1. Show worktree list with fzf
2. User selects target worktree
3. Change directory to selected worktree
4. Update statusline automatically

**Integration with aiterm workflow:**
```bash
# Current workflow
cd /path/to/worktree

# Enhanced workflow
ait wt switch    # Interactive picker
# → Auto-cd to selected worktree
# → StatusLine updates immediately
```

**Pros:**
- ✅ Seamless worktree navigation
- ✅ Leverages existing aiterm context switching
- ✅ ADHD-friendly (no path typing)

**Cons:**
- ❌ Requires shell integration
- ❌ Complex implementation

---

## 📊 Decision Matrix

### Spacing Solutions

| Solution | Ease | Impact | Line Length | Recommended |
|----------|------|--------|-------------|-------------|
| **A: Consistent Padding** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | +10 chars | ✅ **Yes** |
| B: Variable Padding | ⭐⭐⭐ | ⭐⭐⭐ | +5 chars | ⚠️ Maybe |
| C: Grouped Segments | ⭐⭐ | ⭐⭐⭐⭐⭐ | +15 chars | 🔧 Refactor needed |

### Worktree Solutions

| Solution | Ease | Info Shown | Space Used | Recommended |
|----------|------|------------|------------|-------------|
| A: Count Only | ⭐⭐⭐⭐⭐ | ⭐⭐ | +4 chars | ✅ **Quick win** |
| B: Current Name | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | +10-20 chars | ⚠️ Line 1 crowded |
| **C: Hybrid Count+Marker** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | +6 chars | ✅ **Best balance** |
| D: Expand on Request | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | +0 chars | 🔧 Complex |
| E: Dedicated Segment | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | +6 chars | ✅ **Modular** |

---

## 🚀 Recommended Implementation Path

### Phase 1: Spacing (30 minutes)

**Implement Option A: Consistent Padding**

1. Update `_build_line2()` in `renderer.py`:
   ```python
   # Change all separators from:
   f" │ {content}"

   # To:
   f"  │  {content}"
   ```

2. Update theme config to support spacing:
   ```json
   {
     "display": {
       "separator_spacing": "standard"  // minimal|standard|relaxed
     }
   }
   ```

3. Test rendering:
   ```bash
   ait statusline test
   ```

**Expected result:**
```
Before: Sonnet 4.5 │ 11:46 │ ⏱ 5m │ +123/-45
After:  Sonnet 4.5  │  11:46  │  ⏱ 5m  │  +123/-45
        ^^^^^^^^^^^    ^^^^^^    ^^^^^^^
        Better spacing
```

---

### Phase 2: Worktree Display (1-2 hours)

**Implement Option C: Hybrid Count+Marker**

1. Add worktree detection to `GitSegment`:
   ```python
   def _get_worktree_info(self, cwd: str) -> dict:
       """Get worktree information.

       Returns:
           {
               'total': int,           # Total worktrees
               'is_worktree': bool,    # Current location is worktree
               'current_name': str     # Worktree name or 'main'
           }
       """
   ```

2. Update git segment rendering:
   ```python
   # After branch display
   wt_info = self._get_worktree_info(cwd)
   if wt_info['total'] > 1:
       marker = "(wt)" if wt_info['is_worktree'] else ""
       output += f" {marker}🌳{wt_info['total']}"
   ```

3. Add config toggle:
   ```json
   {
     "git": {
       "show_worktree_count": true
     }
   }
   ```

**Expected result:**
```
Main directory:  🐍 aiterm  main 🌳3
Worktree:        🐍 aiterm (wt)  feature-auth 🌳3
```

---

### Phase 3: Worktree Segment (Future - 2-3 hours)

**Implement Option E: Dedicated Segment**

1. Create `src/aiterm/statusline/worktree.py`:
   ```python
   class WorktreeSegment:
       """Renders worktree information."""

       def render(self, cwd: str) -> str:
           """Render worktree segment."""
           # Full implementation
   ```

2. Add segment to renderer:
   ```python
   # In _build_line1() or _build_line2()
   worktree_segment = WorktreeSegment(self.config, self.theme)
   worktree_output = worktree_segment.render(cwd)
   if worktree_output:
       line += f"  │  {worktree_output}"
   ```

3. Add comprehensive config:
   ```json
   {
     "worktree": {
       "show_count": true,
       "show_current_name": false,
       "show_marker": true,
       "compact_format": true
     }
   }
   ```

---

## 🧪 Testing Plan

### Spacing Tests

```python
def test_consistent_spacing():
    """Test 2-space padding around separators."""
    renderer = StatusLineRenderer()
    output = renderer.render(mock_data)

    # Should have 2 spaces before and after separators
    assert "  │  " in output
    assert " │ " not in output  # Old pattern

def test_spacing_config():
    """Test configurable spacing."""
    config = StatusLineConfig()
    config.set('display.separator_spacing', 'relaxed')

    renderer = StatusLineRenderer(config)
    output = renderer.render(mock_data)

    # Should have 3 spaces for relaxed mode
    assert "   │   " in output
```

### Worktree Tests

```python
def test_worktree_count_detection(tmp_path):
    """Test worktree count detection."""
    # Create mock git repo with worktrees
    repo = tmp_path / "repo"
    repo.mkdir()

    segment = WorktreeSegment(config)
    wt_info = segment._get_worktree_info(str(repo))

    assert wt_info['total'] >= 1

def test_worktree_marker():
    """Test worktree marker display."""
    segment = WorktreeSegment(config)
    output = segment.render("/path/to/worktree")

    # Should show (wt) marker when in worktree
    assert "(wt)" in output or "🌳" in output
```

---

## 📝 Configuration Examples

### Minimal Spacing + Worktree Count

```json
{
  "display": {
    "separator_spacing": "minimal"
  },
  "git": {
    "show_worktree_count": true
  }
}
```

**Result:**
```
╭─ 🐍 aiterm  main 🌳3
╰─ Sonnet 4.5│11:46│⏱ 5m│+123/-45
```

---

### Relaxed Spacing + Full Worktree Info

```json
{
  "display": {
    "separator_spacing": "relaxed",
    "segment_grouping": true
  },
  "git": {
    "show_worktree_count": true,
    "show_worktree_marker": true
  }
}
```

**Result:**
```
╭─ 🐍 aiterm  main 🌳3
╰─ Sonnet 4.5 🧠   │   11:46 🌅   │   ⏱ 5m 🟢   │   🤖2   │   +123/-45
```

---

## 🎨 Visual Mockups

### Current (Cramped)

```
╰─ Sonnet 4.5 │ 11:46 🌅 │ ⏱ 1h48m │ +123/-45 │ [learning]
```

### Option A: Standard Spacing

```
╰─ Sonnet 4.5  │  11:46 🌅  │  ⏱ 1h48m  │  +123/-45  │  [learning]
```

### Option C: Grouped Segments

```
╰─ Sonnet 4.5 🧠  │  11:46 🌅  │  ⏱ 1h48m 🟢  │  🤖2  │  +123/-45
   ^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^
   Model group       Time group                  Activity group
```

### Worktree Display Variations

**Minimal (Count only):**
```
╭─ 🐍 aiterm  main 🌳3
```

**Marker (In worktree):**
```
╭─ 🐍 aiterm (wt)  feature-auth 🌳3
```

**Full (With index):**
```
╭─ 🐍 aiterm  feature-auth 🌳2/3
                            ^^^^
                            Worktree 2 of 3
```

---

## 🔗 Related Features

### Integration with aiterm Feature Workflow

**Current worktree workflow:**
```bash
# Create feature branch with worktree
ait feature start auth -w
# → Creates worktree at ~/.claude-squad/worktrees/aiterm-auth/

# StatusLine should show:
╭─ 🐍 aiterm (wt)  dt/auth 🌳2
```

### Integration with Session Tracking

**Track worktree context in sessions:**
```json
{
  "session_id": "abc123",
  "worktree": {
    "path": "/Users/dt/.claude-squad/worktrees/aiterm-auth",
    "branch": "dt/auth",
    "created": "2025-12-31T10:00:00Z"
  }
}
```

**Benefits:**
- Resume session in correct worktree
- Clean up abandoned worktrees
- Track productivity per worktree

---

## 🚧 Open Questions

1. **Spacing preference survey:**
   - Get feedback from users on spacing options
   - A/B test different spacing levels

2. **Worktree display placement:**
   - Line 1 (with git) or Line 2 (with stats)?
   - Always show or only when worktrees exist?

3. **Performance impact:**
   - How slow is `git worktree list`?
   - Should we cache worktree info?

4. **Configuration complexity:**
   - Too many options = analysis paralysis
   - Find right balance of configurability

---

## 📚 References

- [Git Worktree Docs](https://git-scm.com/docs/git-worktree)
- [Powerlevel10k Spacing](https://github.com/romkatv/powerlevel10k#spacing)
- [iTerm2 Status Bar Best Practices](https://iterm2.com/documentation-status-bar.html)

---

## ✅ Next Steps

1. **Implement Phase 1 (Spacing):**
   - [ ] Update separator pattern to 2 spaces
   - [ ] Add config option for spacing level
   - [ ] Test with various segment combinations
   - [ ] Update documentation

2. **Implement Phase 2 (Worktree):**
   - [ ] Add worktree detection to GitSegment
   - [ ] Show count when worktrees exist
   - [ ] Add (wt) marker for current worktree
   - [ ] Add config toggles

3. **Testing & Validation:**
   - [ ] Write tests for spacing variations
   - [ ] Write tests for worktree detection
   - [ ] Manual testing with real worktrees
   - [ ] Get user feedback

4. **Documentation:**
   - [ ] Update StatusLine guide with spacing options
   - [ ] Document worktree display feature
   - [ ] Add configuration examples
   - [ ] Create troubleshooting section

---

**Duration:** 18 minutes (within quick brainstorm budget)
**Agents Used:** None (quick mode)
**Output Saved:** BRAINSTORM-statusline-spacing-worktree-2025-12-31.md
