# Ghostty Configuration Tutorial

A step-by-step tutorial for configuring Ghostty terminal with aiterm.

## What You'll Learn

- How to detect and verify Ghostty
- Theme and font configuration
- Using Ghostty 1.2.x features
- Profile and backup management

## Prerequisites

- Ghostty 1.2.0+ installed
- aiterm installed

## Tutorial Steps

### Part 1: Getting Started (5 min)

#### Step 1: Verify Ghostty is Detected

Open Ghostty and run:

```bash
ait ghostty status
```

You should see:

```
┌────────────────────┬──────────────────────────────┐
│ Running in Ghostty │ Yes                          │
│ Config File        │ ~/.config/ghostty/config     │
└────────────────────┴──────────────────────────────┘
```

#### Step 2: View Current Configuration

```bash
ait ghostty config
```

This shows all your current Ghostty settings.

### Part 2: Customizing Appearance (10 min)

#### Step 3: Choose a Theme

List all available themes:

```bash
ait ghostty theme list
```

Apply a theme:

```bash
ait ghostty theme apply catppuccin-mocha
```

**Try these popular themes:**

- `catppuccin-mocha` - Modern dark theme
- `nord` - Cool blue-gray
- `tokyo-night` - Purple/blue dark theme
- `gruvbox-dark` - Warm retro colors

#### Step 4: Set Your Font

```bash
# Set font family and size
ait ghostty font set "JetBrains Mono" 14
```

**Popular monospace fonts:**

- JetBrains Mono
- Fira Code
- Hack
- Source Code Pro
- Cascadia Code

#### Step 5: Adjust Window Padding

```bash
# Set padding (in pixels)
ait ghostty set window-padding-x 12
ait ghostty set window-padding-y 8
```

### Part 3: Ghostty 1.2.x Features (10 min)

#### Step 6: Configure macOS Titlebar

Ghostty 1.2.x supports different titlebar styles:

```bash
# Integrated tabs in titlebar
ait ghostty set macos-titlebar-style tabs
```

**Available styles:**

- `native` - Standard macOS titlebar
- `transparent` - Transparent titlebar
- `tabs` - Tabs integrated in titlebar (recommended)
- `hidden` - No titlebar

#### Step 7: Add a Background Image (Optional)

```bash
# Set background image
ait ghostty set background-image ~/Pictures/terminal-bg.jpg

# Adjust opacity for better readability
ait ghostty set background-opacity 0.95
```

**Tips:**

- Use subtle, low-contrast images
- PNG or JPEG formats supported
- Combine with opacity for best results

#### Step 8: Adjust Scroll Sensitivity

```bash
# Default is 3, adjust to your preference
ait ghostty set mouse-scroll-multiplier 2.0
```

**Recommended values:**

- `1.0-2.0` - Slower, more precise
- `3.0` - Default
- `4.0-6.0` - Faster scrolling

### Part 4: Saving Your Configuration (5 min)

#### Step 9: Create a Profile

Save your current configuration as a profile:

```bash
ait ghostty profile create my-theme -d "My custom Ghostty theme"
```

View your profiles:

```bash
ait ghostty profile list
```

#### Step 10: Create a Backup

Always backup before major changes:

```bash
ait ghostty backup --suffix before-changes
```

List backups:

```bash
ait ghostty restore
```

### Part 5: Advanced Configuration (10 min)

#### Step 11: Set Multiple Options

You can set any Ghostty configuration option:

```bash
# Cursor style
ait ghostty set cursor-style bar
ait ghostty set cursor-style-blink true

# Opacity
ait ghostty set background-opacity 0.9

# Padding
ait ghostty set window-padding-x 15
ait ghostty set window-padding-y 10
```

#### Step 12: Edit Config Directly

For advanced users:

```bash
# Open config in your editor
ait ghostty config --edit
```

Example config:

```ini
theme = catppuccin-mocha
font-family = JetBrains Mono
font-size = 14
macos-titlebar-style = tabs
window-padding-x = 12
window-padding-y = 8
background-opacity = 1.0
cursor-style = block
mouse-scroll-multiplier = 2.0
```

#### Step 13: Apply Profiles

Switch between configurations easily:

```bash
# Create different profiles for different contexts
ait ghostty profile create work -d "Work setup"
ait ghostty profile create personal -d "Personal setup"

# Switch profiles
ait ghostty profile apply work
```

### Part 6: Maintenance (5 min)

#### Step 14: Restore from Backup

If something goes wrong:

```bash
# List backups
ait ghostty restore

# Restore specific backup
ait ghostty restore config.backup.20260117120000
```

#### Step 15: View Profile Details

Check what's in a profile:

```bash
ait ghostty profile show my-theme
```

## Quick Reference

### Essential Commands

```bash
# Status and config
ait ghostty status
ait ghostty config

# Themes
ait ghostty theme list
ait ghostty theme apply <name>

# Fonts
ait ghostty font set <family> [size]

# 1.2.x Features
ait ghostty set macos-titlebar-style tabs
ait ghostty set background-image <path>
ait ghostty set mouse-scroll-multiplier <value>

# Profiles
ait ghostty profile create <name> -d "description"
ait ghostty profile list
ait ghostty profile apply <name>

# Backups
ait ghostty backup --suffix <name>
ait ghostty restore
```

## Next Steps

- Explore [Ghostty 1.2.x features](../docs/guides/ghostty-1.2.x.md)
- Check the [Ghostty Reference Card](../docs/reference/REFCARD-GHOSTTY.md)
- Try different themes and fonts
- Create profiles for different workflows

## Troubleshooting

**Q: Changes don't appear?**
A: Ghostty auto-reloads config. If not working, restart Ghostty.

**Q: Can't find a theme?**
A: Run `ait ghostty theme list` to see all available themes.

**Q: How do I reset to defaults?**
A: Delete `~/.config/ghostty/config` and restart Ghostty.

**Q: Profile not applying?**
A: Check profile exists with `ait ghostty profile list`.

## Summary

You've learned how to:

- ✅ Detect and configure Ghostty
- ✅ Apply themes and fonts
- ✅ Use Ghostty 1.2.x features
- ✅ Manage profiles and backups
- ✅ Customize advanced settings

Happy terminal customization! 🎨
