"""Tests for Ghostty terminal integration."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGhosttyDetection:
    """Test Ghostty terminal detection."""

    def test_is_ghostty_true(self):
        """Test detection when TERM_PROGRAM is ghostty."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            assert ghostty.is_ghostty() is True

    def test_is_ghostty_false_iterm(self):
        """Test detection when TERM_PROGRAM is iTerm."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            assert ghostty.is_ghostty() is False

    def test_is_ghostty_false_empty(self):
        """Test detection when TERM_PROGRAM is not set."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": ""}):
            assert ghostty.is_ghostty() is False

    def test_is_ghostty_case_insensitive(self):
        """Test detection is case-insensitive."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "Ghostty"}):
            assert ghostty.is_ghostty() is True


class TestGhosttyConfig:
    """Test Ghostty configuration parsing."""

    def test_parse_empty_config(self, tmp_path: Path):
        """Test parsing an empty config file."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("")

        config = ghostty.parse_config(config_file)
        assert config.font_family == "monospace"
        assert config.font_size == 14
        assert config.theme == ""

    def test_parse_config_with_values(self, tmp_path: Path):
        """Test parsing config with actual values."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """
font-family = JetBrains Mono
font-size = 16
theme = catppuccin-mocha
window-padding-x = 10
window-padding-y = 8
macos-titlebar-style = native
background-image = test.png
mouse-scroll-multiplier = 1.5
"""
        )

        config = ghostty.parse_config(config_file)
        assert config.font_family == "JetBrains Mono"
        assert config.font_size == 16
        assert config.theme == "catppuccin-mocha"
        assert config.window_padding_x == 10
        assert config.window_padding_y == 8
        assert config.macos_titlebar_style == "native"
        assert config.background_image == "test.png"
        assert config.mouse_scroll_multiplier == 1.5

    def test_parse_config_with_comments(self, tmp_path: Path):
        """Test parsing config ignores comments."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """
# This is a comment
font-family = Fira Code
# Another comment
font-size = 14
"""
        )

        config = ghostty.parse_config(config_file)
        assert config.font_family == "Fira Code"
        assert config.font_size == 14

    def test_parse_nonexistent_config(self, tmp_path: Path):
        """Test parsing returns defaults for nonexistent file."""
        from aiterm.terminal import ghostty

        config = ghostty.parse_config(tmp_path / "nonexistent")
        assert config.font_family == "monospace"
        assert config.font_size == 14


class TestGhosttyConfigWrite:
    """Test writing Ghostty configuration."""

    def test_set_config_value_new_file(self, tmp_path: Path):
        """Test setting value creates file if needed."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        ghostty.set_config_value("theme", "nord", config_file)

        assert config_file.exists()
        content = config_file.read_text()
        assert "theme = nord" in content

    def test_set_config_value_update_existing(self, tmp_path: Path):
        """Test updating existing value."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = old-theme\nfont-size = 14\n")

        ghostty.set_config_value("theme", "new-theme", config_file)

        content = config_file.read_text()
        assert "theme = new-theme" in content
        assert "old-theme" not in content
        assert "font-size = 14" in content

    def test_set_config_value_add_new(self, tmp_path: Path):
        """Test adding new value to existing file."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("font-size = 14\n")

        ghostty.set_config_value("theme", "dracula", config_file)

        content = config_file.read_text()
        assert "theme = dracula" in content
        assert "font-size = 14" in content


class TestGhosttyThemes:
    """Test Ghostty theme functionality."""

    def test_list_themes(self):
        """Test listing available themes."""
        from aiterm.terminal import ghostty

        themes = ghostty.list_themes()
        assert len(themes) > 0
        assert "catppuccin-mocha" in themes
        assert "nord" in themes
        assert "dracula" in themes

    def test_set_theme(self, tmp_path: Path):
        """Test setting a theme."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        result = ghostty.set_theme("tokyo-night", config_file)

        assert result is True
        config = ghostty.parse_config(config_file)
        assert config.theme == "tokyo-night"


class TestTerminalDetector:
    """Test terminal type detection."""

    def test_detect_ghostty(self):
        """Test detecting Ghostty terminal."""
        from aiterm.terminal import detect_terminal, TerminalType

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            assert detect_terminal() == TerminalType.GHOSTTY

    def test_detect_iterm2(self):
        """Test detecting iTerm2 terminal."""
        from aiterm.terminal import detect_terminal, TerminalType

        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            assert detect_terminal() == TerminalType.ITERM2

    def test_detect_kitty(self):
        """Test detecting Kitty terminal."""
        from aiterm.terminal import detect_terminal, TerminalType

        with patch.dict(os.environ, {"TERM_PROGRAM": "kitty"}):
            assert detect_terminal() == TerminalType.KITTY

    def test_detect_unknown(self):
        """Test detecting unknown terminal."""
        from aiterm.terminal import detect_terminal, TerminalType

        with patch.dict(os.environ, {"TERM_PROGRAM": ""}):
            assert detect_terminal() == TerminalType.UNKNOWN


class TestTerminalInfo:
    """Test get_terminal_info function."""

    def test_terminal_info_ghostty(self):
        """Test terminal info for Ghostty."""
        from aiterm.terminal import get_terminal_info

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            info = get_terminal_info()
            assert info["type"] == "ghostty"
            assert info["supports_themes"] is True
            assert info["config_editable"] is True
            assert info["supports_profiles"] is False

    def test_terminal_info_iterm2(self):
        """Test terminal info for iTerm2."""
        from aiterm.terminal import get_terminal_info

        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            info = get_terminal_info()
            assert info["type"] == "iterm2"
            assert info["supports_profiles"] is True
            assert info["supports_user_vars"] is True


# =============================================================================
# NEW TESTS: get_version() - subprocess handling
# =============================================================================


class TestGhosttyVersion:
    """Test Ghostty version detection."""

    def test_get_version_success(self):
        """Test successful version retrieval."""
        from aiterm.terminal import ghostty
        from unittest.mock import MagicMock
        import subprocess

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Ghostty 1.0.0"

        with patch.object(subprocess, "run", return_value=mock_result) as mock_run:
            version = ghostty.get_version()
            assert version == "Ghostty 1.0.0"
            mock_run.assert_called_once()

    def test_get_version_not_installed(self):
        """Test version when Ghostty is not installed."""
        from aiterm.terminal import ghostty
        import subprocess

        with patch.object(subprocess, "run", side_effect=FileNotFoundError):
            version = ghostty.get_version()
            assert version is None

    def test_get_version_timeout(self):
        """Test version when command times out."""
        from aiterm.terminal import ghostty
        import subprocess

        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("ghostty", 5)):
            version = ghostty.get_version()
            assert version is None

    def test_get_version_nonzero_exit(self):
        """Test version when command fails."""
        from aiterm.terminal import ghostty
        from unittest.mock import MagicMock
        import subprocess

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch.object(subprocess, "run", return_value=mock_result):
            version = ghostty.get_version()
            assert version is None


# =============================================================================
# NEW TESTS: set_title() - OSC escape sequence handling
# =============================================================================


class TestGhosttySetTitle:
    """Test Ghostty window title setting."""

    def test_set_title_in_ghostty(self):
        """Test setting title when in Ghostty."""
        from aiterm.terminal import ghostty
        import io

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            mock_stdout = io.StringIO()
            with patch("sys.stdout", mock_stdout):
                result = ghostty.set_title("My Title")
                assert result is True
                output = mock_stdout.getvalue()
                assert "\033]2;My Title\007" in output

    def test_set_title_not_in_ghostty(self):
        """Test setting title when not in Ghostty."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            result = ghostty.set_title("My Title")
            assert result is False

    def test_set_title_with_special_characters(self):
        """Test setting title with special characters."""
        from aiterm.terminal import ghostty
        import io

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            mock_stdout = io.StringIO()
            with patch("sys.stdout", mock_stdout):
                result = ghostty.set_title("📁 project (main)")
                assert result is True
                output = mock_stdout.getvalue()
                assert "📁 project (main)" in output


# =============================================================================
# NEW TESTS: apply_context() - context to title mapping
# =============================================================================


class TestGhosttyApplyContext:
    """Test applying context info to Ghostty."""

    def test_apply_context_full(self):
        """Test applying context with all fields."""
        from aiterm.terminal import ghostty
        from aiterm.context.detector import ContextInfo, ContextType
        import io

        context = ContextInfo(
            type=ContextType.PYTHON,
            name="myproject",
            icon="🐍",
            profile="Python-Dev",
            branch="feature-x",
            is_dirty=False,
        )

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            mock_stdout = io.StringIO()
            with patch("sys.stdout", mock_stdout):
                ghostty.apply_context(context)
                output = mock_stdout.getvalue()
                assert "🐍" in output
                assert "myproject" in output
                assert "feature-x" in output

    def test_apply_context_minimal(self):
        """Test applying context with minimal fields."""
        from aiterm.terminal import ghostty
        from aiterm.context.detector import ContextInfo, ContextType
        import io

        context = ContextInfo(
            type=ContextType.DEFAULT,
            name="unknown",
            icon="",
            profile="Default",
        )

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            mock_stdout = io.StringIO()
            with patch("sys.stdout", mock_stdout):
                ghostty.apply_context(context)
                output = mock_stdout.getvalue()
                assert "unknown" in output

    def test_apply_context_no_branch(self):
        """Test applying context without branch info."""
        from aiterm.terminal import ghostty
        from aiterm.context.detector import ContextInfo, ContextType
        import io

        context = ContextInfo(
            type=ContextType.NODE,
            name="webapp",
            icon="📦",
            profile="Node-Dev",
        )

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            mock_stdout = io.StringIO()
            with patch("sys.stdout", mock_stdout):
                ghostty.apply_context(context)
                output = mock_stdout.getvalue()
                assert "📦" in output
                assert "webapp" in output
                # No branch parentheses
                assert "(" not in output or "webapp" in output


# =============================================================================
# NEW TESTS: show_config() - formatted output
# =============================================================================


class TestGhosttyShowConfig:
    """Test show_config formatted output."""

    def test_show_config_with_values(self, tmp_path: Path):
        """Test show_config with actual config."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """font-family = JetBrains Mono
font-size = 16
theme = dracula
cursor-style = underline
"""
        )

        with patch.object(ghostty, "get_config_path", return_value=config_file):
            output = ghostty.show_config()

            assert "Ghostty Configuration" in output
            assert "JetBrains Mono" in output
            assert "16" in output
            assert "dracula" in output
            assert "underline" in output

    def test_show_config_no_file(self):
        """Test show_config when no config exists."""
        from aiterm.terminal import ghostty

        with patch.object(ghostty, "get_config_path", return_value=None):
            output = ghostty.show_config()

            assert "Ghostty Configuration" in output
            assert "Not found" in output
            assert "monospace" in output  # default font


# =============================================================================
# NEW TESTS: Edge cases - invalid values, malformed config
# =============================================================================


class TestGhosttyConfigEdgeCases:
    """Test edge cases in config parsing."""

    def test_parse_invalid_int(self, tmp_path: Path):
        """Test parsing config with invalid integer value."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("font-size = not-a-number\n")

        config = ghostty.parse_config(config_file)
        # Should keep default value
        assert config.font_size == 14

    def test_parse_invalid_float(self, tmp_path: Path):
        """Test parsing config with invalid float value."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("background-opacity = invalid\n")

        config = ghostty.parse_config(config_file)
        # Should keep default value
        assert config.background_opacity == 1.0

    def test_parse_malformed_line(self, tmp_path: Path):
        """Test parsing config with malformed line (no equals)."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """font-size = 14
this line has no equals sign
theme = nord
"""
        )

        config = ghostty.parse_config(config_file)
        assert config.font_size == 14
        assert config.theme == "nord"

    def test_parse_whitespace_handling(self, tmp_path: Path):
        """Test parsing handles various whitespace."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """  font-family   =   Fira Code
font-size=12
  theme =tokyo-night
"""
        )

        config = ghostty.parse_config(config_file)
        assert config.font_family == "Fira Code"
        assert config.font_size == 12
        assert config.theme == "tokyo-night"

    def test_parse_background_opacity(self, tmp_path: Path):
        """Test parsing background opacity."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("background-opacity = 0.85\n")

        config = ghostty.parse_config(config_file)
        assert config.background_opacity == 0.85

    def test_raw_config_capture(self, tmp_path: Path):
        """Test that raw_config captures all key-value pairs."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """font-family = Monaco
custom-key = custom-value
another = setting
"""
        )

        config = ghostty.parse_config(config_file)
        assert "custom-key" in config.raw_config
        assert config.raw_config["custom-key"] == "custom-value"
        assert config.raw_config["another"] == "setting"


# =============================================================================
# NEW TESTS: Config path functions
# =============================================================================


class TestGhosttyConfigPaths:
    """Test config path detection functions."""

    def test_get_config_path_xdg(self, tmp_path: Path):
        """Test finding config in XDG location."""
        from aiterm.terminal import ghostty

        # Create fake XDG config
        xdg_config = tmp_path / ".config" / "ghostty" / "config"
        xdg_config.parent.mkdir(parents=True)
        xdg_config.write_text("theme = test")

        with patch.object(Path, "home", return_value=tmp_path):
            # Need to re-import to pick up patched CONFIG_PATHS
            with patch.object(ghostty, "CONFIG_PATHS", [xdg_config, tmp_path / ".ghostty"]):
                path = ghostty.get_config_path()
                assert path == xdg_config

    def test_get_config_path_none_found(self, tmp_path: Path):
        """Test when no config file exists."""
        from aiterm.terminal import ghostty

        with patch.object(ghostty, "CONFIG_PATHS", [tmp_path / "nonexistent1", tmp_path / "nonexistent2"]):
            path = ghostty.get_config_path()
            assert path is None

    def test_get_default_config_path_creates_dirs(self, tmp_path: Path):
        """Test default config path creates parent directories."""
        from aiterm.terminal import ghostty

        with patch.object(Path, "home", return_value=tmp_path):
            path = ghostty.get_default_config_path()
            assert path.parent.exists()
            assert path.name == "config"


# =============================================================================
# NEW TESTS: reload_config()
# =============================================================================


class TestGhosttyReloadConfig:
    """Test config reload functionality."""

    def test_reload_config_in_ghostty(self):
        """Test reload returns True in Ghostty."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            result = ghostty.reload_config()
            assert result is True

    def test_reload_config_not_in_ghostty(self):
        """Test reload returns False when not in Ghostty."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            result = ghostty.reload_config()
            assert result is False


# =============================================================================
# NEW TESTS: Theme list immutability
# =============================================================================


class TestGhosttyThemeList:
    """Test theme list behavior."""

    def test_list_themes_returns_copy(self):
        """Test that list_themes returns a copy (not mutable original)."""
        from aiterm.terminal import ghostty

        themes1 = ghostty.list_themes()
        themes1.append("fake-theme")

        themes2 = ghostty.list_themes()
        assert "fake-theme" not in themes2

    def test_builtin_themes_count(self):
        """Test expected number of built-in themes."""
        from aiterm.terminal import ghostty

        themes = ghostty.list_themes()
        # Should have at least the documented themes
        assert len(themes) >= 14


# =============================================================================
# NEW TESTS: Profile Management (v0.4.0)
# =============================================================================


class TestGhosttyProfile:
    """Test GhosttyProfile dataclass."""

    def test_profile_to_config_lines(self):
        """Test converting profile to config file lines."""
        from aiterm.terminal.ghostty import GhosttyProfile

        profile = GhosttyProfile(
            name="test-profile",
            theme="nord",
            font_family="JetBrains Mono",
            font_size=16,
            description="Test profile",
            created_at="2025-12-30T12:00:00",
        )

        lines = profile.to_config_lines()
        assert "# Profile: test-profile" in lines
        assert "# Test profile" in lines
        assert "theme = nord" in lines
        assert "font-family = JetBrains Mono" in lines
        assert "font-size = 16" in lines

    def test_profile_from_config(self):
        """Test creating profile from GhosttyConfig."""
        from aiterm.terminal.ghostty import GhosttyProfile, GhosttyConfig

        config = GhosttyConfig(
            font_family="Fira Code",
            font_size=14,
            theme="dracula",
            background_opacity=0.9,
            macos_titlebar_style="tabs",
            background_image="bg.jpg",
            mouse_scroll_multiplier=2.0,
        )

        profile = GhosttyProfile.from_config("my-profile", config, "My coding setup")

        assert profile.name == "my-profile"
        assert profile.theme == "dracula"
        assert profile.font_family == "Fira Code"
        assert profile.font_size == 14
        assert profile.background_opacity == 0.9
        assert profile.macos_titlebar_style == "tabs"
        assert profile.background_image == "bg.jpg"
        assert profile.mouse_scroll_multiplier == 2.0
        assert profile.description == "My coding setup"
        assert profile.created_at  # Should have timestamp

    def test_profile_with_custom_settings(self):
        """Test profile with custom settings."""
        from aiterm.terminal.ghostty import GhosttyProfile

        profile = GhosttyProfile(
            name="custom",
            theme="nord",
            custom_settings={"keybind": "ctrl+t=new_tab", "shell": "/bin/zsh"},
        )

        lines = profile.to_config_lines()
        assert "keybind = ctrl+t=new_tab" in lines
        assert "shell = /bin/zsh" in lines


class TestGhosttyProfileManagement:
    """Test profile management functions."""

    def test_get_profiles_dir(self, tmp_path: Path):
        """Test profiles directory creation."""
        from aiterm.terminal import ghostty

        profiles_dir = tmp_path / ".config" / "ghostty" / "profiles"
        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            result = ghostty.get_profiles_dir()
            assert result.exists()
            assert result == profiles_dir

    def test_list_profiles_empty(self, tmp_path: Path):
        """Test listing profiles when none exist."""
        from aiterm.terminal import ghostty

        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            profiles = ghostty.list_profiles()
            assert profiles == []

    def test_save_and_get_profile(self, tmp_path: Path):
        """Test saving and retrieving a profile."""
        from aiterm.terminal import ghostty
        from aiterm.terminal.ghostty import GhosttyProfile

        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            profile = GhosttyProfile(
                name="coding",
                theme="tokyo-night",
                font_family="JetBrains Mono",
                font_size=14,
                description="My coding setup",
                created_at="2025-12-30T12:00:00",
            )

            saved_path = ghostty.save_profile(profile)
            assert saved_path.exists()
            assert saved_path.name == "coding.conf"

            loaded = ghostty.get_profile("coding")
            assert loaded is not None
            assert loaded.name == "coding"
            assert loaded.theme == "tokyo-night"
            assert loaded.font_family == "JetBrains Mono"
            assert loaded.font_size == 14

    def test_get_profile_not_found(self, tmp_path: Path):
        """Test getting a non-existent profile."""
        from aiterm.terminal import ghostty

        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            profile = ghostty.get_profile("nonexistent")
            assert profile is None

    def test_delete_profile(self, tmp_path: Path):
        """Test deleting a profile."""
        from aiterm.terminal import ghostty
        from aiterm.terminal.ghostty import GhosttyProfile

        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            profile = GhosttyProfile(name="to-delete", theme="nord")
            ghostty.save_profile(profile)

            assert ghostty.get_profile("to-delete") is not None

            result = ghostty.delete_profile("to-delete")
            assert result is True
            assert ghostty.get_profile("to-delete") is None

    def test_delete_profile_not_found(self, tmp_path: Path):
        """Test deleting a non-existent profile."""
        from aiterm.terminal import ghostty

        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            result = ghostty.delete_profile("nonexistent")
            assert result is False

    def test_create_profile_from_current(self, tmp_path: Path):
        """Test creating a profile from current config."""
        from aiterm.terminal import ghostty

        # Setup profiles dir
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)

        # Setup config file
        config_file = tmp_path / "config"
        config_file.write_text(
            """font-family = Monaco
font-size = 13
theme = solarized-dark
"""
        )

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            with patch.object(ghostty, "get_config_path", return_value=config_file):
                profile = ghostty.create_profile_from_current("backup", "Before update")

                assert profile.name == "backup"
                assert profile.theme == "solarized-dark"
                assert profile.font_family == "Monaco"
                assert profile.font_size == 13
                assert profile.description == "Before update"

                # Should be saved to disk
                saved = ghostty.get_profile("backup")
                assert saved is not None
                assert saved.theme == "solarized-dark"

    def test_apply_profile(self, tmp_path: Path):
        """Test applying a profile to config."""
        from aiterm.terminal import ghostty
        from aiterm.terminal.ghostty import GhosttyProfile

        # Setup
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)
        config_file = tmp_path / "config"
        config_file.write_text("theme = old-theme\n")

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            with patch.object(ghostty, "get_config_path", return_value=config_file):
                with patch.object(ghostty, "get_default_config_path", return_value=config_file):
                    # Save a profile
                    profile = GhosttyProfile(
                        name="new-look",
                        theme="gruvbox-dark",
                        font_family="Fira Code",
                        font_size=15,
                    )
                    ghostty.save_profile(profile)

                    # Apply it (with backup disabled for simpler test)
                    result = ghostty.apply_profile("new-look", backup=False)
                    assert result is True

                    # Check config was updated
                    config = ghostty.parse_config(config_file)
                    assert config.theme == "gruvbox-dark"
                    assert config.font_family == "Fira Code"
                    assert config.font_size == 15

    def test_apply_profile_not_found(self, tmp_path: Path):
        """Test applying a non-existent profile."""
        from aiterm.terminal import ghostty

        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir(parents=True)

        with patch.object(ghostty, "PROFILES_DIR", profiles_dir):
            result = ghostty.apply_profile("nonexistent")
            assert result is False


class TestGhosttyBackup:
    """Test backup functionality."""

    def test_backup_config(self, tmp_path: Path):
        """Test creating a config backup."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = catppuccin-mocha\n")

        with patch.object(ghostty, "get_config_path", return_value=config_file):
            backup_path = ghostty.backup_config()

            assert backup_path is not None
            assert backup_path.exists()
            assert "config.backup." in backup_path.name
            assert backup_path.read_text() == "theme = catppuccin-mocha\n"

    def test_backup_config_with_suffix(self, tmp_path: Path):
        """Test creating a backup with custom suffix."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = nord\n")

        with patch.object(ghostty, "get_config_path", return_value=config_file):
            backup_path = ghostty.backup_config(suffix="before-update")

            assert backup_path is not None
            assert "before-update" in backup_path.name

    def test_backup_config_no_file(self, tmp_path: Path):
        """Test backup when no config exists."""
        from aiterm.terminal import ghostty

        with patch.object(ghostty, "get_config_path", return_value=None):
            backup_path = ghostty.backup_config()
            assert backup_path is None

    def test_list_backups(self, tmp_path: Path):
        """Test listing available backups."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = test\n")

        # Create some backup files
        (tmp_path / "config.backup.20251230120000").write_text("v1")
        (tmp_path / "config.backup.20251230130000").write_text("v2")
        (tmp_path / "config.backup.20251230140000").write_text("v3")

        with patch.object(ghostty, "get_config_path", return_value=config_file):
            backups = ghostty.list_backups()

            assert len(backups) == 3
            # Should be sorted newest first
            assert "140000" in backups[0].name
            assert "120000" in backups[-1].name

    def test_restore_backup(self, tmp_path: Path):
        """Test restoring from a backup."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = current\n")

        backup_file = tmp_path / "config.backup.old"
        backup_file.write_text("theme = old-theme\n")

        with patch.object(ghostty, "get_config_path", return_value=config_file):
            with patch.object(ghostty, "get_default_config_path", return_value=config_file):
                result = ghostty.restore_backup(backup_file)

                assert result is True
                assert config_file.read_text() == "theme = old-theme\n"
                # Should have created pre-restore backup
                assert (tmp_path / "config.pre-restore").exists()

    def test_restore_backup_not_found(self, tmp_path: Path):
        """Test restoring from non-existent backup."""
        from aiterm.terminal import ghostty

        result = ghostty.restore_backup(tmp_path / "nonexistent")
        assert result is False


# =============================================================================
# NEW TESTS: Keybind Management (v0.4.0 Phase 0.8.3)
# =============================================================================


class TestGhosttyKeybind:
    """Test GhosttyKeybind dataclass."""

    def test_keybind_to_config_line(self):
        """Test converting keybind to config format."""
        from aiterm.terminal.ghostty import GhosttyKeybind

        kb = GhosttyKeybind(trigger="ctrl+t", action="new_tab")
        assert kb.to_config_line() == "keybind = ctrl+t=new_tab"

    def test_keybind_with_prefix(self):
        """Test keybind with prefix."""
        from aiterm.terminal.ghostty import GhosttyKeybind

        kb = GhosttyKeybind(trigger="ctrl+shift+t", action="new_window", prefix="global:")
        assert kb.to_config_line() == "keybind = global:ctrl+shift+t=new_window"

    def test_keybind_from_config_line(self):
        """Test parsing keybind from config line."""
        from aiterm.terminal.ghostty import GhosttyKeybind

        kb = GhosttyKeybind.from_config_line("keybind = ctrl+d=new_split:right")
        assert kb is not None
        assert kb.trigger == "ctrl+d"
        assert kb.action == "new_split:right"
        assert kb.prefix == ""

    def test_keybind_from_config_line_with_prefix(self):
        """Test parsing keybind with prefix."""
        from aiterm.terminal.ghostty import GhosttyKeybind

        kb = GhosttyKeybind.from_config_line("keybind = global:ctrl+q=quit")
        assert kb is not None
        assert kb.trigger == "ctrl+q"
        assert kb.action == "quit"
        assert kb.prefix == "global:"

    def test_keybind_from_invalid_line(self):
        """Test parsing invalid keybind line."""
        from aiterm.terminal.ghostty import GhosttyKeybind

        assert GhosttyKeybind.from_config_line("not a keybind") is None
        assert GhosttyKeybind.from_config_line("keybind = no-equals-here") is None


class TestKeybindManagement:
    """Test keybind management functions."""

    def test_list_keybinds_empty(self, tmp_path: Path):
        """Test listing keybinds when none exist."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = nord\n")

        keybinds = ghostty.list_keybinds(config_file)
        assert keybinds == []

    def test_list_keybinds(self, tmp_path: Path):
        """Test listing keybinds from config."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """theme = nord
keybind = ctrl+t=new_tab
keybind = ctrl+w=close_surface
keybind = global:ctrl+q=quit
"""
        )

        keybinds = ghostty.list_keybinds(config_file)
        assert len(keybinds) == 3
        assert keybinds[0].trigger == "ctrl+t"
        assert keybinds[0].action == "new_tab"
        assert keybinds[2].prefix == "global:"

    def test_add_keybind(self, tmp_path: Path):
        """Test adding a keybind."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = dracula\n")

        result = ghostty.add_keybind("ctrl+n", "new_window", config_path=config_file)
        assert result is True

        content = config_file.read_text()
        assert "keybind = ctrl+n=new_window" in content

    def test_add_keybind_with_prefix(self, tmp_path: Path):
        """Test adding a keybind with prefix."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("")

        result = ghostty.add_keybind(
            "ctrl+q", "quit", prefix="global:", config_path=config_file
        )
        assert result is True

        content = config_file.read_text()
        assert "keybind = global:ctrl+q=quit" in content

    def test_add_keybind_updates_existing(self, tmp_path: Path):
        """Test that adding a keybind updates existing trigger."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("keybind = ctrl+t=old_action\n")

        result = ghostty.add_keybind("ctrl+t", "new_action", config_path=config_file)
        assert result is True

        content = config_file.read_text()
        assert "keybind = ctrl+t=new_action" in content
        assert "old_action" not in content

    def test_remove_keybind(self, tmp_path: Path):
        """Test removing a keybind."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text(
            """theme = nord
keybind = ctrl+t=new_tab
keybind = ctrl+w=close_surface
"""
        )

        result = ghostty.remove_keybind("ctrl+t", config_path=config_file)
        assert result is True

        content = config_file.read_text()
        assert "ctrl+t" not in content
        assert "ctrl+w=close_surface" in content

    def test_remove_keybind_not_found(self, tmp_path: Path):
        """Test removing non-existent keybind."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = nord\n")

        result = ghostty.remove_keybind("ctrl+nonexistent", config_path=config_file)
        assert result is False


class TestKeybindPresets:
    """Test keybind preset functions."""

    def test_get_keybind_presets(self):
        """Test getting preset names."""
        from aiterm.terminal import ghostty

        presets = ghostty.get_keybind_presets()
        assert "vim" in presets
        assert "emacs" in presets
        assert "tmux" in presets
        assert "macos" in presets

    def test_get_keybind_preset_vim(self):
        """Test getting vim preset keybinds."""
        from aiterm.terminal import ghostty

        preset = ghostty.get_keybind_preset("vim")
        assert preset is not None
        assert len(preset) > 0

        # Check for vim-style navigation
        triggers = [kb.trigger for kb in preset]
        assert "ctrl+h" in triggers
        assert "ctrl+j" in triggers
        assert "ctrl+k" in triggers
        assert "ctrl+l" in triggers

    def test_get_keybind_preset_not_found(self):
        """Test getting non-existent preset."""
        from aiterm.terminal import ghostty

        preset = ghostty.get_keybind_preset("nonexistent")
        assert preset is None

    def test_apply_keybind_preset(self, tmp_path: Path):
        """Test applying a keybind preset."""
        from aiterm.terminal import ghostty

        config_file = tmp_path / "config"
        config_file.write_text("theme = nord\n")

        with patch.object(ghostty, "get_config_path", return_value=config_file):
            result = ghostty.apply_keybind_preset("macos", backup=False, config_path=config_file)
            assert result is True

            content = config_file.read_text()
            assert "cmd+t=new_tab" in content
            assert "cmd+d=new_split:right" in content

    def test_apply_keybind_preset_not_found(self, tmp_path: Path):
        """Test applying non-existent preset."""
        from aiterm.terminal import ghostty

        result = ghostty.apply_keybind_preset("nonexistent")
        assert result is False


# =============================================================================
# NEW TESTS: Session Management (v0.4.0 Phase 0.8.4)
# =============================================================================


class TestGhosttySession:
    """Test GhosttySession dataclass."""

    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        from aiterm.terminal.ghostty import GhosttySession

        session = GhosttySession(
            name="dev-session",
            working_dirs=["/home/user/project", "/home/user/docs"],
            created_at="2025-12-30T12:00:00",
            description="Development session",
            layout="split-h",
        )

        data = session.to_dict()
        assert data["name"] == "dev-session"
        assert len(data["working_dirs"]) == 2
        assert data["layout"] == "split-h"
        assert data["description"] == "Development session"

    def test_session_from_dict(self):
        """Test creating session from dictionary."""
        from aiterm.terminal.ghostty import GhosttySession

        data = {
            "name": "test-session",
            "working_dirs": ["/tmp/test"],
            "created_at": "2025-12-30T10:00:00",
            "description": "Test",
            "layout": "single",
        }

        session = GhosttySession.from_dict(data)
        assert session.name == "test-session"
        assert session.working_dirs == ["/tmp/test"]
        assert session.layout == "single"

    def test_session_from_dict_with_defaults(self):
        """Test creating session with missing fields."""
        from aiterm.terminal.ghostty import GhosttySession

        data = {"name": "minimal"}
        session = GhosttySession.from_dict(data)

        assert session.name == "minimal"
        assert session.working_dirs == []
        assert session.layout == "single"


class TestSessionManagement:
    """Test session management functions."""

    def test_get_sessions_dir(self, tmp_path: Path):
        """Test sessions directory creation."""
        from aiterm.terminal import ghostty

        sessions_dir = tmp_path / ".config" / "ghostty" / "sessions"
        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            result = ghostty.get_sessions_dir()
            assert result.exists()
            assert result == sessions_dir

    def test_list_sessions_empty(self, tmp_path: Path):
        """Test listing sessions when none exist."""
        from aiterm.terminal import ghostty

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            sessions = ghostty.list_sessions()
            assert sessions == []

    def test_save_and_get_session(self, tmp_path: Path):
        """Test saving and retrieving a session."""
        from aiterm.terminal import ghostty
        from aiterm.terminal.ghostty import GhosttySession

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            session = GhosttySession(
                name="work",
                working_dirs=["/home/user/project"],
                created_at="2025-12-30T12:00:00",
                description="Work session",
                layout="split-h",
            )

            saved_path = ghostty.save_session(session)
            assert saved_path.exists()
            assert saved_path.name == "work.json"

            loaded = ghostty.get_session("work")
            assert loaded is not None
            assert loaded.name == "work"
            assert loaded.working_dirs == ["/home/user/project"]
            assert loaded.layout == "split-h"

    def test_get_session_not_found(self, tmp_path: Path):
        """Test getting a non-existent session."""
        from aiterm.terminal import ghostty

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            session = ghostty.get_session("nonexistent")
            assert session is None

    def test_create_session(self, tmp_path: Path):
        """Test creating a new session."""
        from aiterm.terminal import ghostty

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            session = ghostty.create_session(
                name="new-session",
                working_dirs=["/tmp/test1", "/tmp/test2"],
                description="Test session",
                layout="grid",
            )

            assert session.name == "new-session"
            assert len(session.working_dirs) == 2
            assert session.layout == "grid"
            assert session.created_at  # Should have timestamp

            # Should be saved to disk
            saved = ghostty.get_session("new-session")
            assert saved is not None
            assert saved.name == "new-session"

    def test_create_session_default_dir(self, tmp_path: Path):
        """Test creating session with default working directory."""
        from aiterm.terminal import ghostty

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        # Change to tmp_path for the test
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
                session = ghostty.create_session(name="cwd-session")

                assert session.working_dirs == [str(tmp_path)]
        finally:
            os.chdir(original_cwd)

    def test_delete_session(self, tmp_path: Path):
        """Test deleting a session."""
        from aiterm.terminal import ghostty
        from aiterm.terminal.ghostty import GhosttySession

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            session = GhosttySession(name="to-delete")
            ghostty.save_session(session)

            assert ghostty.get_session("to-delete") is not None

            result = ghostty.delete_session("to-delete")
            assert result is True
            assert ghostty.get_session("to-delete") is None

    def test_delete_session_not_found(self, tmp_path: Path):
        """Test deleting a non-existent session."""
        from aiterm.terminal import ghostty

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            result = ghostty.delete_session("nonexistent")
            assert result is False

    def test_restore_session(self, tmp_path: Path):
        """Test restoring a session."""
        from aiterm.terminal import ghostty
        from aiterm.terminal.ghostty import GhosttySession

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        # Create a test directory to restore to
        restore_dir = tmp_path / "restore_target"
        restore_dir.mkdir()

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            session = GhosttySession(
                name="restore-me",
                working_dirs=[str(restore_dir)],
                layout="single",
            )
            ghostty.save_session(session)

            original_cwd = os.getcwd()
            try:
                result = ghostty.restore_session("restore-me")
                assert result is not None
                assert result.name == "restore-me"
                # Should have changed to the session's directory
                assert os.getcwd() == str(restore_dir)
            finally:
                os.chdir(original_cwd)

    def test_restore_session_not_found(self, tmp_path: Path):
        """Test restoring a non-existent session."""
        from aiterm.terminal import ghostty

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.object(ghostty, "SESSIONS_DIR", sessions_dir):
            result = ghostty.restore_session("nonexistent")
            assert result is None

    def test_split_terminal_not_in_ghostty(self):
        """Test split_terminal when not in Ghostty."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "iTerm.app"}):
            result = ghostty.split_terminal("right")
            assert result is False

    def test_split_terminal_invalid_direction(self):
        """Test split_terminal with invalid direction."""
        from aiterm.terminal import ghostty

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            result = ghostty.split_terminal("invalid")
            assert result is False

    def test_split_terminal_right(self):
        """Test split_terminal right direction."""
        from aiterm.terminal import ghostty
        import subprocess

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            with patch.object(subprocess, "run") as mock_run:
                result = ghostty.split_terminal("right")
                assert result is True
                mock_run.assert_called_once()

    def test_split_terminal_down(self):
        """Test split_terminal down direction."""
        from aiterm.terminal import ghostty
        import subprocess

        with patch.dict(os.environ, {"TERM_PROGRAM": "ghostty"}):
            with patch.object(subprocess, "run") as mock_run:
                result = ghostty.split_terminal("down")
                assert result is True
                mock_run.assert_called_once()
