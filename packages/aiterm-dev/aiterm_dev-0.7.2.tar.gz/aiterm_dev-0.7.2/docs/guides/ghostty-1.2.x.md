# Ghostty 1.2.x Integration Guide

This guide covers the new Ghostty 1.2.x features supported in aiterm v0.7.2.

## New Configuration Keys

### macOS Titlebar Style

Ghostty 1.2.x introduces support for macOS Tahoe's new titlebar styles.

```bash
# View current setting
ait ghostty config | grep "Titlebar Style"

# Set to tabs style (Tahoe)
ait ghostty set macos-titlebar-style tabs

# Set to native style (default)
ait ghostty set macos-titlebar-style native
```

**Options:**

- `native` - Standard macOS titlebar (default)
- `tabs` - Tahoe-style integrated tabs

### Background Image

Set a background image for your terminal.

```bash
# Set background image
ait ghostty set background-image ~/Pictures/terminal-bg.jpg

# Remove background image
ait ghostty set background-image ""
```

**Tips:**

- Use absolute paths for images
- Combine with `background-opacity` for subtle effects
- Supported formats: JPG, PNG

### Mouse Scroll Multiplier

Fine-tune scroll sensitivity for precision devices like Apple trackpads.

```bash
# View current multiplier
ait ghostty config | grep "Scroll Multiplier"

# Set to 2x speed
ait ghostty set mouse-scroll-multiplier 2.0

# Set to 0.5x speed (slower)
ait ghostty set mouse-scroll-multiplier 0.5
```

**Default:** `1.0`

## Native Progress Bars (OSC 9;4)

Ghostty 1.2.x supports graphical progress bars via OSC 9;4 escape sequences. aiterm automatically enables this for Ghostty users in the Claude Code status bar.

### Lines Changed Progress

When using Claude Code, the status bar will show a native progress bar for code changes:

- **Green bar**: More lines added than removed (success)
- **Red bar**: More lines removed than added (error)
- **Percentage**: Ratio of lines added to total changes

### Usage Tracking Progress

API usage is displayed as a progress bar:

- **Normal (blue)**: Usage below warning threshold
- **Warning (red)**: Usage at or above threshold (default: 80%)

### Configuration

Progress bars are automatically enabled when Ghostty is detected. No configuration needed!

## Profile Support

All new 1.2.x settings are fully supported in Ghostty profiles.

```bash
# Create a profile with Tahoe settings
ait ghostty profile create tahoe-dark -d "Tahoe dark theme with tabs"

# The profile will include:
# - macos-titlebar-style
# - background-image
# - mouse-scroll-multiplier
# - All other Ghostty settings

# Apply the profile
ait ghostty profile apply tahoe-dark
```

## Verification

Check that your Ghostty version supports these features:

```bash
# Check Ghostty version
ait ghostty status

# View all 1.2.x settings
ait ghostty config
```

**Minimum Version:** Ghostty 1.2.0 (recommended: 1.2.3+)

## See Also

- [Ghostty Official Docs](https://ghostty.org)
- [StatusLine Minimal Guide](statusline-minimal.md)
- [StatusLine Spacing Guide](statusline-spacing.md)
