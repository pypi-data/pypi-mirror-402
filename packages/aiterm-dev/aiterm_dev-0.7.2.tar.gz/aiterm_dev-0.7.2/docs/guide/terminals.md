# Terminal Emulators Guide

**aiterm** supports multiple terminal emulators for AI-assisted development workflows.

---

## Supported Terminals

| Terminal | macOS | Linux | Windows | aiterm Support |
|----------|-------|-------|---------|----------------|
| **iTerm2** | ✅ | - | - | Full (profiles, badge, status) |
| **Ghostty** | ✅ | ✅ | - | Full (v0.3.9+) |
| **Kitty** | ✅ | ✅ | - | Basic |
| **Alacritty** | ✅ | ✅ | ✅ | Basic |
| **WezTerm** | ✅ | ✅ | ✅ | Good |

---

## Quick Start

```bash
# Check which terminals are installed
ait terminals list

# Detect your current terminal
ait terminals detect

# See features for a specific terminal
ait terminals features ghostty
```

---

## Ghostty Support (v0.3.9+, Enhanced v0.3.15)

[Ghostty](https://ghostty.org/) is a fast, native terminal emulator built with Zig. aiterm provides **full iTerm2 parity** for Ghostty as of v0.3.15.

### Detection

aiterm detects Ghostty via:
- `GHOSTTY_RESOURCES_DIR` environment variable
- `ghostty --version` command output

```bash
$ ait terminals detect
Terminal Detection

✓ Detected: ghostty
  Version: Ghostty 1.2.3
  Channel: stable
  Features: tab_title, themes, native_ui
```

### Features

| Feature | Support | Notes |
|---------|---------|-------|
| Tab Title | ✅ | Via escape sequences |
| Themes | ✅ | 14 built-in themes |
| Native UI | ✅ | macOS native look |
| Profiles | ✅ v0.3.15 | aiterm-managed profiles |
| Keybinds | ✅ v0.3.15 | With presets (vim/emacs/tmux/macos) |
| Sessions | ✅ v0.3.15 | Save/restore terminal layouts |
| Backup | ✅ v0.3.15 | Timestamped config backups |
| Badge | ❌ | Not supported by Ghostty |

### Configuration

Ghostty configuration lives at:

```
~/.config/ghostty/config
```

**Example aiterm-friendly config:**

```ini
# ~/.config/ghostty/config

# Enable title changes from applications
window-title-format = "%t"

# Theme (optional)
theme = dracula

# Font
font-family = "JetBrains Mono"
font-size = 14

# Window
window-padding-x = 10
window-padding-y = 10
```

### Setting Tab Title

```bash
# Set tab title (works in Ghostty)
ait terminals title "Working on aiterm"
```

### Ghostty CLI Commands (v0.3.9+, Enhanced v0.3.15)

aiterm provides dedicated commands for managing Ghostty settings:

```bash
# Check Ghostty status and configuration
ait ghostty status

# Output:
# Ghostty Configuration
# ─────────────────────
# Config file: ~/.config/ghostty/config
# Theme: catppuccin-mocha
# Font: JetBrains Mono @ 14pt
```

**Theme Management:**
```bash
# List all 14 built-in themes
ait ghostty theme
# catppuccin-mocha, dracula, nord, tokyo-night,
# gruvbox-dark, gruvbox-light, solarized-dark,
# solarized-light, one-dark, one-light, etc.

# Apply a theme
ait ghostty theme dracula
# ✅ Theme set: dracula
# Ghostty auto-reloads on config change
```

**Font Configuration:**
```bash
# View current font settings
ait ghostty font
# Font: JetBrains Mono @ 14pt

# Change font family and size
ait ghostty font "Fira Code" 16
# ✅ Font set: Fira Code @ 16pt

# Change size only (keeps family)
ait ghostty font --size 18
```

**Custom Settings:**
```bash
# Set any Ghostty config value
ait ghostty set window-padding-x 12
ait ghostty set window-padding-y 12
ait ghostty set background-opacity 0.95
ait ghostty set cursor-style underline
ait ghostty set cursor-style-blink true

# View specific setting
ait ghostty get background-opacity
```

**Config File Location:**
```bash
# Show config file path
ait ghostty config
# ~/.config/ghostty/config

# Open config in $EDITOR
ait ghostty edit
```

### New in v0.3.15: Full iTerm2 Parity

**Profile Management:**
```bash
# Create profile from current config
ait ghostty profile create coding "My dev setup"

# List and apply profiles
ait ghostty profile list
ait ghostty profile apply coding

# Profiles stored in: ~/.config/ghostty/profiles/
```

**Keybind Management:**
```bash
# Apply a keybind preset
ait ghostty keybind preset vim    # vim-style navigation
ait ghostty keybind preset tmux   # tmux-style prefixes
ait ghostty keybind preset macos  # macOS native shortcuts

# Add custom keybinds
ait ghostty keybind add "ctrl+t" "new_tab"
ait ghostty keybind add "ctrl+q" "quit" --prefix global:

# List current keybinds
ait ghostty keybind list
```

**Session Management:**
```bash
# Save current working directory as session
ait ghostty session save work --layout split-h

# List and restore sessions
ait ghostty session list
ait ghostty session restore work

# Create terminal splits
ait ghostty session split right
ait ghostty session split down

# Sessions stored in: ~/.config/ghostty/sessions/
```

**Config Backup:**
```bash
# Create timestamped backup
ait ghostty backup
# → config.backup.20251230123456

# List and restore backups
ait ghostty restore
ait ghostty restore config.backup.20251230123456
```

### flow-cli Integration (tm dispatcher)

For instant Ghostty control via shell:

```bash
# tm dispatcher commands (no Python overhead)
tm ghost status          # Same as: ait ghostty status
tm ghost theme dracula   # Same as: ait ghostty theme dracula
tm ghost font "Fira Code" 16  # Same as: ait ghostty font
```

---

## iTerm2 Support

[iTerm2](https://iterm2.com/) is the most feature-rich terminal for macOS. aiterm provides full integration.

### Features

| Feature | Support | Notes |
|---------|---------|-------|
| Profiles | ✅ | Full profile switching |
| Tab Title | ✅ | Via escape sequences |
| Badge | ✅ | Status badges |
| Status Bar | ✅ | User-defined variables |
| Themes | ✅ | Color presets |

### Profile Switching

```bash
# Switch to a named profile
ait terminals profile "Python-Dev"

# Or use context-based switching
ait switch  # Automatically selects profile based on directory
```

### Recommended Profiles

Create these profiles in iTerm2 Preferences for automatic context switching:

| Profile | Color | Use Case |
|---------|-------|----------|
| `Default` | Blue | General development |
| `Python-Dev` | Green | Python projects |
| `R-Dev` | Purple | R package development |
| `Node-Dev` | Yellow | Node.js projects |
| `Production` | **Red** | Production environments |
| `AI-Session` | Cyan | Claude/Gemini sessions |

---

## WezTerm Support

[WezTerm](https://wezfurlong.org/wezterm/) is a GPU-accelerated terminal with Lua configuration.

### Features

| Feature | Support | Notes |
|---------|---------|-------|
| Tab Title | ✅ | Via escape sequences |
| Themes | ✅ | Color schemes |
| Lua Config | ✅ | Full scripting |
| Multiplexing | ✅ | Built-in tmux-like |

### Configuration

WezTerm config lives at `~/.wezterm.lua`:

```lua
-- ~/.wezterm.lua
local wezterm = require 'wezterm'
local config = {}

-- Allow aiterm to set tab title
config.window_title = 'WezTerm'

-- Theme
config.color_scheme = 'Dracula'

-- Font
config.font = wezterm.font 'JetBrains Mono'
config.font_size = 14.0

return config
```

---

## Kitty Support

[Kitty](https://sw.kovidgoyal.net/kitty/) is a fast, GPU-accelerated terminal.

### Features

| Feature | Support | Notes |
|---------|---------|-------|
| Tab Title | ✅ | Via escape sequences |
| Themes | ✅ | Via kitty-themes |
| Kittens | ✅ | Plugin system |

### Configuration

```ini
# ~/.config/kitty/kitty.conf

# Allow aiterm to set window title
allow_remote_control yes

# Theme
include ~/.config/kitty/themes/dracula.conf

# Font
font_family JetBrains Mono
font_size 14.0
```

---

## Alacritty Support

[Alacritty](https://alacritty.org/) is a minimalist, cross-platform terminal.

### Features

| Feature | Support | Notes |
|---------|---------|-------|
| Tab Title | ✅ | Via escape sequences |
| Themes | ✅ | TOML config |
| Profiles | ❌ | Single config only |

### Configuration

```toml
# ~/.config/alacritty/alacritty.toml

[window]
title = "Alacritty"
dynamic_title = true

[font]
size = 14.0

[font.normal]
family = "JetBrains Mono"
```

---

## Feature Comparison

Run `ait terminals compare` for a live comparison:

```
                    Terminal Feature Comparison
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┓
┃ Terminal  ┃ Profiles ┃ Tab Title ┃ Badge ┃ Themes ┃ Native UI ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━┩
│ iTerm2    │    ✓     │     ✓     │   ✓   │   ✓    │     ✓     │
│ Kitty     │    ✓     │     ✓     │   ✗   │   ✓    │     ✗     │
│ Alacritty │    ✗     │     ✓     │   ✗   │   ✓    │     ✗     │
│ WezTerm   │    ✓     │     ✓     │   ✗   │   ✓    │     ✓     │
│ Ghostty   │  ✓*      │     ✓     │   ✗   │   ✓    │     ✓     │
└───────────┴──────────┴───────────┴───────┴────────┴───────────┘
* Ghostty profiles managed by aiterm v0.3.15+ (not native to Ghostty)
```

---

## Choosing a Terminal

### For AI-Assisted Development

**Recommended: iTerm2 or Ghostty**

- **iTerm2** - Best for profile-based context switching, status bar integration
- **Ghostty** - Best for performance, native macOS feel, simplicity

### For Cross-Platform

**Recommended: WezTerm**

- Works on macOS, Linux, Windows
- Lua scripting for customization
- Good performance

### For Minimalism

**Recommended: Alacritty or Ghostty**

- Simple configuration
- Fast startup
- Low resource usage

---

## Troubleshooting

### Terminal Not Detected

```bash
# Check what aiterm sees
ait terminals detect

# If wrong terminal detected, check environment
echo $TERM_PROGRAM
echo $GHOSTTY_RESOURCES_DIR
```

### Tab Title Not Changing

Some terminals require configuration to allow title changes:

**Ghostty:** Should work by default

**iTerm2:** Preferences → Profiles → Terminal → "Applications in terminal may change the title"

**Kitty:** Add `allow_remote_control yes` to config

**WezTerm:** Should work by default

### Profile Not Switching (iTerm2)

1. Ensure the profile exists in iTerm2 Preferences
2. Check profile name matches exactly (case-sensitive)
3. Try running manually: `ait terminals profile "ProfileName"`

---

## Next Steps

- **Context Detection:** [How aiterm detects project types](context-detection.md)
- **Profile Configuration:** [Setting up profiles](profiles.md)
- **Workflows:** [Development workflows](workflows.md)
