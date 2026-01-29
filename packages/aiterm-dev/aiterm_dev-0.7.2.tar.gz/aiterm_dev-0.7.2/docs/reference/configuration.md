# Configuration Reference

## aiterm Configuration

### Config Directory (XDG-Compliant)

aiterm uses XDG-compliant configuration paths:

| Path | Purpose |
|------|---------|
| `~/.config/aiterm/` | Main config directory |
| `~/.config/aiterm/config.toml` | Main configuration file |
| `~/.config/aiterm/profiles/` | Terminal profiles |
| `~/.config/aiterm/themes/` | Custom themes |
| `~/.config/aiterm/cache/` | Cached data |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AITERM_CONFIG_HOME` | Override config directory | `~/.config/aiterm` |
| `XDG_CONFIG_HOME` | XDG base config directory | `~/.config` |
| `AITERM_DEBUG` | Enable debug logging | `0` |
| `AITERM_QUIET` | Suppress non-essential output | `0` |

**Priority order:**
1. `AITERM_CONFIG_HOME` (if set)
2. `XDG_CONFIG_HOME/aiterm` (if XDG_CONFIG_HOME set)
3. `~/.config/aiterm` (default)

### Example Configuration

```toml
# ~/.config/aiterm/config.toml

[general]
# Default terminal (auto, iterm2, ghostty)
default_terminal = "auto"

# Quiet mode - suppress non-essential output
quiet_mode = false

[profiles]
# Default profile name
default = "default"

# Auto-switch profiles based on context
auto_switch = true

[flow_cli]
# Enable flow-cli integration
enabled = true

# Dispatcher name (tm)
dispatcher = "tm"

[claude]
# Manage Claude Code settings
manage_settings = true

# Create backups before modifying settings
backup_on_change = true
```

### CLI Commands

```bash
# Show config paths
ait config path              # Show config directory
ait config path --all        # Show all paths with status

# View/edit configuration
ait config show              # Display current config
ait config edit              # Open in $EDITOR

# Initialize config
ait config init              # Create default config.toml
ait config init --force      # Overwrite existing
```

---

## Shell Configuration

### Required in .zshrc

```zsh
# Must be before Oh My Zsh / Antidote loads
DISABLE_AUTO_TITLE="true"

# flow-cli integration (provides tm dispatcher)
source ~/path/to/flow-cli/flow.plugin.zsh
```

### Shell Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TERM_PROGRAM` | Must be "iTerm.app" for iTerm2 | Set by iTerm2 |
| `DISABLE_AUTO_TITLE` | Prevent OMZ title override | Not set |
| `GHOSTTY_RESOURCES_DIR` | Ghostty detection | Set by Ghostty |

---

## Integration Variables

These are set by the integration (read-only):

| Variable | Purpose |
|----------|---------|
| `_ITERM_CURRENT_PROFILE` | Currently active profile |
| `_ITERM_CURRENT_TITLE` | Current tab title |
| `_ITERM_HOOK_REGISTERED` | Prevents duplicate hooks |

---

## iTerm2 Configuration

### Title Settings

Path: Settings → Profiles → General → Title

| Setting | Recommended |
|---------|-------------|
| Title | Session Name |
| Alternative | Session Name + Job |

### For Triggers

Path: Settings → Profiles → Default → Advanced → Triggers

See [Triggers Guide](../guide/triggers.md) for setup.

---

## File Locations

| File | Location |
|------|----------|
| aiterm config | `~/.config/aiterm/config.toml` |
| Integration script | `flow-cli/zsh/functions/aiterm-integration.zsh` |
| Dynamic Profiles | `profiles/context-switcher-profiles.json` |
| iTerm2 Dynamic Profiles | `~/Library/Application Support/iTerm2/DynamicProfiles/` |
| iTerm2 Preferences | `~/Library/Preferences/com.googlecode.iterm2.plist` |
| Ghostty config | `~/.config/ghostty/config` |

---

## Claude Code Configuration

| File | Location | Purpose |
|------|----------|---------|
| Settings | `~/.claude/settings.json` | Main Claude Code settings |
| Hooks | `~/.claude/hooks/` | Hook scripts |
| Sessions | `~/.claude/sessions/` | Session tracking |
| Backups | `~/.claude/settings.backup-*.json` | Auto-backups |

---

## Escape Sequences Used

| Sequence | Purpose |
|----------|---------|
| `\033]1337;SetProfile=NAME\007` | Switch iTerm2 profile |
| `\033]2;TITLE\007` | Set window/tab title |
| `\033]1337;SetUserVar=VAR=VALUE\007` | Set iTerm2 user variable |
