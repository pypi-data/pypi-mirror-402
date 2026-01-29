"""Tests for craft CLI commands."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aiterm.cli.craft import (
    app,
    get_craft_config,
    get_craft_version,
    is_craft_installed,
    get_craft_commands,
    get_craft_skills,
    get_craft_agents,
    PLUGINS_DIR,
    CRAFT_PLUGIN_DIR,
)

runner = CliRunner()


class TestCraftDetection:
    """Test craft plugin detection functions."""

    def test_is_craft_installed_true(self, tmp_path: Path):
        """Test detecting installed craft plugin."""
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            assert is_craft_installed() is True

    def test_is_craft_installed_false(self, tmp_path: Path):
        """Test detecting missing craft plugin."""
        craft_dir = tmp_path / "craft"  # Not created

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            assert is_craft_installed() is False

    def test_get_craft_config(self, tmp_path: Path):
        """Test loading craft config."""
        craft_dir = tmp_path / "craft"
        plugin_dir = craft_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True)

        config = {"name": "craft", "version": "1.0.0"}
        (plugin_dir / "plugin.json").write_text(json.dumps(config))

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = get_craft_config()
            assert result == config

    def test_get_craft_config_fallback(self, tmp_path: Path):
        """Test loading craft config from config.json fallback."""
        craft_dir = tmp_path / "craft"
        plugin_dir = craft_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True)

        config = {"name": "craft", "version": "0.9.0"}
        (plugin_dir / "config.json").write_text(json.dumps(config))

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = get_craft_config()
            assert result == config

    def test_get_craft_config_not_found(self, tmp_path: Path):
        """Test loading craft config when not present."""
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = get_craft_config()
            assert result is None

    def test_get_craft_version(self, tmp_path: Path):
        """Test getting craft version."""
        craft_dir = tmp_path / "craft"
        plugin_dir = craft_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True)

        config = {"version": "1.5.0"}
        (plugin_dir / "plugin.json").write_text(json.dumps(config))

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            assert get_craft_version() == "1.5.0"


class TestCraftComponents:
    """Test craft component listing functions."""

    def test_get_craft_commands(self, tmp_path: Path):
        """Test listing craft commands."""
        craft_dir = tmp_path / "craft"
        commands_dir = craft_dir / "commands"
        commands_dir.mkdir(parents=True)

        # Create some commands
        (commands_dir / "check.md").write_text("# Check")
        (commands_dir / "do.md").write_text("# Do")
        git_dir = commands_dir / "git"
        git_dir.mkdir()
        (git_dir / "worktree.md").write_text("# Worktree")

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            commands = get_craft_commands()
            assert "check" in commands
            assert "do" in commands
            assert "git" in commands

    def test_get_craft_skills(self, tmp_path: Path):
        """Test listing craft skills."""
        craft_dir = tmp_path / "craft"
        skills_dir = craft_dir / "skills"
        skills_dir.mkdir(parents=True)

        (skills_dir / "testing").mkdir()
        (skills_dir / "docs").mkdir()
        (skills_dir / "ci").mkdir()

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            skills = get_craft_skills()
            assert "testing" in skills
            assert "docs" in skills
            assert "ci" in skills

    def test_get_craft_agents(self, tmp_path: Path):
        """Test listing craft agents."""
        craft_dir = tmp_path / "craft"
        agents_dir = craft_dir / "agents"
        agents_dir.mkdir(parents=True)

        (agents_dir / "orchestrator.md").write_text("# Orchestrator")
        (agents_dir / "helper.md").write_text("# Helper")

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            agents = get_craft_agents()
            assert "orchestrator" in agents
            assert "helper" in agents


class TestCraftCLI:
    """Test craft CLI commands."""

    def test_craft_status_not_installed(self, tmp_path: Path):
        """Test status when craft is not installed."""
        craft_dir = tmp_path / "craft"

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 1
            assert "not installed" in result.output

    def test_craft_status_installed(self, tmp_path: Path):
        """Test status when craft is installed."""
        craft_dir = tmp_path / "craft"
        plugin_dir = craft_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True)

        config = {"name": "craft", "version": "1.0.0", "description": "Test plugin"}
        (plugin_dir / "plugin.json").write_text(json.dumps(config))

        # Create minimal structure
        (craft_dir / "commands").mkdir()
        (craft_dir / "skills").mkdir()
        (craft_dir / "agents").mkdir()

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "1.0.0" in result.output

    def test_craft_list_commands(self, tmp_path: Path):
        """Test listing craft commands."""
        craft_dir = tmp_path / "craft"
        commands_dir = craft_dir / "commands"
        commands_dir.mkdir(parents=True)
        skills_dir = craft_dir / "skills"
        skills_dir.mkdir()
        agents_dir = craft_dir / "agents"
        agents_dir.mkdir()

        (commands_dir / "check.md").write_text("# Check command")

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["list", "--commands"])
            assert result.exit_code == 0
            assert "check" in result.output

    def test_craft_list_not_installed(self, tmp_path: Path):
        """Test list when craft is not installed."""
        craft_dir = tmp_path / "craft"

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["list"])
            assert result.exit_code == 1

    def test_craft_install_already_installed(self, tmp_path: Path):
        """Test install when already installed."""
        craft_dir = tmp_path / "plugins" / "craft"
        craft_dir.mkdir(parents=True)

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["install"])
            assert result.exit_code == 0
            assert "already installed" in result.output

    def test_craft_install_source_not_found(self, tmp_path: Path):
        """Test install with missing source."""
        craft_dir = tmp_path / "plugins" / "craft"
        source_dir = tmp_path / "nonexistent"

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            with patch("aiterm.cli.craft.CRAFT_SOURCE_DIR", source_dir):
                result = runner.invoke(app, ["install", "--force"])
                assert result.exit_code == 1
                assert "not found" in result.output

    def test_craft_update_not_installed(self, tmp_path: Path):
        """Test update when not installed."""
        craft_dir = tmp_path / "craft"

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["update"])
            assert result.exit_code == 1
            assert "not installed" in result.output

    def test_craft_sync(self, tmp_path: Path):
        """Test sync command."""
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()
        (craft_dir / "commands").mkdir()
        (craft_dir / "skills").mkdir()

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["sync"])
            assert result.exit_code == 0
            assert "Project Context" in result.output

    def test_craft_run(self, tmp_path: Path):
        """Test run command shows instructions."""
        craft_dir = tmp_path / "craft"
        craft_dir.mkdir()

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["run", "check"])
            assert result.exit_code == 0
            assert "/craft:check" in result.output

    def test_craft_commands_namespace(self, tmp_path: Path):
        """Test commands namespace listing."""
        craft_dir = tmp_path / "craft"
        commands_dir = craft_dir / "commands"
        git_dir = commands_dir / "git"
        git_dir.mkdir(parents=True)

        (git_dir / "worktree.md").write_text("# Git Worktree Management")
        (git_dir / "clean.md").write_text("# Git Clean")

        with patch("aiterm.cli.craft.CRAFT_PLUGIN_DIR", craft_dir):
            result = runner.invoke(app, ["commands", "git"])
            assert result.exit_code == 0
            assert "worktree" in result.output
            assert "clean" in result.output
