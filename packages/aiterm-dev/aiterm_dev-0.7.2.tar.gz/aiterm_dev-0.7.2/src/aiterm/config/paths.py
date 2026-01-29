"""
XDG-compliant path resolution for aiterm configuration.

Priority order:
1. AITERM_CONFIG_HOME (if set)
2. XDG_CONFIG_HOME/aiterm (if XDG_CONFIG_HOME set)
3. ~/.config/aiterm (default)

Example usage:
    from aiterm.config import get_config_home, CONFIG_FILE

    config_dir = get_config_home()
    # /Users/user/.config/aiterm

    config_file = CONFIG_FILE
    # /Users/user/.config/aiterm/config.toml
"""

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_config_home() -> Path:
    """
    Get aiterm config directory.

    Priority:
    1. AITERM_CONFIG_HOME (if set)
    2. XDG_CONFIG_HOME/aiterm (if XDG_CONFIG_HOME set)
    3. ~/.config/aiterm (default)

    Returns:
        Path to config directory (may not exist yet)
    """
    # Check AITERM_CONFIG_HOME first
    if env_path := os.environ.get("AITERM_CONFIG_HOME"):
        return Path(env_path).expanduser()

    # Check XDG_CONFIG_HOME
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "aiterm"

    # Default: ~/.config/aiterm
    return Path.home() / ".config" / "aiterm"


def get_config_file() -> Path:
    """Get path to main config file (config.toml)."""
    return get_config_home() / "config.toml"


def get_profiles_dir() -> Path:
    """Get path to profiles directory."""
    return get_config_home() / "profiles"


def get_themes_dir() -> Path:
    """Get path to themes directory."""
    return get_config_home() / "themes"


def get_cache_dir() -> Path:
    """Get path to cache directory."""
    return get_config_home() / "cache"


def ensure_config_dir() -> Path:
    """
    Ensure config directory exists, creating if necessary.

    Returns:
        Path to config directory
    """
    config_home = get_config_home()
    config_home.mkdir(parents=True, exist_ok=True)
    return config_home


def ensure_profiles_dir() -> Path:
    """Ensure profiles directory exists."""
    profiles_dir = get_profiles_dir()
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir


def ensure_themes_dir() -> Path:
    """Ensure themes directory exists."""
    themes_dir = get_themes_dir()
    themes_dir.mkdir(parents=True, exist_ok=True)
    return themes_dir


# Convenience constants (evaluated at import time)
# Note: These use lru_cache so they're efficient
CONFIG_HOME = get_config_home()
CONFIG_FILE = get_config_file()
PROFILES_DIR = get_profiles_dir()
THEMES_DIR = get_themes_dir()
CACHE_DIR = get_cache_dir()
