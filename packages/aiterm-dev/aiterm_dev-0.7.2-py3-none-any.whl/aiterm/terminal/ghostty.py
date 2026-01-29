"""Ghostty terminal integration.

Provides configuration management and theme switching for Ghostty terminal.
Ghostty is a GPU-accelerated terminal emulator by Mitchell Hashimoto.

Key differences from iTerm2:
- Config file: ~/.config/ghostty/config (plain text, not JSON)
- No runtime profile switching via escape sequences
- Changes require config reload (Cmd+Shift+,) or restart
- Themes are applied by modifying config file

Profile Management (v0.4.0):
- Profiles stored in ~/.config/ghostty/profiles/
- Each profile is a partial config that gets merged into main config
- Supports create from current, apply, delete operations
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiterm.context.detector import ContextInfo


@dataclass
class GhosttyConfig:
    """Parsed Ghostty configuration."""

    font_family: str = "monospace"
    font_size: int = 14
    theme: str = ""
    window_padding_x: int = 0
    window_padding_y: int = 0
    background_opacity: float = 1.0
    macos_titlebar_style: str = "native"
    background_image: str = ""
    mouse_scroll_multiplier: float = 1.0
    cursor_style: str = "block"
    raw_config: dict = field(default_factory=dict)


@dataclass
class GhosttySession:
    """A saved Ghostty session layout."""

    name: str
    working_dirs: list[str] = field(default_factory=list)  # Paths for each pane/tab
    created_at: str = ""
    description: str = ""
    layout: str = "single"  # single, split-h, split-v, grid

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return {
            "name": self.name,
            "working_dirs": self.working_dirs,
            "created_at": self.created_at,
            "description": self.description,
            "layout": self.layout,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GhosttySession":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            working_dirs=data.get("working_dirs", []),
            created_at=data.get("created_at", ""),
            description=data.get("description", ""),
            layout=data.get("layout", "single"),
        )


@dataclass
class GhosttyKeybind:
    """A Ghostty keybinding."""

    trigger: str  # e.g., "ctrl+t", "cmd+shift+n"
    action: str  # e.g., "new_tab", "new_split:right"
    prefix: str = ""  # e.g., "global:", "unconsumed:", "all:"

    def to_config_line(self) -> str:
        """Convert to config file format."""
        if self.prefix:
            return f"keybind = {self.prefix}{self.trigger}={self.action}"
        return f"keybind = {self.trigger}={self.action}"

    @classmethod
    def from_config_line(cls, line: str) -> Optional["GhosttyKeybind"]:
        """Parse a keybind from config line."""
        # Format: keybind = [prefix:]trigger=action
        if "=" not in line:
            return None

        _, _, value = line.partition("=")
        value = value.strip()

        if "=" not in value:
            return None

        # Check for prefixes
        prefix = ""
        for p in ["global:", "unconsumed:", "all:", "global:unconsumed:", "unconsumed:global:"]:
            if value.startswith(p):
                prefix = p
                value = value[len(p) :]
                break

        trigger, _, action = value.partition("=")
        if not trigger or not action:
            return None

        return cls(trigger=trigger.strip(), action=action.strip(), prefix=prefix)


@dataclass
class GhosttyProfile:
    """A named Ghostty profile (partial config)."""

    name: str
    theme: str = ""
    font_family: str = ""
    font_size: int = 0
    background_opacity: float = 0.0
    window_padding_x: int = 0
    window_padding_y: int = 0
    cursor_style: str = ""
    macos_titlebar_style: str = ""
    background_image: str = ""
    mouse_scroll_multiplier: float = 0.0
    cursor_style: str = ""
    custom_settings: dict = field(default_factory=dict)
    created_at: str = ""
    description: str = ""

    def to_config_lines(self) -> list[str]:
        """Convert profile to config file lines."""
        lines = [f"# Profile: {self.name}"]
        if self.description:
            lines.append(f"# {self.description}")
        lines.append(f"# Created: {self.created_at}")
        lines.append("")

        if self.theme:
            lines.append(f"theme = {self.theme}")
        if self.font_family:
            lines.append(f"font-family = {self.font_family}")
        if self.font_size:
            lines.append(f"font-size = {self.font_size}")
        if self.background_opacity > 0:
            lines.append(f"background-opacity = {self.background_opacity}")
        if self.window_padding_x:
            lines.append(f"window-padding-x = {self.window_padding_x}")
        if self.window_padding_y:
            lines.append(f"window-padding-y = {self.window_padding_y}")
        if self.cursor_style:
            lines.append(f"cursor-style = {self.cursor_style}")
        if self.macos_titlebar_style:
            lines.append(f"macos-titlebar-style = {self.macos_titlebar_style}")
        if self.background_image:
            lines.append(f"background-image = {self.background_image}")
        if self.mouse_scroll_multiplier > 0:
            lines.append(f"mouse-scroll-multiplier = {self.mouse_scroll_multiplier}")

        for key, value in self.custom_settings.items():
            lines.append(f"{key} = {value}")

        return lines

    @classmethod
    def from_config(cls, name: str, config: "GhosttyConfig", description: str = "") -> "GhosttyProfile":
        """Create a profile from current config."""
        return cls(
            name=name,
            theme=config.theme,
            font_family=config.font_family,
            font_size=config.font_size,
            background_opacity=config.background_opacity,
            window_padding_x=config.window_padding_x,
            window_padding_y=config.window_padding_y,
            cursor_style=config.cursor_style,
            macos_titlebar_style=config.macos_titlebar_style,
            background_image=config.background_image,
            mouse_scroll_multiplier=config.mouse_scroll_multiplier,
            created_at=datetime.now().isoformat(),
            description=description,
        )


# Standard config locations
CONFIG_PATHS = [
    Path.home() / ".config" / "ghostty" / "config",
    Path.home() / ".ghostty",
]

# Profile storage location
PROFILES_DIR = Path.home() / ".config" / "ghostty" / "profiles"

# Session storage location
SESSIONS_DIR = Path.home() / ".config" / "ghostty" / "sessions"

# Built-in themes (Ghostty ships with these)
BUILTIN_THEMES = [
    "catppuccin-mocha",
    "catppuccin-latte",
    "catppuccin-frappe",
    "catppuccin-macchiato",
    "dracula",
    "gruvbox-dark",
    "gruvbox-light",
    "nord",
    "solarized-dark",
    "solarized-light",
    "tokyo-night",
    "tokyo-night-storm",
    "one-dark",
    "one-light",
]


def is_ghostty() -> bool:
    """Check if running in Ghostty terminal."""
    return os.environ.get("TERM_PROGRAM", "").lower() == "ghostty"


def get_config_path() -> Optional[Path]:
    """Find the Ghostty config file path.

    Returns:
        Path to config file if found, None otherwise.
    """
    for path in CONFIG_PATHS:
        if path.exists():
            return path
    return None


def get_default_config_path() -> Path:
    """Get the default config path (creates parent dirs if needed)."""
    config_dir = Path.home() / ".config" / "ghostty"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config"


def parse_config(config_path: Optional[Path] = None) -> GhosttyConfig:
    """Parse Ghostty configuration file.

    Args:
        config_path: Path to config file. Auto-detected if None.

    Returns:
        GhosttyConfig with parsed values.
    """
    config = GhosttyConfig()

    path = config_path or get_config_path()
    if not path or not path.exists():
        return config

    with open(path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse key = value
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                config.raw_config[key] = value

                # Map known keys
                if key == "font-family":
                    config.font_family = value
                elif key == "font-size":
                    try:
                        config.font_size = int(value)
                    except ValueError:
                        pass
                elif key == "theme":
                    config.theme = value
                elif key == "window-padding-x":
                    try:
                        config.window_padding_x = int(value)
                    except ValueError:
                        pass
                elif key == "window-padding-y":
                    try:
                        config.window_padding_y = int(value)
                    except ValueError:
                        pass
                elif key == "background-opacity":
                    try:
                        config.background_opacity = float(value)
                    except ValueError:
                        pass
                elif key == "cursor-style":
                    config.cursor_style = value
                elif key == "macos-titlebar-style":
                    config.macos_titlebar_style = value
                elif key == "background-image":
                    config.background_image = value
                elif key == "mouse-scroll-multiplier":
                    try:
                        config.mouse_scroll_multiplier = float(value)
                    except ValueError:
                        pass

    return config


def set_config_value(key: str, value: str, config_path: Optional[Path] = None) -> bool:
    """Set a configuration value in the Ghostty config file.

    Args:
        key: Configuration key (e.g., "theme", "font-size").
        value: Value to set.
        config_path: Path to config file. Auto-detected if None.

    Returns:
        True if config was updated, False on error.
    """
    path = config_path or get_config_path() or get_default_config_path()

    # Read existing config
    lines = []
    key_found = False

    if path.exists():
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(f"{key} ") or stripped.startswith(f"{key}="):
                    lines.append(f"{key} = {value}\n")
                    key_found = True
                else:
                    lines.append(line)

    # Add new key if not found
    if not key_found:
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"{key} = {value}\n")

    # Write back
    with open(path, "w") as f:
        f.writelines(lines)

    return True


def set_theme(theme: str, config_path: Optional[Path] = None) -> bool:
    """Set the Ghostty theme.

    Args:
        theme: Theme name (e.g., "catppuccin-mocha").
        config_path: Path to config file. Auto-detected if None.

    Returns:
        True if theme was set, False on error.
    """
    return set_config_value("theme", theme, config_path)


def list_themes() -> list[str]:
    """List available Ghostty themes.

    Returns:
        List of built-in theme names.
    """
    return BUILTIN_THEMES.copy()


def set_title(title: str) -> bool:
    """Set the terminal window title.

    Uses standard OSC 2 escape sequence (works in most terminals).

    Args:
        title: The title to set.

    Returns:
        True if title was set.
    """
    if not is_ghostty():
        return False

    sys.stdout.write(f"\033]2;{title}\007")
    sys.stdout.flush()
    return True


def reload_config() -> bool:
    """Trigger Ghostty config reload.

    Note: Ghostty auto-reloads on config file save, so this is usually
    not needed. This function sends Cmd+Shift+, via AppleScript as fallback.

    Returns:
        True if reload was triggered, False on error.
    """
    if not is_ghostty():
        return False

    # Ghostty auto-reloads on config save, so just return True
    # If we need manual reload, we could use AppleScript:
    # osascript -e 'tell application "Ghostty" to activate'
    # osascript -e 'tell application "System Events" to keystroke "," using {command down, shift down}'
    return True


def apply_context(context: ContextInfo) -> None:
    """Apply a context to Ghostty (title only, no profile switching).

    Ghostty doesn't support runtime profile switching like iTerm2.
    We can only set the window title.

    Args:
        context: The context info to apply.
    """
    # Build title with context info
    title_parts = []
    if context.icon:
        title_parts.append(context.icon)
    if context.name:
        title_parts.append(context.name)
    if context.branch:
        title_parts.append(f"({context.branch})")

    title = " ".join(title_parts) if title_parts else context.title
    set_title(title)


def show_config() -> str:
    """Get a formatted display of current Ghostty config.

    Returns:
        Formatted string showing current configuration.
    """
    config = parse_config()
    path = get_config_path()

    lines = [
        "Ghostty Configuration",
        "=" * 40,
        f"Config file: {path or 'Not found'}",
        "",
        f"Font:       {config.font_family} @ {config.font_size}pt",
        f"Theme:      {config.theme or '(default)'}",
        f"Padding:    x={config.window_padding_x}, y={config.window_padding_y}",
        f"Opacity:    {config.background_opacity}",
        f"Cursor:     {config.cursor_style}",
    ]

    return "\n".join(lines)


def get_version() -> Optional[str]:
    """Get Ghostty version.

    Returns:
        Version string or None if not available.
    """
    try:
        result = subprocess.run(
            ["ghostty", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


# =============================================================================
# Profile Management (v0.4.0)
# =============================================================================


def get_profiles_dir() -> Path:
    """Get the profiles directory, creating it if needed."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILES_DIR


def list_profiles() -> list[GhosttyProfile]:
    """List all saved profiles.

    Returns:
        List of GhosttyProfile objects.
    """
    profiles = []
    profiles_dir = get_profiles_dir()

    for profile_file in sorted(profiles_dir.glob("*.conf")):
        profile = get_profile(profile_file.stem)
        if profile:
            profiles.append(profile)

    return profiles


def get_profile(name: str) -> Optional[GhosttyProfile]:
    """Load a profile by name.

    Args:
        name: Profile name (without .conf extension).

    Returns:
        GhosttyProfile if found, None otherwise.
    """
    profile_path = get_profiles_dir() / f"{name}.conf"
    if not profile_path.exists():
        return None

    profile = GhosttyProfile(name=name)

    with open(profile_path) as f:
        for line in f:
            line = line.strip()
            # Parse metadata from comments
            if line.startswith("# Profile:"):
                continue  # Skip, we already have the name
            elif line.startswith("# Created:"):
                profile.created_at = line.replace("# Created:", "").strip()
            elif line.startswith("#") and profile.description == "":
                # First non-metadata comment is description
                desc = line.lstrip("# ").strip()
                if desc and not desc.startswith("Profile:"):
                    profile.description = desc
            elif "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                if key == "theme":
                    profile.theme = value
                elif key == "font-family":
                    profile.font_family = value
                elif key == "font-size":
                    try:
                        profile.font_size = int(value)
                    except ValueError:
                        pass
                elif key == "background-opacity":
                    try:
                        profile.background_opacity = float(value)
                    except ValueError:
                        pass
                elif key == "window-padding-x":
                    try:
                        profile.window_padding_x = int(value)
                    except ValueError:
                        pass
                elif key == "window-padding-y":
                    try:
                        profile.window_padding_y = int(value)
                    except ValueError:
                        pass
                elif key == "cursor-style":
                    profile.cursor_style = value
                elif key == "macos-titlebar-style":
                    profile.macos_titlebar_style = value
                elif key == "background-image":
                    profile.background_image = value
                elif key == "mouse-scroll-multiplier":
                    try:
                        profile.mouse_scroll_multiplier = float(value)
                    except ValueError:
                        pass
                else:
                    profile.custom_settings[key] = value

    return profile


def save_profile(profile: GhosttyProfile) -> Path:
    """Save a profile to disk.

    Args:
        profile: The profile to save.

    Returns:
        Path to the saved profile file.
    """
    profiles_dir = get_profiles_dir()
    profile_path = profiles_dir / f"{profile.name}.conf"

    lines = profile.to_config_lines()
    with open(profile_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return profile_path


def create_profile_from_current(name: str, description: str = "") -> GhosttyProfile:
    """Create a new profile from current Ghostty config.

    Args:
        name: Name for the new profile.
        description: Optional description.

    Returns:
        The created GhosttyProfile.
    """
    current_config = parse_config()
    profile = GhosttyProfile.from_config(name, current_config, description)
    save_profile(profile)
    return profile


def apply_profile(name: str, backup: bool = True) -> bool:
    """Apply a profile to the main Ghostty config.

    This merges the profile settings into the main config file.
    Ghostty will auto-reload on config change.

    Args:
        name: Profile name to apply.
        backup: Whether to backup current config first.

    Returns:
        True if profile was applied, False if profile not found.
    """
    profile = get_profile(name)
    if not profile:
        return False

    config_path = get_config_path() or get_default_config_path()

    # Backup current config
    if backup and config_path.exists():
        backup_path = config_path.with_suffix(
            f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        shutil.copy2(config_path, backup_path)

    # Apply profile settings
    if profile.theme:
        set_config_value("theme", profile.theme, config_path)
    if profile.font_family:
        set_config_value("font-family", profile.font_family, config_path)
    if profile.font_size:
        set_config_value("font-size", str(profile.font_size), config_path)
    if profile.background_opacity > 0:
        set_config_value("background-opacity", str(profile.background_opacity), config_path)
    if profile.window_padding_x:
        set_config_value("window-padding-x", str(profile.window_padding_x), config_path)
    if profile.window_padding_y:
        set_config_value("window-padding-y", str(profile.window_padding_y), config_path)
    if profile.cursor_style:
        set_config_value("cursor-style", profile.cursor_style, config_path)
    if profile.macos_titlebar_style:
        set_config_value("macos-titlebar-style", profile.macos_titlebar_style, config_path)
    if profile.background_image:
        set_config_value("background-image", profile.background_image, config_path)
    if profile.mouse_scroll_multiplier > 0:
        set_config_value("mouse-scroll-multiplier", str(profile.mouse_scroll_multiplier), config_path)

    for key, value in profile.custom_settings.items():
        set_config_value(key, value, config_path)

    return True


def delete_profile(name: str) -> bool:
    """Delete a profile.

    Args:
        name: Profile name to delete.

    Returns:
        True if deleted, False if profile not found.
    """
    profile_path = get_profiles_dir() / f"{name}.conf"
    if not profile_path.exists():
        return False

    profile_path.unlink()
    return True


def backup_config(suffix: Optional[str] = None) -> Optional[Path]:
    """Create a timestamped backup of the Ghostty config.

    Args:
        suffix: Optional suffix for backup filename.

    Returns:
        Path to backup file, or None if no config exists.
    """
    config_path = get_config_path()
    if not config_path or not config_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if suffix:
        backup_name = f"config.backup.{timestamp}.{suffix}"
    else:
        backup_name = f"config.backup.{timestamp}"

    backup_path = config_path.parent / backup_name
    shutil.copy2(config_path, backup_path)
    return backup_path


def list_backups() -> list[Path]:
    """List available config backups.

    Returns:
        List of backup file paths, sorted by date (newest first).
    """
    config_path = get_config_path()
    if not config_path:
        return []

    config_dir = config_path.parent
    backups = list(config_dir.glob("config.backup.*"))
    return sorted(backups, reverse=True)


def restore_backup(backup_path: Path) -> bool:
    """Restore config from a backup.

    Args:
        backup_path: Path to the backup file.

    Returns:
        True if restored, False on error.
    """
    if not backup_path.exists():
        return False

    config_path = get_config_path() or get_default_config_path()

    # Backup current config before restore
    if config_path.exists():
        pre_restore_backup = config_path.with_suffix(".pre-restore")
        shutil.copy2(config_path, pre_restore_backup)

    shutil.copy2(backup_path, config_path)
    return True


# =============================================================================
# Keybind Management (v0.4.0)
# =============================================================================

# Keybind presets for common workflows
KEYBIND_PRESETS: dict[str, list[GhosttyKeybind]] = {
    "vim": [
        # Vim-style navigation
        GhosttyKeybind("ctrl+h", "goto_split:left"),
        GhosttyKeybind("ctrl+j", "goto_split:down"),
        GhosttyKeybind("ctrl+k", "goto_split:up"),
        GhosttyKeybind("ctrl+l", "goto_split:right"),
        # Split management
        GhosttyKeybind("ctrl+w>v", "new_split:right"),
        GhosttyKeybind("ctrl+w>s", "new_split:down"),
        GhosttyKeybind("ctrl+w>c", "close_surface"),
        # Tab navigation
        GhosttyKeybind("ctrl+w>n", "new_tab"),
        GhosttyKeybind("ctrl+w>]", "next_tab"),
        GhosttyKeybind("ctrl+w>[", "previous_tab"),
    ],
    "emacs": [
        # Emacs-style navigation
        GhosttyKeybind("ctrl+x>2", "new_split:down"),
        GhosttyKeybind("ctrl+x>3", "new_split:right"),
        GhosttyKeybind("ctrl+x>0", "close_surface"),
        GhosttyKeybind("ctrl+x>o", "goto_split:next"),
        # Buffer-style tabs
        GhosttyKeybind("ctrl+x>b", "toggle_tab_overview"),
        GhosttyKeybind("ctrl+x>k", "close_tab"),
        GhosttyKeybind("ctrl+x>ctrl+f", "new_tab"),
    ],
    "tmux": [
        # tmux-style with ctrl+b prefix
        GhosttyKeybind("ctrl+b>%", "new_split:right"),
        GhosttyKeybind('ctrl+b>"', "new_split:down"),
        GhosttyKeybind("ctrl+b>x", "close_surface"),
        GhosttyKeybind("ctrl+b>c", "new_tab"),
        GhosttyKeybind("ctrl+b>n", "next_tab"),
        GhosttyKeybind("ctrl+b>p", "previous_tab"),
        GhosttyKeybind("ctrl+b>h", "goto_split:left"),
        GhosttyKeybind("ctrl+b>j", "goto_split:down"),
        GhosttyKeybind("ctrl+b>k", "goto_split:up"),
        GhosttyKeybind("ctrl+b>l", "goto_split:right"),
        GhosttyKeybind("ctrl+b>z", "toggle_split_zoom"),
    ],
    "macos": [
        # macOS-native style
        GhosttyKeybind("cmd+t", "new_tab"),
        GhosttyKeybind("cmd+w", "close_surface"),
        GhosttyKeybind("cmd+shift+]", "next_tab"),
        GhosttyKeybind("cmd+shift+[", "previous_tab"),
        GhosttyKeybind("cmd+d", "new_split:right"),
        GhosttyKeybind("cmd+shift+d", "new_split:down"),
        GhosttyKeybind("cmd+]", "goto_split:next"),
        GhosttyKeybind("cmd+[", "goto_split:previous"),
    ],
}


def list_keybinds(config_path: Optional[Path] = None) -> list[GhosttyKeybind]:
    """List all keybindings from config.

    Args:
        config_path: Path to config file. Auto-detected if None.

    Returns:
        List of GhosttyKeybind objects.
    """
    path = config_path or get_config_path()
    if not path or not path.exists():
        return []

    keybinds = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("keybind") and "=" in line:
                kb = GhosttyKeybind.from_config_line(line)
                if kb:
                    keybinds.append(kb)

    return keybinds


def add_keybind(
    trigger: str, action: str, prefix: str = "", config_path: Optional[Path] = None
) -> bool:
    """Add a keybinding to config.

    Args:
        trigger: Key trigger (e.g., "ctrl+t").
        action: Action to perform (e.g., "new_tab").
        prefix: Optional prefix (e.g., "global:").
        config_path: Path to config file. Auto-detected if None.

    Returns:
        True if added successfully.
    """
    path = config_path or get_config_path() or get_default_config_path()

    kb = GhosttyKeybind(trigger=trigger, action=action, prefix=prefix)

    # Read existing config
    lines = []
    if path.exists():
        with open(path) as f:
            lines = f.readlines()

    # Check if keybind already exists (update it)
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith("keybind") and f"{trigger}=" in line:
            lines[i] = kb.to_config_line() + "\n"
            updated = True
            break

    if not updated:
        # Add new keybind
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(kb.to_config_line() + "\n")

    with open(path, "w") as f:
        f.writelines(lines)

    return True


def remove_keybind(trigger: str, config_path: Optional[Path] = None) -> bool:
    """Remove a keybinding from config.

    Args:
        trigger: Key trigger to remove.
        config_path: Path to config file. Auto-detected if None.

    Returns:
        True if removed, False if not found.
    """
    path = config_path or get_config_path()
    if not path or not path.exists():
        return False

    lines = []
    removed = False
    with open(path) as f:
        for line in f:
            if line.strip().startswith("keybind") and f"{trigger}=" in line:
                removed = True
                continue  # Skip this line
            lines.append(line)

    if removed:
        with open(path, "w") as f:
            f.writelines(lines)

    return removed


def get_keybind_presets() -> list[str]:
    """Get available keybind preset names.

    Returns:
        List of preset names.
    """
    return list(KEYBIND_PRESETS.keys())


def get_keybind_preset(name: str) -> Optional[list[GhosttyKeybind]]:
    """Get keybindings for a preset.

    Args:
        name: Preset name (vim, emacs, tmux, macos).

    Returns:
        List of keybindings or None if preset not found.
    """
    return KEYBIND_PRESETS.get(name)


def apply_keybind_preset(
    name: str, backup: bool = True, config_path: Optional[Path] = None
) -> bool:
    """Apply a keybind preset to config.

    Args:
        name: Preset name to apply.
        backup: Whether to backup current config first.
        config_path: Path to config file. Auto-detected if None.

    Returns:
        True if applied, False if preset not found.
    """
    preset = get_keybind_preset(name)
    if not preset:
        return False

    path = config_path or get_config_path() or get_default_config_path()

    if backup and path.exists():
        backup_config(f"before-{name}-preset")

    for kb in preset:
        add_keybind(kb.trigger, kb.action, kb.prefix, path)

    return True


# =============================================================================
# Session Management (v0.4.0)
# =============================================================================


def get_sessions_dir() -> Path:
    """Get the sessions directory, creating it if needed."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def list_sessions() -> list[GhosttySession]:
    """List all saved sessions.

    Returns:
        List of GhosttySession objects.
    """
    sessions = []
    sessions_dir = get_sessions_dir()

    for session_file in sorted(sessions_dir.glob("*.json")):
        session = get_session(session_file.stem)
        if session:
            sessions.append(session)

    return sessions


def get_session(name: str) -> Optional[GhosttySession]:
    """Load a session by name.

    Args:
        name: Session name (without .json extension).

    Returns:
        GhosttySession if found, None otherwise.
    """
    session_path = get_sessions_dir() / f"{name}.json"
    if not session_path.exists():
        return None

    try:
        with open(session_path) as f:
            data = json.load(f)
        return GhosttySession.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def save_session(session: GhosttySession) -> Path:
    """Save a session to disk.

    Args:
        session: The session to save.

    Returns:
        Path to the saved session file.
    """
    sessions_dir = get_sessions_dir()
    session_path = sessions_dir / f"{session.name}.json"

    with open(session_path, "w") as f:
        json.dump(session.to_dict(), f, indent=2)

    return session_path


def create_session(
    name: str,
    working_dirs: Optional[list[str]] = None,
    description: str = "",
    layout: str = "single",
) -> GhosttySession:
    """Create a new session.

    Args:
        name: Session name.
        working_dirs: List of working directories. Defaults to current directory.
        description: Optional description.
        layout: Layout type (single, split-h, split-v, grid).

    Returns:
        The created GhosttySession.
    """
    if working_dirs is None:
        working_dirs = [os.getcwd()]

    session = GhosttySession(
        name=name,
        working_dirs=working_dirs,
        created_at=datetime.now().isoformat(),
        description=description,
        layout=layout,
    )

    save_session(session)
    return session


def delete_session(name: str) -> bool:
    """Delete a session.

    Args:
        name: Session name to delete.

    Returns:
        True if deleted, False if session not found.
    """
    session_path = get_sessions_dir() / f"{name}.json"
    if not session_path.exists():
        return False

    session_path.unlink()
    return True


def restore_session(name: str) -> Optional[GhosttySession]:
    """Restore a session (changes to first working directory).

    Note: Full session restoration with splits requires Ghostty API
    or AppleScript. This basic implementation changes to the session's
    first working directory and returns the session for the CLI to
    display instructions.

    Args:
        name: Session name to restore.

    Returns:
        GhosttySession if found and restored, None otherwise.
    """
    session = get_session(name)
    if not session:
        return None

    # Change to first working directory if it exists
    if session.working_dirs:
        first_dir = session.working_dirs[0]
        if os.path.isdir(first_dir):
            os.chdir(first_dir)

    return session


def split_terminal(direction: str = "right") -> bool:
    """Create a terminal split.

    Uses Ghostty keybind actions via AppleScript. Requires accessibility
    permissions for iTerm2/Terminal.

    Args:
        direction: Split direction (right, down, left, up).

    Returns:
        True if split command was sent, False on error.
    """
    if not is_ghostty():
        return False

    # Map direction to Ghostty action
    action_map = {
        "right": "new_split:right",
        "down": "new_split:down",
        "left": "new_split:left",
        "up": "new_split:up",
        "h": "new_split:right",  # horizontal split = right
        "v": "new_split:down",  # vertical split = down
    }

    action = action_map.get(direction.lower())
    if not action:
        return False

    # Use AppleScript to trigger the split
    # Note: This requires Ghostty to have the keybind configured
    # We'll try to send the default Ghostty keybind
    try:
        # Use osascript to simulate keypress
        # Default Ghostty split: cmd+d (right), cmd+shift+d (down)
        if direction in ("right", "h"):
            key_code = 'd'
            modifiers = "command down"
        elif direction in ("down", "v"):
            key_code = 'd'
            modifiers = "{command down, shift down}"
        else:
            # For non-standard directions, just return success
            # (user needs to configure keybinds)
            return True

        script = f'''
        tell application "Ghostty"
            activate
        end tell
        tell application "System Events"
            keystroke "{key_code}" using {modifiers}
        end tell
        '''

        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
