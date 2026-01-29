# XDG Config Migration Proposal

**Generated:** 2025-12-29
**Topic:** Move aiterm config to `~/.config/aiterm/` with environment variable support

---

## Current State

aiterm doesn't have a dedicated config directory yet. Various files are scattered:

| File | Current Location | Purpose |
|------|------------------|---------|
| Claude settings | `~/.claude/settings.json` | Claude Code config (not ours) |
| flow-cli integration | `~/.config/flow/` (via flow-cli) | Shell integration |
| Ghostty config | `~/.config/ghostty/config` | Terminal config (not ours) |

---

## Proposed: XDG-Compliant Config

### Environment Variable: `AITERM_CONFIG_HOME`

Following the pattern used by:
- `ZDOTDIR` - ZSH config directory
- `FLOW_CONFIG_DIR` - flow-cli config (already XDG-compliant)
- `CLAUDE_CONFIG_DIR` - Claude Code (hypothetical)

```bash
# Default (XDG-compliant)
AITERM_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/aiterm"

# User can override
export AITERM_CONFIG_HOME="$HOME/.aiterm"  # Legacy style
export AITERM_CONFIG_HOME="/custom/path"   # Custom
```

### Directory Structure

```
~/.config/aiterm/                    # AITERM_CONFIG_HOME
├── config.toml                      # Main config file
├── profiles/                        # Terminal profiles
│   ├── r-dev.toml
│   ├── python-dev.toml
│   └── production.toml
├── themes/                          # Custom themes
│   └── my-theme.toml
├── hooks/                           # Custom hooks
│   └── post-switch.sh
└── cache/                           # Could also be XDG_CACHE_HOME
    └── terminal-detection.json
```

---

## Options

### Option A: `AITERM_CONFIG_HOME` (Recommended)

**Pattern:** Like `ZDOTDIR` but for aiterm

```bash
# In ~/.zshenv or ~/.zshrc
export AITERM_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/aiterm"
```

**Python implementation:**
```python
import os
from pathlib import Path

def get_config_home() -> Path:
    """Get aiterm config directory, respecting AITERM_CONFIG_HOME."""
    if env_path := os.environ.get("AITERM_CONFIG_HOME"):
        return Path(env_path)

    xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(xdg_config) / "aiterm"

CONFIG_HOME = get_config_home()
CONFIG_FILE = CONFIG_HOME / "config.toml"
```

**Pros:**
- Follows ZDOTDIR pattern (familiar to ZSH users)
- Single variable to override everything
- XDG-compliant by default

**Cons:**
- Another env var to remember

---

### Option B: Pure XDG (No Custom Variable)

**Pattern:** Just use XDG_CONFIG_HOME directly

```python
def get_config_home() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(xdg_config) / "aiterm"
```

**Pros:**
- Simpler, no custom env var
- Users already know XDG

**Cons:**
- Can't override just aiterm without affecting all XDG apps
- Less flexibility

---

### Option C: Multiple XDG Variables

**Pattern:** Separate vars for config, data, cache

```bash
AITERM_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/aiterm"
AITERM_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/aiterm"
AITERM_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/aiterm"
AITERM_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}/aiterm"
```

**Pros:**
- Full XDG compliance
- Separation of concerns

**Cons:**
- Overkill for aiterm's needs
- Too many variables

---

## Recommendation: Option A

Use `AITERM_CONFIG_HOME` with XDG fallback:

```python
# src/aiterm/config/paths.py
import os
from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=1)
def get_config_home() -> Path:
    """
    Get aiterm config directory.

    Priority:
    1. AITERM_CONFIG_HOME (if set)
    2. XDG_CONFIG_HOME/aiterm (if XDG_CONFIG_HOME set)
    3. ~/.config/aiterm (default)
    """
    if env_path := os.environ.get("AITERM_CONFIG_HOME"):
        return Path(env_path).expanduser()

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "aiterm"

    return Path.home() / ".config" / "aiterm"

# Convenience constants
CONFIG_HOME = get_config_home()
CONFIG_FILE = CONFIG_HOME / "config.toml"
PROFILES_DIR = CONFIG_HOME / "profiles"
THEMES_DIR = CONFIG_HOME / "themes"
```

---

## Implementation Plan

### Phase 1: Add Config Module (30 min)

Create `src/aiterm/config/paths.py`:
- `get_config_home()` - Main config directory
- `get_config_file()` - Main config file path
- `ensure_config_dir()` - Create if not exists
- Constants: `CONFIG_HOME`, `CONFIG_FILE`, `PROFILES_DIR`

### Phase 2: Migrate Existing Code (1 hour)

Update all hardcoded paths to use the new module:
- Terminal profiles
- Theme configurations
- Cache files
- Hook storage

### Phase 3: Config File Format (1 hour)

Create `config.toml` schema:

```toml
# ~/.config/aiterm/config.toml

[general]
default_terminal = "auto"  # auto, iterm2, ghostty, etc.
quiet_mode = false

[profiles]
default = "default"
auto_switch = true

[flow_cli]
enabled = true
dispatcher = "tm"

[claude]
manage_settings = true
backup_on_change = true
```

### Phase 4: CLI Commands (30 min)

Add config management commands:

```bash
ait config show              # Show current config
ait config path              # Show config file path
ait config edit              # Open in $EDITOR
ait config init              # Initialize config directory
ait config migrate           # Migrate from old locations
```

### Phase 5: Documentation (30 min)

- Update docs with config location info
- Add environment variable reference
- Migration guide for existing users

---

## Environment Variables Summary

| Variable | Purpose | Default |
|----------|---------|---------|
| `AITERM_CONFIG_HOME` | Config directory override | `$XDG_CONFIG_HOME/aiterm` or `~/.config/aiterm` |
| `AITERM_DEBUG` | Enable debug logging | `0` |
| `AITERM_QUIET` | Suppress non-essential output | `0` |

---

## Comparison with Similar Tools

| Tool | Config Location | Env Override |
|------|-----------------|--------------|
| ZSH | `~/.zshrc` or `$ZDOTDIR/.zshrc` | `ZDOTDIR` |
| flow-cli | `~/.config/flow/` | `FLOW_CONFIG_DIR` |
| Ghostty | `~/.config/ghostty/` | (none, pure XDG) |
| Starship | `~/.config/starship.toml` | `STARSHIP_CONFIG` |
| bat | `~/.config/bat/` | `BAT_CONFIG_PATH` |
| fd | `~/.config/fd/` | (none) |

**Pattern:** Most CLI tools use either:
1. Pure XDG (`~/.config/<app>/`)
2. XDG + single override env var (`<APP>_CONFIG` or `<APP>_CONFIG_HOME`)

---

## Migration Path

For users with existing configs (future):

```bash
# Old location (hypothetical)
~/.aiterm/config.json

# New location
~/.config/aiterm/config.toml

# Migration command
ait config migrate
```

---

## Quick Wins (Do Now)

1. **Create paths module** - `src/aiterm/config/paths.py`
2. **Add `AITERM_CONFIG_HOME`** - Environment variable support
3. **Create default config** - `~/.config/aiterm/config.toml`
4. **Add `ait config path`** - Show where config lives

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/aiterm/config/__init__.py` | New module |
| `src/aiterm/config/paths.py` | Path resolution |
| `src/aiterm/config/schema.py` | Config schema |
| `src/aiterm/cli/config.py` | Config CLI commands |
| `docs/reference/configuration.md` | Documentation |

---

## References

- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/)
- [XDG Best Practices](https://xdgbasedirectoryspecification.com/)
- [Arch Wiki - XDG Base Directory](https://wiki.archlinux.org/title/XDG_Base_Directory)
- flow-cli: `${XDG_CONFIG_HOME:-$HOME/.config}/flow`
- ZDOTDIR pattern: `${ZDOTDIR:-$HOME}`

---

*Status: Proposal*
*Target: v0.4.0*
*Pattern: AITERM_CONFIG_HOME with XDG fallback*
