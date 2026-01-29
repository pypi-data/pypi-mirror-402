"""Tests for statusLine worktree features (Phase 1 + Phase 2).

Tests cover:
- Smart branch truncation
- Worktree name detection
- Right-side segment rendering
- Adaptive worktree display
- ANSI code stripping for alignment
"""

import pytest
from aiterm.statusline.segments import GitSegment
from aiterm.statusline.renderer import StatusLineRenderer
from aiterm.statusline.config import StatusLineConfig


class TestBranchTruncation:
    """Test smart branch truncation (keep start/end)."""

    def test_short_branch_no_truncation(self):
        """Short branch names are not truncated."""
        config = StatusLineConfig()
        git_segment = GitSegment(config)

        branch = "main"
        result = git_segment._truncate_branch(branch, 32)

        assert result == "main"
        assert len(result) <= 32

    def test_long_branch_truncation(self):
        """Long branch names are truncated with start/end preserved."""
        config = StatusLineConfig()
        git_segment = GitSegment(config)

        branch = "feature/authentication-system-oauth2-integration"
        result = git_segment._truncate_branch(branch, 32)

        # Should have ellipsis in middle
        assert "..." in result
        # Should preserve start
        assert result.startswith("feature/")
        # Should preserve end
        assert result.endswith("integration")
        # Should be within length limit
        assert len(result) <= 32

    def test_exact_length_branch(self):
        """Branch exactly at max length is not truncated."""
        config = StatusLineConfig()
        git_segment = GitSegment(config)

        branch = "a" * 32
        result = git_segment._truncate_branch(branch, 32)

        assert result == branch
        assert "..." not in result

    def test_very_short_max_length(self):
        """Very short max_len falls back to simple ellipsis."""
        config = StatusLineConfig()
        git_segment = GitSegment(config)

        branch = "feature/long-branch-name"
        result = git_segment._truncate_branch(branch, 10)

        assert "..." in result
        assert len(result) <= 10

    def test_truncation_preserves_context(self):
        """Truncated branch still has meaningful prefix/suffix."""
        config = StatusLineConfig()
        git_segment = GitSegment(config)

        branch = "feature/add-user-authentication-with-oauth"
        result = git_segment._truncate_branch(branch, 32)

        # Should see both "feature/" and "oauth"
        assert result.startswith("feature/")
        assert "oauth" in result
        assert "..." in result


class TestWorktreeDetection:
    """Test worktree name detection."""

    def test_get_worktree_name_returns_none_for_main(self, tmp_path):
        """Main working directory returns None."""
        config = StatusLineConfig()
        git_segment = GitSegment(config)

        # For non-git dir, should return None
        result = git_segment._get_worktree_name(str(tmp_path))
        assert result is None

    def test_is_worktree_false_for_main(self, tmp_path):
        """Main working directory is not a worktree."""
        config = StatusLineConfig()
        git_segment = GitSegment(config)

        result = git_segment._is_worktree(str(tmp_path))
        assert result is False


class TestRightSideRendering:
    """Test right-side segment rendering."""

    def test_render_right_segment_basic(self):
        """Right segment renders with P10k style."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        content = "(wt) feature-auth"
        result = renderer._render_right_segment(content)

        # Should contain content
        assert "(wt) feature-auth" in result
        # Should have powerline arrows
        assert "░▒▓" in result
        assert "▓▒░" in result
        # Should have ANSI color codes
        assert "\033[" in result

    def test_render_right_segment_worktree_count(self):
        """Right segment renders worktree count."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        content = "🌳 3 worktrees"
        result = renderer._render_right_segment(content)

        assert "🌳 3 worktrees" in result
        assert "░▒▓" in result

    def test_build_right_segments_disabled(self, tmp_path):
        """Right segments disabled when config is off."""
        config = StatusLineConfig()
        config.set('git.show_worktrees', False)
        renderer = StatusLineRenderer(config)

        from aiterm.statusline.segments import GitSegment
        git_segment = GitSegment(config)

        result = renderer._build_right_segments(str(tmp_path), git_segment)
        assert result == ""


class TestANSIStripping:
    """Test ANSI code stripping for alignment."""

    def test_strip_ansi_length_plain_text(self):
        """Plain text length is unchanged."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        text = "Hello World"
        length = renderer._strip_ansi_length(text)

        assert length == len(text)
        assert length == 11

    def test_strip_ansi_length_with_colors(self):
        """ANSI color codes are stripped."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        text = "\033[38;5;245mHello\033[0m World"
        length = renderer._strip_ansi_length(text)

        # Only "Hello World" (11 chars) should count
        assert length == 11

    def test_strip_ansi_length_complex(self):
        """Complex ANSI codes are handled."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        text = "\033[48;5;235m\033[38;5;245m░▒▓ (wt) test ▓▒░\033[0m"
        length = renderer._strip_ansi_length(text)

        # Only visible chars: "░▒▓ (wt) test ▓▒░"
        visible_text = "░▒▓ (wt) test ▓▒░"
        assert length == len(visible_text)

    def test_strip_ansi_empty_string(self):
        """Empty string has zero length."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        assert renderer._strip_ansi_length("") == 0

    def test_strip_ansi_only_codes(self):
        """String with only ANSI codes has zero visible length."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        text = "\033[0m\033[38;5;245m\033[0m"
        length = renderer._strip_ansi_length(text)

        assert length == 0


class TestLineAlignment:
    """Test line alignment with padding."""

    def test_align_line_sufficient_space(self):
        """Line aligns correctly when there's space."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        left = "╭─ Left"
        right = "Right ▓▒░"

        result = renderer._align_line(left, right)

        # Should have padding between left and right
        assert result.startswith("╭─ Left")
        assert result.endswith("Right ▓▒░")
        assert " " in result  # Has spacing

    def test_align_line_insufficient_space(self):
        """Line falls back to left-only when too narrow."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        # Very long left side
        left = "╭─ " + "x" * 200
        right = "Right"

        result = renderer._align_line(left, right)

        # Should fallback to just left side
        assert result == left
        assert "Right" not in result

    def test_align_line_with_ansi_codes(self):
        """Alignment works correctly with ANSI codes."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        left = "\033[38;5;245m╭─ Left\033[0m"
        right = "\033[38;5;245mRight\033[0m"

        result = renderer._align_line(left, right)

        # Should calculate padding based on visible chars
        # "╭─ Left" = 7 chars, "Right" = 5 chars
        # Terminal width 120, so padding = 120 - 7 - 5 = 108
        assert left in result
        assert right in result


class TestAdaptiveDisplay:
    """Test adaptive worktree display (main vs worktree)."""

    def test_build_right_segments_main_no_worktrees(self, tmp_path):
        """Main branch with no worktrees shows nothing."""
        config = StatusLineConfig()
        renderer = StatusLineRenderer(config)

        from aiterm.statusline.segments import GitSegment
        git_segment = GitSegment(config)

        result = renderer._build_right_segments(str(tmp_path), git_segment)

        # No worktrees = no right side
        assert result == ""

    def test_preset_minimal_disables_bloat(self):
        """Minimal preset correctly disables bloat features."""
        config = StatusLineConfig()

        # Apply minimal preset settings
        config.set('display.show_session_duration', False)
        config.set('display.show_current_time', False)
        config.set('display.show_lines_changed', False)

        # Verify settings
        assert config.get('display.show_session_duration') is False
        assert config.get('display.show_current_time') is False
        assert config.get('display.show_lines_changed') is False

    def test_worktree_config_exists(self):
        """Worktree display config option exists."""
        config = StatusLineConfig()

        # Config should have git.show_worktrees setting
        value = config.get('git.show_worktrees')
        assert value is not None
        assert isinstance(value, bool)


class TestConfigPreset:
    """Test config preset command."""

    def test_minimal_preset_settings(self):
        """Minimal preset defines correct settings."""
        expected_disabled = [
            'display.show_session_duration',
            'display.show_current_time',
            'display.show_lines_changed',
            'display.show_session_usage',
            'display.show_weekly_usage',
            'usage.show_reset_timer',
        ]

        config = StatusLineConfig()

        # Apply minimal settings
        for key in expected_disabled:
            config.set(key, False)

        # Verify all are False
        for key in expected_disabled:
            assert config.get(key) is False, f"{key} should be False in minimal preset"


# Integration test
class TestStatusLineIntegration:
    """Integration tests for complete statusLine rendering."""

    def test_render_with_worktree_disabled(self, tmp_path):
        """StatusLine renders correctly with worktrees disabled."""
        import json

        config = StatusLineConfig()
        config.set('git.show_worktrees', False)
        renderer = StatusLineRenderer(config)

        mock_data = {
            "workspace": {
                "current_dir": str(tmp_path),
                "project_dir": str(tmp_path)
            },
            "model": {
                "display_name": "Claude Sonnet 4.5"
            },
            "output_style": {"name": "default"},
            "session_id": "test",
            "cost": {"total_lines_added": 0, "total_lines_removed": 0}
        }

        result = renderer.render(json.dumps(mock_data))

        # Should have 2 lines
        lines = result.split('\n')
        assert len(lines) == 2

        # Line 1 should not have (wt) marker
        assert "(wt)" not in lines[0]

    def test_minimal_config_hides_bloat(self, tmp_path):
        """Minimal config successfully hides bloat metrics."""
        import json

        config = StatusLineConfig()
        config.set('display.show_session_duration', False)
        config.set('display.show_current_time', False)
        config.set('display.show_lines_changed', False)

        renderer = StatusLineRenderer(config)

        mock_data = {
            "workspace": {
                "current_dir": str(tmp_path),
                "project_dir": str(tmp_path)
            },
            "model": {"display_name": "Claude Sonnet 4.5"},
            "output_style": {"name": "default"},
            "session_id": "test",
            "cost": {
                "total_lines_added": 123,
                "total_lines_removed": 45,
                "total_duration_ms": 45000
            }
        }

        result = renderer.render(json.dumps(mock_data))

        # Should not contain lines changed (+123/-45)
        assert "+123" not in result
        assert "-45" not in result

        # Should still have model name
        assert "Sonnet" in result
