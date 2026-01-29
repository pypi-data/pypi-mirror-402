"""
Config module for aiterm.

Provides XDG-compliant configuration path management with
AITERM_CONFIG_HOME environment variable support.
"""

from aiterm.config.paths import (
    CONFIG_FILE,
    CONFIG_HOME,
    PROFILES_DIR,
    THEMES_DIR,
    ensure_config_dir,
    get_config_file,
    get_config_home,
)

__all__ = [
    "get_config_home",
    "get_config_file",
    "ensure_config_dir",
    "CONFIG_HOME",
    "CONFIG_FILE",
    "PROFILES_DIR",
    "THEMES_DIR",
]
