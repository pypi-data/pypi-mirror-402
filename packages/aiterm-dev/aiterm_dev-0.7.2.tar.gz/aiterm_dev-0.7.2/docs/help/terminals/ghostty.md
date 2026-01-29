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
# Ghostty Quick Reference

Quick reference for aiterm's Ghostty terminal integration.

**Added in:** v0.3.9 | **Updated:** v0.7.2 (Ghostty 1.2.x Support)

---

## All Commands (v0.3.15)

```
┌─────────────────────────────────────────────────────────────┐
│ GHOSTTY COMMANDS                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ STATUS & CONFIG                                             │
│ ──────────────                                              │
│ ait ghostty status        Show config and detection status  │
│ ait ghostty config        Display config file location      │
│ ait ghostty config --edit Open config in $EDITOR            │
│                                                             │
│ THEME MANAGEMENT                                            │
│ ────────────────                                            │
│ ait ghostty theme list    List 14 built-in themes           │
│ ait ghostty theme show    Show current theme                │
│ ait ghostty theme apply   Apply a theme (auto-reload)       │
│                                                             │
│ FONT CONFIGURATION                                          │
│ ──────────────────                                          │
│ ait ghostty font show     Show current font settings        │
│ ait ghostty font set      Set font family and/or size       │
│                                                             │
│ GENERIC SETTINGS                                            │
│ ────────────────                                            │
│ ait ghostty set           Set any config key=value          │
│                                                             │
│ PROFILE MANAGEMENT (v0.3.15)                                │
│ ────────────────────────────                                │
│ ait ghostty profile list          List saved profiles       │
│ ait ghostty profile show <name>   Show profile details      │
│ ait ghostty profile create <name> Create from current config│
│ ait ghostty profile apply <name>  Apply profile to config   │
│ ait ghostty profile delete <name> Delete a profile          │
│                                                             │
│ CONFIG BACKUP (v0.3.15)                                     │
│ ───────────────────────                                     │
│ ait ghostty backup [--suffix]     Create timestamped backup │
│ ait ghostty restore               List available backups    │
│ ait ghostty restore <backup>      Restore from backup       │
│                                                             │
│ KEYBIND MANAGEMENT (v0.3.15)                                │
│ ────────────────────────────                                │
│ ait ghostty keybind list          List current keybinds     │
│ ait ghostty keybind add KEY ACT   Add a keybinding          │
│ ait ghostty keybind remove KEY    Remove a keybinding       │
│ ait ghostty keybind preset NAME   Apply keybind preset      │
│                                                             │
│ SESSION CONTROL (v0.3.15)                                   │
│ ─────────────────────────                                   │
│ ait ghostty session list          List saved sessions       │
│ ait ghostty session show <name>   Show session details      │
│ ait ghostty session save <name>   Save current as session   │
│ ait ghostty session restore <name> Restore a session        │
│ ait ghostty session delete <name> Delete a session          │
│ ait ghostty session split [dir]   Create terminal split     │
│                                                             │
│ SHORTCUTS (via ghost alias)                                 │
│ ──────────────────────────                                  │
│ ait ghost                 → ait ghostty status              │
│ ait ghost theme           → ait ghostty theme list          │
│ ait ghost config          → ait ghostty config              │
│ ait ghost font            → ait ghostty font show           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Built-in Themes (14)

| Theme | Style |
|-------|-------|
| `catppuccin-mocha` | Dark, pastel |
| `catppuccin-latte` | Light, pastel |
| `catppuccin-frappe` | Medium dark |
| `catppuccin-macchiato` | Dark, muted |
| `dracula` | Dark, purple accent |
| `gruvbox-dark` | Dark, orange/green |
| `gruvbox-light` | Light, warm |
| `nord` | Dark, blue-gray |
| `solarized-dark` | Dark, teal accent |
| `solarized-light` | Light, teal accent |
| `tokyo-night` | Dark, purple/blue |
| `tokyo-night-storm` | Dark, stormy |
| `one-dark` | Atom One Dark |
| `one-light` | Atom One Light |

```bash
# Apply a theme
ait ghostty theme apply nord

# Ghostty auto-reloads on config change
```

---

## Common Configuration Keys

| Key | Values | Description |
|-----|--------|-------------|
| `theme` | Theme name | Color scheme |
| `font-family` | Font name | Monospace font |
| `font-size` | Integer | Font size in points |
| `window-padding-x` | Integer | Horizontal padding (px) |
| `window-padding-y` | Integer | Vertical padding (px) |
| `background-opacity` | 0.0-1.0 | Window transparency |
| `cursor-style` | block/bar/underline | Cursor shape |
| `cursor-style-blink` | true/false | Blink cursor |
| `macos-titlebar-style` | native/transparent/tabs/hidden | macOS titlebar style (1.2.x) |
| `background-image` | Path to PNG/JPEG | Terminal background image (1.2.x) |
| `mouse-scroll-multiplier` | 0.01-10000 | Scroll sensitivity (1.2.x) |

```bash
# Examples
ait ghostty set background-opacity 0.95
ait ghostty set cursor-style bar
ait ghostty set window-padding-x 12

# Ghostty 1.2.x features
ait ghostty set macos-titlebar-style tabs
ait ghostty set background-image ~/Pictures/bg.jpg
ait ghostty set mouse-scroll-multiplier 2.0
```

---

## Config File Location

```
~/.config/ghostty/config
```

```bash
# Open in editor
ait ghostty config --edit

# Example config
cat ~/.config/ghostty/config
```

**Sample config:**

```ini
font-family = JetBrains Mono
font-size = 14
theme = catppuccin-mocha
window-padding-x = 10
window-padding-y = 8
background-opacity = 1.0
cursor-style = block
```

---

## Detection

aiterm detects Ghostty via:

1. `GHOSTTY_RESOURCES_DIR` environment variable
2. `ghostty --version` command output

```bash
# Check detection
ait terminals detect

# Output when in Ghostty:
# ✓ Detected: ghostty
#   Version: Ghostty 1.2.3
```

---

## Keybind Presets (v0.3.15)

Four built-in keybind presets for common workflows:

| Preset | Style | Key Bindings |
|--------|-------|--------------|
| `vim` | Vim-style | ctrl+h/j/k/l for navigation, ctrl+w prefixes |
| `emacs` | Emacs-style | ctrl+x prefixes, buffer-style tabs |
| `tmux` | tmux-style | ctrl+b prefix for all operations |
| `macos` | macOS native | cmd+t/w/d, cmd+shift+[] |

```bash
# Apply a preset
ait ghostty keybind preset vim

# List available presets
ait ghostty keybind preset --list

# Add custom keybind
ait ghostty keybind add "ctrl+t" "new_tab"
ait ghostty keybind add "cmd+shift+d" "new_split:down" --prefix global:
```

**Keybind prefixes:**

- `global:` - Works even when terminal isn't focused
- `unconsumed:` - Only if not consumed by shell
- `all:` - Combines global + unconsumed

---

## Session Management (v0.3.15)

Save and restore terminal layouts with sessions:

```bash
# Save current directory as a session
ait ghostty session save work --layout split-h

# List saved sessions
ait ghostty session list

# Restore a session
ait ghostty session restore work

# Create a terminal split
ait ghostty session split right    # or: down, left, up
```

**Session storage:** `~/.config/ghostty/sessions/*.json`

**Layout types:**

- `single` - Single pane (default)
- `split-h` - Horizontal split
- `split-v` - Vertical split
- `grid` - 2x2 grid

---

## Profile Management (v0.3.15)

Save and switch between Ghostty configurations:

```bash
# Create profile from current config
ait ghostty profile create coding "My dev setup"

# List saved profiles
ait ghostty profile list

# Apply a profile
ait ghostty profile apply coding

# Delete a profile
ait ghostty profile delete old-profile
```

**Profile storage:** `~/.config/ghostty/profiles/*.conf`

---

## Config Backup (v0.3.15)

Timestamped backups matching Claude Code pattern:

```bash
# Create backup
ait ghostty backup
# → config.backup.20251230123456

# Create backup with custom suffix
ait ghostty backup --suffix before-update

# List available backups
ait ghostty restore

# Restore from backup
ait ghostty restore config.backup.20251230123456
```

**Backup location:** Same directory as config (`~/.config/ghostty/`)

---

## flow-cli Integration

For instant Ghostty control via shell (no Python overhead):

```bash
# tm dispatcher commands
tm ghost status          # Same as: ait ghostty status
tm ghost theme dracula   # Same as: ait ghostty theme apply dracula
tm ghost font "Fira Code" 16  # Same as: ait ghostty font set
```

---

## Comparison with iTerm2

| Feature | Ghostty | iTerm2 |
|---------|---------|--------|
| Themes | ✓ Built-in (14) | ✓ Color presets |
| Profiles | ✓ aiterm managed (v0.3.15) | ✓ Native support |
| Keybinds | ✓ With presets (v0.3.15) | ✓ Full support |
| Sessions | ✓ aiterm managed (v0.3.15) | ✓ Arrangements |
| Tab Title | ✓ Via escape seqs | ✓ Via escape seqs |
| Backup | ✓ Timestamped (v0.3.15) | ✓ Via plist |
| Badge | ✗ Not supported | ✓ Full support |
| Status Bar | ✗ Not supported | ✓ Full support |
| Native UI | ✓ macOS native | ✓ macOS native |
| Config Reload | ✓ Auto-reload | ✗ Manual |

**Note:** v0.3.15 achieves full iTerm2 parity for the features Ghostty supports!

---

## Related

- [Terminal Support Guide](../guide/terminals.md) - Full terminal documentation
- [Context Detection](../guide/context-detection.md) - Profile switching
- [REFCARD](../REFCARD.md) - Main quick reference
