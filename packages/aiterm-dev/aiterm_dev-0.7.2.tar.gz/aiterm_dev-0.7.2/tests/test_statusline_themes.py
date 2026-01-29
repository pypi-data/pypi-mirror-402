"""Tests for StatusLine theme system."""

import pytest
from pathlib import Path

from aiterm.statusline.themes import (
    Theme,
    get_theme,
    list_themes,
    ThemeManager,
    PURPLE_CHARCOAL,
    COOL_BLUES,
    FOREST_GREENS,
)
from aiterm.statusline.config import StatusLineConfig


class TestTheme:
    """Test Theme dataclass."""

    def test_theme_has_all_required_attributes(self):
        """Test theme has all required color attributes."""
        theme = PURPLE_CHARCOAL

        # Check all required attributes exist
        assert hasattr(theme, 'name')
        assert hasattr(theme, 'dir_bg')
        assert hasattr(theme, 'dir_fg')
        assert hasattr(theme, 'dir_short')
        assert hasattr(theme, 'dir_anchor')
        assert hasattr(theme, 'vcs_clean_bg')
        assert hasattr(theme, 'vcs_modified_bg')
        assert hasattr(theme, 'vcs_fg')
        assert hasattr(theme, 'meta_fg')
        assert hasattr(theme, 'model_sonnet')
        assert hasattr(theme, 'model_opus')
        assert hasattr(theme, 'model_haiku')
        assert hasattr(theme, 'time_fg')
        assert hasattr(theme, 'duration_fg')
        assert hasattr(theme, 'lines_added_fg')
        assert hasattr(theme, 'lines_removed_fg')
        assert hasattr(theme, 'separator_fg')
        assert hasattr(theme, 'thinking_fg')
        assert hasattr(theme, 'style_fg')

    def test_theme_colors_are_valid_ansi(self):
        """Test theme colors are valid ANSI codes."""
        theme = PURPLE_CHARCOAL

        # Check a few color codes are in correct format
        # Background colors: 48;5;N
        assert theme.dir_bg.startswith('48;5;')
        assert theme.vcs_clean_bg.startswith('48;5;')

        # Foreground colors: 38;5;N
        assert theme.dir_fg.startswith('38;5;')
        assert theme.model_sonnet.startswith('38;5;')

    def test_get_ansi_method(self):
        """Test get_ansi method."""
        theme = PURPLE_CHARCOAL

        # Test getting various color codes
        assert theme.get_ansi('dir_bg') == '48;5;54'
        assert theme.get_ansi('dir_fg') == '38;5;250'
        assert theme.get_ansi('model_sonnet') == '38;5;147'

        # Test non-existent key returns empty string
        assert theme.get_ansi('nonexistent') == ''


class TestThemeLoading:
    """Test theme loading functions."""

    def test_get_theme_by_name(self):
        """Test loading theme by name."""
        theme = get_theme('purple-charcoal')
        assert theme.name == 'purple-charcoal'
        assert isinstance(theme, Theme)

    def test_get_theme_invalid_name(self):
        """Test loading invalid theme raises error."""
        with pytest.raises(ValueError, match="Theme 'invalid' not found"):
            get_theme('invalid')

    def test_list_themes(self):
        """Test listing all themes."""
        themes = list_themes()

        assert isinstance(themes, list)
        assert 'purple-charcoal' in themes
        assert 'cool-blues' in themes
        assert 'forest-greens' in themes
        assert len(themes) == 3


class TestThemeDefinitions:
    """Test specific theme definitions."""

    def test_purple_charcoal_theme(self):
        """Test purple-charcoal theme definition."""
        theme = PURPLE_CHARCOAL

        assert theme.name == 'purple-charcoal'
        assert theme.dir_bg == '48;5;54'  # Deep purple
        assert theme.dir_fg == '38;5;250'  # Light gray

    def test_cool_blues_theme(self):
        """Test cool-blues theme definition."""
        theme = COOL_BLUES

        assert theme.name == 'cool-blues'
        assert theme.dir_bg == '48;5;24'  # Ocean blue
        assert theme.dir_fg == '38;5;254'  # Off-white

    def test_forest_greens_theme(self):
        """Test forest-greens theme definition."""
        theme = FOREST_GREENS

        assert theme.name == 'forest-greens'
        assert theme.dir_bg == '48;5;22'  # Forest green
        assert theme.dir_fg == '38;5;252'  # Light gray


class TestThemeManager:
    """Test ThemeManager class."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config in temp directory."""
        config_dir = tmp_path / ".config" / "aiterm"
        config_dir.mkdir(parents=True)

        # Create config instance pointing to temp dir
        config = StatusLineConfig()
        config.config_path = config_dir / "statusline.json"

        # Initialize with default settings
        config.save(config.load())

        return config

    @pytest.fixture
    def manager(self, config):
        """Create ThemeManager with test config."""
        return ThemeManager(config)

    def test_get_current_theme_default(self, manager):
        """Test getting current theme (default)."""
        theme = manager.get_current_theme()

        assert theme.name == 'purple-charcoal'
        assert isinstance(theme, Theme)

    def test_set_theme(self, manager):
        """Test setting theme."""
        # Initially purple-charcoal
        assert manager.get_current_theme().name == 'purple-charcoal'

        # Change to cool-blues
        manager.set_theme('cool-blues')
        assert manager.get_current_theme().name == 'cool-blues'

        # Change to forest-greens
        manager.set_theme('forest-greens')
        assert manager.get_current_theme().name == 'forest-greens'

    def test_set_invalid_theme(self, manager):
        """Test setting invalid theme raises error."""
        with pytest.raises(ValueError, match="Theme 'invalid' not found"):
            manager.set_theme('invalid')

    def test_list_available_themes(self, manager):
        """Test listing available themes with metadata."""
        themes = manager.list_available_themes()

        assert isinstance(themes, list)
        assert len(themes) == 3

        # Check structure of first theme
        theme_info = themes[0]
        assert 'name' in theme_info
        assert 'active' in theme_info
        assert 'description' in theme_info

        # Check active theme is marked
        active_themes = [t for t in themes if t['active']]
        assert len(active_themes) == 1
        assert active_themes[0]['name'] == 'purple-charcoal'

    def test_theme_persists_after_change(self, manager):
        """Test theme setting persists to config file."""
        # Change theme
        manager.set_theme('cool-blues')

        # Create new manager (simulates restart)
        new_manager = ThemeManager(manager.config)

        # Theme should still be cool-blues
        assert new_manager.get_current_theme().name == 'cool-blues'


class TestThemeDescriptions:
    """Test theme descriptions."""

    @pytest.fixture
    def manager(self):
        """Create ThemeManager for testing."""
        config = StatusLineConfig()
        return ThemeManager(config)

    def test_theme_descriptions(self, manager):
        """Test all themes have descriptions."""
        themes = manager.list_available_themes()

        for theme in themes:
            assert theme['description']
            assert len(theme['description']) > 0

    def test_default_theme_description(self, manager):
        """Test default theme has '(default)' in description."""
        themes = manager.list_available_themes()

        purple_charcoal = next(t for t in themes if t['name'] == 'purple-charcoal')
        assert '(default)' in purple_charcoal['description']


class TestThemeIntegrationWithSegments:
    """Test theme integration with segments."""

    def test_segments_accept_theme_parameter(self):
        """Test all segments accept theme parameter."""
        from aiterm.statusline.segments import (
            ProjectSegment,
            GitSegment,
            ModelSegment,
            TimeSegment,
            ThinkingSegment,
            LinesSegment,
        )

        config = StatusLineConfig()
        theme = get_theme('cool-blues')

        # All segments should accept theme parameter
        project = ProjectSegment(config, theme)
        git = GitSegment(config, theme)
        model = ModelSegment(config, theme)
        time = TimeSegment(config, theme)
        thinking = ThinkingSegment(config, theme)
        lines = LinesSegment(config, theme)

        # Verify theme is stored
        assert project.theme == theme
        assert git.theme == theme
        assert model.theme == theme
        assert time.theme == theme
        assert thinking.theme == theme
        assert lines.theme == theme

    def test_segments_use_theme_colors(self):
        """Test segments actually use theme colors in output."""
        from aiterm.statusline.segments import ModelSegment

        config = StatusLineConfig()

        # Test with purple-charcoal
        purple_theme = get_theme('purple-charcoal')
        model_purple = ModelSegment(config, purple_theme)
        output_purple = model_purple.render("Claude Sonnet 4.5")

        # Should use purple-charcoal's model_sonnet color
        assert '38;5;147' in output_purple

        # Test with cool-blues
        blues_theme = get_theme('cool-blues')
        model_blues = ModelSegment(config, blues_theme)
        output_blues = model_blues.render("Claude Sonnet 4.5")

        # Should use cool-blues's model_sonnet color
        assert '38;5;117' in output_blues


class TestThemeColorConsistency:
    """Test theme color consistency across all themes."""

    def test_all_themes_have_same_attributes(self):
        """Test all themes define the same set of attributes."""
        themes = [PURPLE_CHARCOAL, COOL_BLUES, FOREST_GREENS]

        # Get attributes from first theme
        base_attrs = set(vars(themes[0]).keys())

        # Check all themes have same attributes
        for theme in themes[1:]:
            theme_attrs = set(vars(theme).keys())
            assert theme_attrs == base_attrs, f"Theme {theme.name} has different attributes"

    def test_all_color_codes_valid_format(self):
        """Test all color codes in all themes are valid ANSI."""
        themes = [PURPLE_CHARCOAL, COOL_BLUES, FOREST_GREENS]

        for theme in themes:
            attrs = vars(theme)
            for key, value in attrs.items():
                if key == 'name':
                    continue  # Skip name attribute

                # All color codes should be strings
                assert isinstance(value, str), f"{theme.name}.{key} is not a string"

                # Should start with either 48;5; (background) or 38;5; (foreground)
                assert value.startswith('48;5;') or value.startswith('38;5;'), \
                    f"{theme.name}.{key} has invalid ANSI code format: {value}"
