---
description: Setup Ghostty with optimal configuration
---

# Ghostty Setup Workflow

This workflow guides you through setting up Ghostty terminal with aiterm for an optimal development experience.

## Prerequisites

- Ghostty 1.2.0+ installed
- aiterm installed (`brew install data-wise/tap/aiterm` or `pip install aiterm-dev`)

## Steps

### 1. Verify Ghostty Detection

```bash
ait ghostty status
```

**Expected:** "Running in Ghostty: Yes"

### 2. Choose and Apply a Theme

```bash
# List available themes
ait ghostty theme list

# Apply your preferred theme
ait ghostty theme apply catppuccin-mocha
```

**Popular choices:**

- `catppuccin-mocha` - Dark, pastel colors
- `nord` - Dark, blue-gray
- `tokyo-night` - Dark, purple/blue
- `gruvbox-dark` - Dark, warm colors

### 3. Configure Font

```bash
# Set font family and size
ait ghostty font set "JetBrains Mono" 14

# Or just font family
ait ghostty font set "Fira Code"
```

### 4. Set macOS Titlebar Style (1.2.x)

```bash
# Choose titlebar style
ait ghostty set macos-titlebar-style tabs

# Options: native, transparent, tabs, hidden
```

### 5. Configure Window Padding

```bash
# Set horizontal and vertical padding
ait ghostty set window-padding-x 12
ait ghostty set window-padding-y 8
```

### 6. Optional: Background Image (1.2.x)

```bash
# Set a background image
ait ghostty set background-image ~/Pictures/terminal-bg.jpg

# Adjust opacity if needed
ait ghostty set background-opacity 0.95
```

### 7. Optional: Scroll Sensitivity (1.2.x)

```bash
# Adjust scroll multiplier (default: 3)
ait ghostty set mouse-scroll-multiplier 2.0
```

### 8. Save as Profile

```bash
# Create a profile from current config
ait ghostty profile create my-setup -d "My optimal Ghostty setup"

# List profiles to verify
ait ghostty profile list
```

### 9. Create Backup

```bash
# Create a timestamped backup
ait ghostty backup --suffix initial-setup
```

### 10. Verify Configuration

```bash
# View current config
ait ghostty config

# Or open in editor
ait ghostty config --edit
```

## Quick Restore

If you need to restore your setup on a new machine:

```bash
# Apply your saved profile
ait ghostty profile apply my-setup
```

## Troubleshooting

**Ghostty not detected:**

```bash
# Check terminal detection
ait terminals detect

# Verify Ghostty is running
echo $TERM_PROGRAM
```

**Config not applying:**

- Ghostty auto-reloads config on save
- If changes don't appear, restart Ghostty

**Theme not found:**

```bash
# List all available themes
ait ghostty theme list
```

## Related

- [Ghostty 1.2.x Guide](../docs/guides/ghostty-1.2.x.md)
- [Ghostty Reference Card](../docs/reference/REFCARD-GHOSTTY.md)
