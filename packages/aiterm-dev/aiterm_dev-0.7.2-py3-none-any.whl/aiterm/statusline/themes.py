"""StatusLine color themes.

This module defines color themes for the statusLine, including:
- purple-charcoal (default)
- cool-blues
- forest-greens

Each theme specifies ANSI color codes for different segments.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """Color theme for statusLine.

    Attributes:
        name: Theme name
        dir_bg: Directory segment background color
        dir_fg: Directory segment foreground color
        dir_short: Color for shortened paths
        dir_anchor: Color for anchor/important parts
        vcs_clean_bg: VCS background when clean
        vcs_modified_bg: VCS background when modified
        vcs_fg: VCS foreground color
        meta_fg: Color for metadata symbols
        model_sonnet: Color for Sonnet model
        model_opus: Color for Opus model
        model_haiku: Color for Haiku model
        time_fg: Color for time display
        duration_fg: Color for duration display
        lines_added_fg: Color for added lines
        lines_removed_fg: Color for removed lines
        separator_fg: Color for separators (│)
        thinking_fg: Color for thinking indicator
        style_fg: Color for output style
    """

    name: str

    # Directory segment
    dir_bg: str
    dir_fg: str
    dir_short: str
    dir_anchor: str

    # VCS segment
    vcs_clean_bg: str
    vcs_modified_bg: str
    vcs_fg: str

    # Meta colors
    meta_fg: str

    # Model colors
    model_sonnet: str
    model_opus: str
    model_haiku: str

    # Time/duration
    time_fg: str
    duration_fg: str

    # Lines changed
    lines_added_fg: str
    lines_removed_fg: str

    # UI elements
    separator_fg: str
    thinking_fg: str
    style_fg: str

    def get_ansi(self, key: str) -> str:
        """Get ANSI color code for a key.

        Args:
            key: Color key (e.g., 'dir_bg', 'vcs_fg')

        Returns:
            ANSI color code (e.g., '48;5;54')
        """
        return getattr(self, key, '')


# =============================================================================
# Theme Definitions
# =============================================================================


PURPLE_CHARCOAL = Theme(
    name="purple-charcoal",

    # Directory segment - deep purple background
    dir_bg="48;5;54",       # Deep purple
    dir_fg="38;5;250",      # Light gray
    dir_short="38;5;245",   # Medium gray for shortened
    dir_anchor="38;5;255;1",  # Bright white bold for anchor

    # VCS segment - charcoal and purple
    vcs_clean_bg="48;5;236",     # Charcoal background (clean)
    vcs_modified_bg="48;5;60",   # Slate purple (modified)
    vcs_fg="38;5;250",           # Light gray

    # Meta colors
    meta_fg="38;5;7",       # White for symbols

    # Model colors
    model_sonnet="38;5;147",   # Medium blue
    model_opus="38;5;177",     # Purple
    model_haiku="38;5;183",    # Light blue

    # Time/duration
    time_fg="38;5;183",        # Light blue
    duration_fg="38;5;139",    # Muted purple

    # Lines changed
    lines_added_fg="38;5;183",   # Light blue
    lines_removed_fg="38;5;168", # Rose

    # UI elements
    separator_fg="38;5;240",   # Dark gray
    thinking_fg="38;5;177",    # Purple (matches opus)
    style_fg="38;5;183",       # Light blue
)


COOL_BLUES = Theme(
    name="cool-blues",

    # Directory segment - ocean blue
    dir_bg="48;5;24",       # Deep ocean blue
    dir_fg="38;5;254",      # Off-white
    dir_short="38;5;249",   # Light gray for shortened
    dir_anchor="38;5;255;1",  # Bright white bold

    # VCS segment - navy and sky
    vcs_clean_bg="48;5;235",     # Dark navy (clean)
    vcs_modified_bg="48;5;31",   # Sky blue (modified)
    vcs_fg="38;5;254",           # Off-white

    # Meta colors
    meta_fg="38;5;15",      # Bright white

    # Model colors
    model_sonnet="38;5;117",   # Sky blue
    model_opus="38;5;147",     # Steel blue
    model_haiku="38;5;159",    # Pale blue

    # Time/duration
    time_fg="38;5;159",        # Pale blue
    duration_fg="38;5;117",    # Sky blue

    # Lines changed
    lines_added_fg="38;5;159",   # Pale blue
    lines_removed_fg="38;5;210", # Salmon

    # UI elements
    separator_fg="38;5;238",   # Medium gray
    thinking_fg="38;5;147",    # Steel blue
    style_fg="38;5;159",       # Pale blue
)


FOREST_GREENS = Theme(
    name="forest-greens",

    # Directory segment - forest green
    dir_bg="48;5;22",       # Dark forest green
    dir_fg="38;5;252",      # Light gray
    dir_short="38;5;246",   # Medium gray
    dir_anchor="38;5;255;1",  # Bright white bold

    # VCS segment - moss and sage
    vcs_clean_bg="48;5;235",     # Charcoal (clean)
    vcs_modified_bg="48;5;64",   # Sage green (modified)
    vcs_fg="38;5;252",           # Light gray

    # Meta colors
    meta_fg="38;5;15",      # Bright white

    # Model colors
    model_sonnet="38;5;114",   # Pale green
    model_opus="38;5;149",     # Yellow-green
    model_haiku="38;5;156",    # Lime

    # Time/duration
    time_fg="38;5;156",        # Lime
    duration_fg="38;5;114",    # Pale green

    # Lines changed
    lines_added_fg="38;5;156",   # Lime (additions)
    lines_removed_fg="38;5;209", # Peach (removals)

    # UI elements
    separator_fg="38;5;239",   # Dark gray
    thinking_fg="38;5;149",    # Yellow-green
    style_fg="38;5;156",       # Lime
)


# Theme registry
THEMES: Dict[str, Theme] = {
    "purple-charcoal": PURPLE_CHARCOAL,
    "cool-blues": COOL_BLUES,
    "forest-greens": FOREST_GREENS,
}


def get_theme(name: str) -> Theme:
    """Get theme by name.

    Args:
        name: Theme name

    Returns:
        Theme object

    Raises:
        ValueError: If theme not found
    """
    if name not in THEMES:
        raise ValueError(
            f"Theme '{name}' not found. "
            f"Available themes: {', '.join(THEMES.keys())}"
        )
    return THEMES[name]


def list_themes() -> list[str]:
    """Get list of available theme names.

    Returns:
        List of theme names
    """
    return list(THEMES.keys())


class ThemeManager:
    """Manages theme loading and application."""

    def __init__(self, config):
        """Initialize theme manager.

        Args:
            config: StatusLineConfig instance
        """
        self.config = config

    def get_current_theme(self) -> Theme:
        """Get currently active theme.

        Returns:
            Theme object
        """
        theme_name = self.config.get('theme.name', 'purple-charcoal')
        return get_theme(theme_name)

    def set_theme(self, theme_name: str) -> None:
        """Set active theme.

        Args:
            theme_name: Theme name to activate

        Raises:
            ValueError: If theme not found
        """
        # Validate theme exists
        get_theme(theme_name)

        # Update config
        self.config.set('theme.name', theme_name)

    def list_available_themes(self) -> list[dict]:
        """List available themes with metadata.

        Returns:
            List of dicts with theme info
        """
        themes_list = []
        current = self.get_current_theme().name

        for name in list_themes():
            theme = get_theme(name)
            themes_list.append({
                'name': name,
                'active': (name == current),
                'description': self._get_theme_description(name)
            })

        return themes_list

    def _get_theme_description(self, name: str) -> str:
        """Get human-readable description for theme.

        Args:
            name: Theme name

        Returns:
            Description string
        """
        descriptions = {
            'purple-charcoal': 'Deep purple with charcoal accents (default)',
            'cool-blues': 'Ocean blues with sky accents',
            'forest-greens': 'Forest greens with sage accents'
        }
        return descriptions.get(name, 'Custom theme')
