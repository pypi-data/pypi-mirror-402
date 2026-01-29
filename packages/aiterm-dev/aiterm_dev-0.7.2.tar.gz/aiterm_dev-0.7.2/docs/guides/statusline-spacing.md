# StatusLine Spacing Guide

**Version:** v0.7.1+
**Date:** 2026-01-02

## Overview

The spacing presets system provides configurable gap control between left and right Powerlevel10k segments in the statusLine. Instead of filling the entire terminal width, you can now choose compact, balanced, or spacious spacing with an optional centered separator.

---

## What Are Spacing Presets?

Spacing presets control the **gap** between the left side (project + git) and right side (worktree) of the statusLine:

```
Before (filled):
╭─ ░▒▓ 📁 aiterm  main ▓▒░                               ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        (fills entire terminal width)

After (spacing preset):
╭─ ░▒▓ 📁 aiterm  main ▓▒░            …           ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^^^^^^^^^^^^^^
                        (fixed gap with separator)
```

### Key Benefits

- **Visual clarity** - Controlled whitespace instead of stretched segments
- **Consistency** - Same gap size across different terminal widths
- **Optional separator** - Subtle `…` marker in the gap center
- **Smart constraints** - Min/max limits prevent extremes

---

## Quick Start

### Apply a Preset

```bash
# Tight spacing (15% of terminal width, 5-20 char gap)
ait statusline config spacing minimal

# Balanced spacing (20% of terminal width, 10-40 char gap) [DEFAULT]
ait statusline config spacing standard

# Wide spacing (30% of terminal width, 15-60 char gap)
ait statusline config spacing spacious

# Preview the changes
ait statusline test
```

### Disable the Separator

If you prefer plain spaces without the centered `…` marker:

```bash
ait statusline config set spacing.show_separator false
```

---

## Presets Reference

| Preset | Base Gap | Min Gap | Max Gap | Use Case |
|--------|----------|---------|---------|----------|
| **minimal** | 15% of width | 5 chars | 20 chars | Compact, information-dense |
| **standard** | 20% of width | 10 chars | 40 chars | Balanced (default) |
| **spacious** | 30% of width | 15 chars | 60 chars | Wide, maximum clarity |

### How Gap Calculation Works

1. **Base calculation:** `gap = terminal_width × base_percent`
2. **Constraints applied:** `gap = max(min_gap, min(gap, max_gap))`
3. **Separator rendering:** If enabled and `gap >= 3`, add centered `…`

**Example (standard preset, 120-column terminal):**
```
gap = 120 × 0.20 = 24 chars
constraints: max(10, min(24, 40)) = 24 chars
result: 24-char gap with centered separator
```

---

## Manual Configuration

### Override Min/Max Constraints

```bash
# Set custom minimum gap
ait statusline config set spacing.min_gap 12

# Set custom maximum gap
ait statusline config set spacing.max_gap 50

# Verify settings
ait statusline config get spacing.min_gap
ait statusline config get spacing.max_gap
```

### View All Spacing Settings

```bash
ait statusline config list | grep spacing
```

Output:
```
spacing.mode: standard
spacing.min_gap: 10
spacing.max_gap: 40
spacing.show_separator: true
```

---

## Visual Examples

### Terminal Width: 80 Columns

#### Minimal Preset (15%)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░     …    ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^
                        12 chars (80 × 0.15)
```

#### Standard Preset (20%)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░        …        ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^^^^^^^^
                        16 chars (80 × 0.20)
```

#### Spacious Preset (30%)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░            …            ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        24 chars (80 × 0.30)
```

### Terminal Width: 120 Columns

#### Standard Preset (20%)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░            …           ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^^^^^^^^^^^^^^
                        24 chars (120 × 0.20)
```

### Terminal Width: 180 Columns

#### Spacious Preset (30%)
```
╭─ ░▒▓ 📁 aiterm  main ▓▒░                        …                       ░▒▓ (wt) feature ▓▒░
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        54 chars (180 × 0.30)
```

---

## Narrow Terminal Behavior

On very narrow terminals, the spacing system gracefully degrades:

### Insufficient Space for Right Side

If there's not enough room for `left + gap + right`, the gap shrinks to fit:

```bash
# Terminal: 60 columns, standard preset wants 12 chars
# Available: 60 - 25 (left) - 18 (right) = 17 chars
# Result: Uses 17-char gap instead of 12
```

### Extreme Narrow (< 50 columns)

Falls back to left-only display if right side doesn't fit:

```bash
# Terminal: 40 columns
# Left side: 25 chars (project + git)
# Right side won't fit
# Result: Shows only left side
╭─ ░▒▓ 📁 aiterm  main ▓▒░
```

---

## Configuration Reference

### All Spacing Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `spacing.mode` | str | `standard` | Preset name (minimal/standard/spacious) |
| `spacing.min_gap` | int | `10` | Minimum gap in chars (narrow terminal fallback) |
| `spacing.max_gap` | int | `40` | Maximum gap in chars (wide terminal cap) |
| `spacing.show_separator` | bool | `true` | Show centered `…` separator in gap |

### Get/Set Commands

```bash
# Get current preset
ait statusline config get spacing.mode

# Set preset
ait statusline config spacing minimal

# Get min gap
ait statusline config get spacing.min_gap

# Set custom min gap
ait statusline config set spacing.min_gap 15

# Disable separator
ait statusline config set spacing.show_separator false

# List all spacing settings
ait statusline config list | grep spacing
```

---

## Common Workflows

### 1. Switch to Compact Layout

```bash
ait statusline config spacing minimal
ait statusline config set spacing.max_gap 15
ait statusline test
```

### 2. Wide Layout with No Separator

```bash
ait statusline config spacing spacious
ait statusline config set spacing.show_separator false
ait statusline test
```

### 3. Custom Balanced Layout

```bash
ait statusline config spacing standard
ait statusline config set spacing.min_gap 12
ait statusline config set spacing.max_gap 30
ait statusline test
```

### 4. Reset to Defaults

```bash
ait statusline config spacing standard
ait statusline config set spacing.min_gap 10
ait statusline config set spacing.max_gap 40
ait statusline config set spacing.show_separator true
ait statusline test
```

---

## Troubleshooting

### Gap is Too Small

**Problem:** Gap is always at minimum despite wide terminal

**Solution:** Check if a custom `spacing.min_gap` override is set:
```bash
ait statusline config get spacing.min_gap
# If not 10 (standard default), reset:
ait statusline config set spacing.min_gap 10
```

### Gap is Too Large

**Problem:** Gap takes up too much space

**Solution:** Switch to minimal preset or lower max gap:
```bash
ait statusline config spacing minimal
# Or set custom max:
ait statusline config set spacing.max_gap 25
```

### Separator Not Showing

**Problem:** No `…` separator appears in gap

**Possible causes:**

1. **Separator disabled:**
   ```bash
   ait statusline config get spacing.show_separator
   # If false, enable:
   ait statusline config set spacing.show_separator true
   ```

2. **Gap too small (< 3 chars):**
   - Separator requires minimum 3-char gap
   - Increase terminal width or use larger preset

3. **Right side not visible:**
   - Check if you're in a worktree (separator only shows when right side exists)
   - Verify with: `ait feature status`

### Right Side Not Showing

**Problem:** Only left side visible, no worktree context

**Possible causes:**

1. **Not in a worktree:**
   - Right side only appears in git worktrees
   - Check: `git worktree list`

2. **Worktree display disabled:**
   ```bash
   ait statusline config get git.show_worktrees
   # If false, enable:
   ait statusline config set git.show_worktrees true
   ```

3. **Terminal too narrow:**
   - Increase terminal width to at least 80 columns

---

## Implementation Details

### Gap Calculation Algorithm

```python
def _calculate_gap(self, terminal_width: int) -> int:
    """Calculate gap size between left and right segments."""
    # Get preset parameters
    mode = self.config.get('spacing.mode', 'standard')
    preset = SPACING_PRESETS[mode]

    # Calculate base gap
    gap = int(terminal_width * preset['base_percent'])

    # Apply constraints
    min_gap = self.config.get('spacing.min_gap', preset['min_gap'])
    max_gap = self.config.get('spacing.max_gap', preset['max_gap'])
    gap = max(min_gap, min(gap, max_gap))

    return gap
```

### Separator Rendering

```python
def _render_gap(self, gap_size: int) -> str:
    """Render gap with optional centered separator."""
    if not self.config.get('spacing.show_separator', True):
        return ' ' * gap_size

    if gap_size < 3:
        # Too small for separator
        return ' ' * gap_size

    # Centered separator
    center = gap_size // 2
    left_spaces = center - 1
    right_spaces = gap_size - center

    return f"{' ' * left_spaces}…{' ' * right_spaces}"
```

### ANSI Code Handling

The spacing system properly strips ANSI escape codes when calculating visible width:

```python
def _strip_ansi_length(self, text: str) -> int:
    """Get visible character count (strip ANSI codes)."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', text))
```

This ensures accurate gap sizing even with colored/styled text.

---

## Related Documentation

- **Minimal StatusLine Guide:** [statusline-minimal.md](statusline-minimal.md)
- **StatusLine Configuration Reference:** See `ait statusline config --help`
- **Feature Workflow Guide:** [Feature Workflow](../guide/feature-workflow.md)
- **Implementation Spec:** [SPEC-statusline-spacing-2026-01-02.md](../specs/SPEC-statusline-spacing-2026-01-02.md)

---

## Version History

### v0.7.1 (2026-01-02)
- ✅ Initial release of spacing presets system
- ✅ 3 presets: minimal, standard, spacious
- ✅ Dynamic gap calculation with constraints
- ✅ Optional centered separator
- ✅ 12 comprehensive tests

---

**See also:**
- `ait statusline --help`
- `ait statusline config --help`
- `ait statusline test` - Preview your spacing
