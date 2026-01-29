"""Tests for aiterm config module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aiterm.config.paths import (
    get_config_home,
    get_config_file,
    get_profiles_dir,
    get_themes_dir,
    get_cache_dir,
    ensure_config_dir,
)


class TestGetConfigHome:
    """Tests for get_config_home function."""

    def test_default_path(self):
        """Default should be ~/.config/aiterm."""
        # Clear cache to test fresh
        get_config_home.cache_clear()

        with patch.dict(os.environ, {}, clear=True):
            # Remove AITERM_CONFIG_HOME and XDG_CONFIG_HOME
            os.environ.pop("AITERM_CONFIG_HOME", None)
            os.environ.pop("XDG_CONFIG_HOME", None)

            get_config_home.cache_clear()
            result = get_config_home()

            assert result == Path.home() / ".config" / "aiterm"

    def test_aiterm_config_home_override(self, tmp_path):
        """AITERM_CONFIG_HOME should override default."""
        get_config_home.cache_clear()

        custom_path = tmp_path / "custom-aiterm"
        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": str(custom_path)}):
            get_config_home.cache_clear()
            result = get_config_home()

            assert result == custom_path

    def test_xdg_config_home_fallback(self, tmp_path):
        """XDG_CONFIG_HOME should be used if AITERM_CONFIG_HOME not set."""
        get_config_home.cache_clear()

        xdg_path = tmp_path / "xdg-config"
        env = {"XDG_CONFIG_HOME": str(xdg_path)}

        # Remove AITERM_CONFIG_HOME if set
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("AITERM_CONFIG_HOME", None)
            get_config_home.cache_clear()
            result = get_config_home()

            assert result == xdg_path / "aiterm"

    def test_aiterm_takes_precedence_over_xdg(self, tmp_path):
        """AITERM_CONFIG_HOME should take precedence over XDG_CONFIG_HOME."""
        get_config_home.cache_clear()

        aiterm_path = tmp_path / "aiterm-config"
        xdg_path = tmp_path / "xdg-config"

        with patch.dict(os.environ, {
            "AITERM_CONFIG_HOME": str(aiterm_path),
            "XDG_CONFIG_HOME": str(xdg_path),
        }):
            get_config_home.cache_clear()
            result = get_config_home()

            assert result == aiterm_path

    def test_tilde_expansion(self, tmp_path):
        """Path with ~ should be expanded."""
        get_config_home.cache_clear()

        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": "~/custom-aiterm"}):
            get_config_home.cache_clear()
            result = get_config_home()

            assert result == Path.home() / "custom-aiterm"


class TestConfigPaths:
    """Tests for config path functions."""

    def test_get_config_file(self):
        """Config file should be config.toml in config home."""
        get_config_home.cache_clear()
        config_home = get_config_home()
        assert get_config_file() == config_home / "config.toml"

    def test_get_profiles_dir(self):
        """Profiles dir should be profiles/ in config home."""
        get_config_home.cache_clear()
        config_home = get_config_home()
        assert get_profiles_dir() == config_home / "profiles"

    def test_get_themes_dir(self):
        """Themes dir should be themes/ in config home."""
        get_config_home.cache_clear()
        config_home = get_config_home()
        assert get_themes_dir() == config_home / "themes"

    def test_get_cache_dir(self):
        """Cache dir should be cache/ in config home."""
        get_config_home.cache_clear()
        config_home = get_config_home()
        assert get_cache_dir() == config_home / "cache"


class TestEnsureConfigDir:
    """Tests for ensure_config_dir function."""

    def test_creates_directory(self, tmp_path):
        """Should create config directory if it doesn't exist."""
        get_config_home.cache_clear()

        config_path = tmp_path / "new-config"
        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": str(config_path)}):
            get_config_home.cache_clear()

            assert not config_path.exists()
            result = ensure_config_dir()
            assert result == config_path
            assert config_path.exists()
            assert config_path.is_dir()

    def test_existing_directory(self, tmp_path):
        """Should work with existing directory."""
        get_config_home.cache_clear()

        config_path = tmp_path / "existing-config"
        config_path.mkdir()

        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": str(config_path)}):
            get_config_home.cache_clear()
            result = ensure_config_dir()

            assert result == config_path
            assert config_path.exists()


class TestConfigCLI:
    """Tests for config CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def app(self):
        """Import app after fixtures are set up."""
        from aiterm.cli.main import app
        return app

    def test_config_path_basic(self, runner, app):
        """ait config path should show config directory."""
        # Clear cache to get real path (not temp from previous tests)
        get_config_home.cache_clear()

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AITERM_CONFIG_HOME", None)
            get_config_home.cache_clear()
            result = runner.invoke(app, ["config", "path"])

            assert result.exit_code == 0
            assert ".config/aiterm" in result.output or "aiterm" in result.output

    def test_config_path_all(self, runner, app):
        """ait config path --all should show all paths."""
        result = runner.invoke(app, ["config", "path", "--all"])
        assert result.exit_code == 0
        assert "Config Home" in result.output
        assert "Config File" in result.output
        assert "Profiles" in result.output
        assert "Themes" in result.output
        assert "Cache" in result.output

    def test_config_show_no_file(self, runner, app, tmp_path):
        """ait config show should handle missing config file."""
        get_config_home.cache_clear()

        empty_config = tmp_path / "empty-config"
        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": str(empty_config)}):
            get_config_home.cache_clear()
            result = runner.invoke(app, ["config", "show"])

            assert result.exit_code == 0
            assert "No configuration file found" in result.output

    def test_config_init_creates_file(self, runner, app, tmp_path):
        """ait config init should create config file."""
        get_config_home.cache_clear()

        new_config = tmp_path / "new-config"
        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": str(new_config)}):
            get_config_home.cache_clear()
            result = runner.invoke(app, ["config", "init"])

            assert result.exit_code == 0
            assert "Created:" in result.output
            assert (new_config / "config.toml").exists()

    def test_config_init_no_overwrite(self, runner, app, tmp_path):
        """ait config init should not overwrite without --force."""
        get_config_home.cache_clear()

        existing_config = tmp_path / "existing"
        existing_config.mkdir()
        config_file = existing_config / "config.toml"
        config_file.write_text("existing content")

        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": str(existing_config)}):
            get_config_home.cache_clear()
            result = runner.invoke(app, ["config", "init"])

            assert result.exit_code == 0
            assert "already exists" in result.output
            assert config_file.read_text() == "existing content"

    def test_config_init_force_overwrites(self, runner, app, tmp_path):
        """ait config init --force should overwrite existing."""
        get_config_home.cache_clear()

        existing_config = tmp_path / "existing"
        existing_config.mkdir()
        config_file = existing_config / "config.toml"
        config_file.write_text("old content")

        with patch.dict(os.environ, {"AITERM_CONFIG_HOME": str(existing_config)}):
            get_config_home.cache_clear()
            result = runner.invoke(app, ["config", "init", "--force"])

            assert result.exit_code == 0
            assert "Created:" in result.output
            assert "old content" not in config_file.read_text()
            assert "[general]" in config_file.read_text()

    def test_config_help(self, runner, app):
        """ait config --help should show available commands."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "path" in result.output
        assert "show" in result.output
        assert "init" in result.output
        assert "edit" in result.output
