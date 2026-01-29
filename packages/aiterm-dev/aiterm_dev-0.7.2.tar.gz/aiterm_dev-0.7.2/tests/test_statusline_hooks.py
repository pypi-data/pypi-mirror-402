"""Tests for StatusLine Hook Templates system.

Tests the hook template management:
- Template listing and validation
- Hook installation and removal
- Hook enable/disable control
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import tempfile

from aiterm.statusline.hooks import StatusLineHooks


class TestStatusLineHooksTemplates:
    """Test hook template definitions."""

    def test_hooks_have_all_templates(self):
        """Test that all expected templates are defined."""
        expected_templates = [
            "on-theme-change",
            "on-remote-session",
            "on-error",
        ]
        templates = StatusLineHooks.list_templates()
        for expected in expected_templates:
            assert expected in templates

    def test_template_structure(self):
        """Test that each template has required fields."""
        required_fields = ["name", "description", "hook_type", "content", "enabled"]

        for template_name in StatusLineHooks.list_templates():
            template = StatusLineHooks.get_template(template_name)
            assert template is not None

            for field in required_fields:
                assert field in template, f"Template {template_name} missing {field}"

    def test_on_theme_change_template(self):
        """Test on-theme-change template specifics."""
        template = StatusLineHooks.get_template("on-theme-change")

        assert template["hook_type"] == "PostToolUse"
        assert "theme" in template["description"].lower()
        assert template["enabled"] is True
        assert "#!/bin/bash" in template["content"]

    def test_on_remote_session_template(self):
        """Test on-remote-session template specifics."""
        template = StatusLineHooks.get_template("on-remote-session")

        assert template["hook_type"] == "PreToolUse"
        assert "remote" in template["description"].lower()
        assert template["enabled"] is True
        assert "teleport" in template["content"].lower()

    def test_on_error_template(self):
        """Test on-error template specifics."""
        template = StatusLineHooks.get_template("on-error")

        assert template["hook_type"] == "PostToolUse"
        # Description should mention alerts or rendering
        assert any(
            word in template["description"].lower()
            for word in ["alert", "fails", "error", "rendering"]
        )
        assert template["enabled"] is False  # Disabled by default
        assert "statusLine" in template["content"]

    def test_unknown_template_returns_none(self):
        """Test that unknown template returns None."""
        template = StatusLineHooks.get_template("nonexistent-template")
        assert template is None


class TestHookTemplateValidation:
    """Test hook template validation."""

    def test_validate_all_built_in_templates(self):
        """Test that all built-in templates pass validation."""
        for template_name in StatusLineHooks.list_templates():
            valid, error = StatusLineHooks.validate_template(template_name)
            assert valid, f"Template {template_name} failed validation: {error}"

    def test_validate_rejects_missing_template(self):
        """Test validation fails for unknown template."""
        valid, error = StatusLineHooks.validate_template("nonexistent")
        assert not valid
        assert "not found" in error.lower()

    def test_validate_requires_all_fields(self):
        """Test validation checks required fields."""
        # This would need mocking to inject invalid templates
        # For now, test with the built-in templates
        for template_name in StatusLineHooks.list_templates():
            valid, error = StatusLineHooks.validate_template(template_name)
            assert valid

    def test_validate_hook_type(self):
        """Test validation of hook types."""
        for template_name in StatusLineHooks.list_templates():
            template = StatusLineHooks.get_template(template_name)
            hook_type = template["hook_type"]
            assert hook_type in ["PreToolUse", "PostToolUse", "Stop"]


class TestHookInstallation:
    """Test hook installation functionality."""

    def test_install_creates_hook_file(self):
        """Test that install creates hook file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                success, message = StatusLineHooks.install_template("on-theme-change")

                assert success
                hook_file = hooks_dir / "statusline-on-theme-change.sh"
                assert hook_file.exists()

    def test_install_makes_hook_executable(self):
        """Test that installed hook is executable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                StatusLineHooks.install_template("on-theme-change")

                hook_file = hooks_dir / "statusline-on-theme-change.sh"
                assert hook_file.stat().st_mode & 0o111  # Check execute bit

    def test_install_registers_hook(self):
        """Test that install registers hook in index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            hooks_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                success, message = StatusLineHooks.install_template("on-theme-change", enable=True)
                assert success

                # Check if index was created
                index_file = hooks_dir / "index.json"
                assert index_file.exists()

                index_data = json.loads(index_file.read_text())
                assert "on-theme-change" in index_data

    def test_install_preserves_content(self):
        """Test that installed hook contains template content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                StatusLineHooks.install_template("on-theme-change")

                hook_file = hooks_dir / "statusline-on-theme-change.sh"
                content = hook_file.read_text()

                # Should contain bash shebang and comments
                assert "#!/bin/bash" in content
                assert "StatusLine" in content or "statusLine" in content

    def test_install_validates_before_installing(self):
        """Test that install validates template before installing."""
        success, message = StatusLineHooks.install_template("nonexistent-template")

        assert not success
        assert "not found" in message.lower()

    def test_install_multiple_hooks(self):
        """Test installing multiple different hooks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                for template_name in ["on-theme-change", "on-remote-session"]:
                    success, message = StatusLineHooks.install_template(template_name)
                    assert success

                # Check both files exist
                assert (hooks_dir / "statusline-on-theme-change.sh").exists()
                assert (hooks_dir / "statusline-on-remote-session.sh").exists()


class TestHookRemoval:
    """Test hook removal functionality."""

    def test_uninstall_removes_hook_file(self):
        """Test that uninstall removes hook file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                # Install first
                StatusLineHooks.install_template("on-theme-change")
                hook_file = hooks_dir / "statusline-on-theme-change.sh"
                assert hook_file.exists()

                # Then uninstall
                success, message = StatusLineHooks.uninstall_template("on-theme-change")
                assert success
                assert not hook_file.exists()

    def test_uninstall_nonexistent_fails(self):
        """Test that uninstalling nonexistent hook fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                success, message = StatusLineHooks.uninstall_template("nonexistent")
                assert not success


class TestHookEnableDisable:
    """Test hook enable/disable functionality."""

    def test_enable_hook(self):
        """Test enabling a hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            hooks_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                # Install first
                StatusLineHooks.install_template("on-error", enable=False)

                # Then enable
                success, message = StatusLineHooks.enable_hook("on-error")
                assert success

    def test_disable_hook(self):
        """Test disabling a hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            hooks_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                # Install first (enabled)
                StatusLineHooks.install_template("on-theme-change", enable=True)

                # Then disable
                success, message = StatusLineHooks.disable_hook("on-theme-change")
                assert success

    def test_enable_nonexistent_fails(self):
        """Test that enabling nonexistent hook fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                success, message = StatusLineHooks.enable_hook("nonexistent")
                assert not success


class TestHookListing:
    """Test hook listing functionality."""

    def test_list_templates(self):
        """Test listing available templates."""
        templates = StatusLineHooks.list_templates()

        assert len(templates) >= 3
        assert "on-theme-change" in templates
        assert "on-remote-session" in templates
        assert "on-error" in templates

    def test_list_installed_empty(self):
        """Test listing when no hooks installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                installed = StatusLineHooks.list_installed()
                # No index.json created yet, so should be empty
                assert len(installed) == 0

    def test_list_installed_after_install(self):
        """Test listing installed hooks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            hooks_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                # Install a hook
                StatusLineHooks.install_template("on-theme-change")

                # List installed
                installed = StatusLineHooks.list_installed()
                assert len(installed) > 0
                assert any(h["name"] == "on-theme-change" for h in installed)


class TestHookIndexManagement:
    """Test hook index file management."""

    def test_index_file_created(self):
        """Test that index file is created during installation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                StatusLineHooks.install_template("on-theme-change")

                index_file = hooks_dir / "index.json"
                assert index_file.exists()

    def test_index_format(self):
        """Test that index file has correct JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            hooks_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(StatusLineHooks, "HOOKS_DIR", hooks_dir):
                StatusLineHooks.install_template("on-theme-change")

                index_file = hooks_dir / "index.json"
                index_data = json.loads(index_file.read_text())

                # Should be dict with hook names as keys
                assert isinstance(index_data, dict)
                hook_entry = index_data.get("on-theme-change")
                assert hook_entry is not None
                assert "path" in hook_entry
                assert "enabled" in hook_entry
                assert "type" in hook_entry


class TestHookContentQuality:
    """Test the quality and correctness of hook scripts."""

    def test_hook_scripts_are_bash(self):
        """Test that all hook scripts are valid bash."""
        for template_name in StatusLineHooks.list_templates():
            template = StatusLineHooks.get_template(template_name)
            content = template["content"]

            # Should start with bash shebang
            assert content.startswith("#!/bin/bash")

    def test_hook_scripts_have_comments(self):
        """Test that hook scripts have documentation comments."""
        for template_name in StatusLineHooks.list_templates():
            template = StatusLineHooks.get_template(template_name)
            content = template["content"]

            # Should have at least one comment line
            assert "#" in content

    def test_hook_scripts_not_empty(self):
        """Test that hook scripts have substantial content."""
        for template_name in StatusLineHooks.list_templates():
            template = StatusLineHooks.get_template(template_name)
            content = template["content"]

            # Should have meaningful content (not just shebang)
            lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
            assert len(lines) > 0


class TestHookPriorityAndOrdering:
    """Test hook priority and execution ordering."""

    def test_hooks_have_priority(self):
        """Test that hooks have priority values."""
        for template_name in StatusLineHooks.list_templates():
            template = StatusLineHooks.get_template(template_name)
            assert "priority" in template
            assert isinstance(template["priority"], int)
            assert 0 <= template["priority"] <= 100

    def test_hook_priority_ordering(self):
        """Test that hook priorities are reasonable."""
        templates = StatusLineHooks.TEMPLATES

        # on-remote-session should have higher priority than on-error
        # (more important to detect remote immediately)
        remote_priority = templates["on-remote-session"].get("priority", 0)
        error_priority = templates["on-error"].get("priority", 0)

        assert remote_priority >= error_priority
