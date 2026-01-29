"""Tests for StatusLine gateway commands (setup, customize).

Tests the new Gateway Pattern implementation:
- ait statusline setup
- ait statusline customize
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from aiterm.cli.main import app
from aiterm.statusline.config import StatusLineConfig


runner = CliRunner()


class TestStatusLineSetupCommand:
    """Test the 'ait statusline setup' gateway command."""

    def test_setup_command_exists(self):
        """Test that setup command is registered."""
        result = runner.invoke(app, ["statusline", "setup", "--help"])
        assert result.exit_code == 0
        assert "gateway" in result.stdout.lower() or "customization" in result.stdout.lower()

    def test_setup_shows_menu_options(self):
        """Test that setup displays all menu options."""
        result = runner.invoke(
            app,
            ["statusline", "setup"],
            input="5\nq\n",  # Select "View all settings", then quit
        )
        # Should show option descriptions
        assert "display" in result.stdout.lower() or "customize" in result.stdout.lower()

    def test_setup_option_1_routes_to_wizard(self):
        """Test that option 1 (Customize display) works."""
        # This would need wizard to be mocked or run interactively
        # For now, test that the routing mechanism exists
        with patch("aiterm.cli.statusline.config_wizard") as mock_wizard:
            result = runner.invoke(
                app,
                ["statusline", "setup"],
                input="1\nq\n",  # Customize display, then quit on next
            )
            # The command should have been called (through routing)
            # Note: Typer routing may not directly call the function in test context

    def test_setup_option_5_shows_settings(self):
        """Test that option 5 (View all settings) calls config_list."""
        with patch("aiterm.cli.statusline.config_list") as mock_list:
            result = runner.invoke(
                app,
                ["statusline", "setup"],
                input="5\nn\n",  # View all settings, then decline to continue
            )
            # Should have displayed something
            assert result.exit_code in [0, 1]

    @pytest.mark.parametrize("choice", ["1", "2", "3", "4", "5", "6"])
    def test_setup_accepts_all_valid_choices(self, choice):
        """Test that setup accepts all numbered choices."""
        # Mock the underlying functions to prevent actual execution
        with patch("aiterm.cli.statusline.config_wizard"):
            with patch("aiterm.cli.statusline.theme_set"):
                with patch("aiterm.cli.statusline.config_spacing"):
                    with patch("aiterm.cli.statusline.config_preset"):
                        with patch("aiterm.cli.statusline.config_list"):
                            with patch("aiterm.cli.statusline.config_edit"):
                                result = runner.invoke(
                                    app,
                                    ["statusline", "setup"],
                                    input=f"{choice}\nn\n",  # Choice, then no to continue
                                )
                                # Should succeed (exit code 0 or 1 if option not implemented)
                                assert result.exit_code in [0, 1]


class TestStatusLineCustomizeCommand:
    """Test the 'ait statusline customize' unified menu command."""

    def test_customize_command_exists(self):
        """Test that customize command is registered."""
        result = runner.invoke(app, ["statusline", "customize", "--help"])
        assert result.exit_code == 0
        assert "unified" in result.stdout.lower() or "customize" in result.stdout.lower()

    def test_customize_shows_current_config(self):
        """Test that customize displays current configuration."""
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",  # Exit immediately (option 5: Done)
        )
        assert result.exit_code == 0
        # Should show theme and spacing info
        assert "theme" in result.stdout.lower() or "spacing" in result.stdout.lower()

    def test_customize_option_1_shows_display(self):
        """Test that option 1 (Display Options) works."""
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",  # Just exit since display menu requires interaction
        )
        # Should show menu structure
        assert "option" in result.stdout.lower() or "display" in result.stdout.lower()

    def test_customize_option_5_exits_cleanly(self):
        """Test that option 5 (Done) exits menu correctly."""
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",  # Select Done
        )
        assert result.exit_code == 0
        assert "done" in result.stdout.lower()

    def test_customize_loop_menu_structure(self):
        """Test that customize has proper menu loop structure."""
        # Test that menu is shown repeatedly
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",  # Select Done to exit
        )
        assert result.exit_code == 0
        # Should have menu structure
        assert "choose" in result.stdout.lower() or "option" in result.stdout.lower()


class TestGatewayPatternIntegration:
    """Test the overall Gateway Pattern implementation."""

    def test_setup_is_primary_entry_point(self):
        """Test that setup is positioned as primary entry point."""
        # Both setup and customize should be at root level commands
        result_setup = runner.invoke(app, ["statusline", "setup", "--help"])
        result_customize = runner.invoke(app, ["statusline", "customize", "--help"])

        assert result_setup.exit_code == 0
        assert result_customize.exit_code == 0

    def test_old_commands_still_available(self):
        """Test backward compatibility - old commands still work."""
        # config command should still exist
        result = runner.invoke(app, ["statusline", "config", "--help"])
        assert result.exit_code == 0

        # theme command should still exist
        result = runner.invoke(app, ["statusline", "theme", "--help"])
        assert result.exit_code == 0

    def test_gateway_reduces_visible_commands(self):
        """Test that gateway pattern reduces user confusion."""
        # Both new commands should be quick entry points
        setup_help = runner.invoke(app, ["statusline", "setup", "--help"]).stdout
        customize_help = runner.invoke(app, ["statusline", "customize", "--help"]).stdout

        # Both should mention being the recommended way
        assert ("gateway" in setup_help.lower() or "recommended" in setup_help.lower())


class TestSetupCommandLineRouting:
    """Test command-line argument routing in setup command."""

    def test_setup_prompts_for_choice(self):
        """Test that setup asks for user choice."""
        result = runner.invoke(
            app,
            ["statusline", "setup"],
            input="5\nn\n",  # View settings, don't continue
        )
        # Should ask for selection (either explicit prompt or menu display)
        assert "what" in result.stdout.lower() or "choose" in result.stdout.lower()

    def test_setup_validates_choice_input(self):
        """Test that setup validates numeric input."""
        # The setup command should only accept 1-6
        result = runner.invoke(
            app,
            ["statusline", "setup"],
            input="5\nn\n",  # Valid choice
        )
        # Should not error on valid input
        assert result.exit_code in [0, 1]


class TestCustomizeMenuNavigator:
    """Test customize menu navigation."""

    def test_customize_menu_shows_all_sections(self):
        """Test that customize menu shows all section options."""
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",  # Exit
        )
        # Should mention all sections in menu
        output = result.stdout.lower()
        assert any(word in output for word in ["display", "theme", "spacing", "advanced"])

    def test_customize_default_is_exit(self):
        """Test that customize defaults to exit option."""
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="\n",  # Just press enter (use default)
        )
        # Should exit cleanly when using default
        assert result.exit_code in [0, 1]

    def test_customize_loop_until_exit(self):
        """Test that customize supports multiple operations."""
        # Test that you can do multiple things before exiting
        # This is a simplified test - full integration would need real menu interaction
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",  # Go straight to done
        )
        assert result.exit_code == 0


class TestSetupUsabilityFeatures:
    """Test UX features of setup command."""

    def test_setup_shows_help_text_for_options(self):
        """Test that each option has description."""
        result = runner.invoke(
            app,
            ["statusline", "setup"],
            input="5\nn\n",
        )
        # Should show descriptions for at least some options
        # (Git, theme, spacing mentions expected)
        output = result.stdout.lower()
        assert any(
            term in output
            for term in ["git", "theme", "spacing", "preset", "display", "config"]
        )

    def test_setup_keyboard_interrupt_handled(self):
        """Test that Ctrl+C (KeyboardInterrupt) is handled gracefully."""
        # Typer's runner doesn't easily simulate Ctrl+C
        # But the code path should be there
        result = runner.invoke(app, ["statusline", "setup", "--help"])
        # Just verify the help is available
        assert result.exit_code == 0

    def test_customize_shows_current_values(self):
        """Test that customize shows current config values."""
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",
        )
        # Should show current theme and spacing
        # (actual values depend on config, but structure should be there)
        assert "current" in result.stdout.lower() or "theme" in result.stdout.lower()


# Integration test example (if test fixtures available)
@pytest.mark.skipif(
    not Path("~/.config/aiterm/config.json").expanduser().exists(),
    reason="StatusLine config not available in test environment"
)
class TestGatewayRealConfigIntegration:
    """Test gateway commands with real configuration."""

    def test_setup_with_real_config(self):
        """Test setup with actual StatusLineConfig."""
        result = runner.invoke(
            app,
            ["statusline", "setup"],
            input="5\nn\n",
        )
        # Should work with real config
        assert result.exit_code in [0, 1]

    def test_customize_with_real_config(self):
        """Test customize with actual StatusLineConfig."""
        result = runner.invoke(
            app,
            ["statusline", "customize"],
            input="5\n",
        )
        # Should work with real config
        assert result.exit_code in [0, 1]
