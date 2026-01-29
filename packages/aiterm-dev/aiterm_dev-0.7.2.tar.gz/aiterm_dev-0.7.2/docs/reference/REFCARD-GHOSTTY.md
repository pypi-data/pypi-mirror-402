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
