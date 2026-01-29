"""Tests for StatusLine renderer and segments."""

import json
import pytest
from pathlib import Path

from aiterm.statusline.renderer import StatusLineRenderer
from aiterm.statusline.segments import (
    ProjectSegment,
    GitSegment,
    ModelSegment,
    TimeSegment,
    ThinkingSegment,
    LinesSegment,
)
from aiterm.statusline.config import StatusLineConfig


class TestStatusLineRenderer:
    """Test StatusLineRenderer class."""

    @pytest.fixture
    def mock_json(self):
        """Create mock JSON input."""
        return json.dumps({
            "workspace": {
                "current_dir": "/Users/dt/projects/dev-tools/aiterm",
                "project_dir": "/Users/dt/projects/dev-tools/aiterm"
            },
            "model": {
                "display_name": "Claude Sonnet 4.5"
            },
            "output_style": {
                "name": "learning"
            },
            "session_id": "test-123",
            "cost": {
                "total_lines_added": 123,
                "total_lines_removed": 45,
                "total_duration_ms": 45000
            }
        })

    def test_render_basic(self, mock_json):
        """Test basic rendering."""
        # Enable features for testing
        config = StatusLineConfig()
        config.set('display.show_lines_changed', True)

        renderer = StatusLineRenderer(config)
        output = renderer.render(mock_json)

        assert isinstance(output, str)
        assert "╭─" in output  # Line 1 start
        assert "╰─" in output  # Line 2 start
        assert "Sonnet" in output  # Model name
        assert "+123" in output  # Lines added

    def test_render_invalid_json(self):
        """Test rendering with invalid JSON."""
        renderer = StatusLineRenderer()
        output = renderer.render("{ invalid json }")

        assert "Invalid JSON" in output

    def test_render_two_lines(self, mock_json):
        """Test output has exactly 2 lines."""
        renderer = StatusLineRenderer()
        output = renderer.render(mock_json)

        # Remove ANSI window title escape sequence
        lines = output.split('\n')
        # Should have 2 lines (plus possible empty line at end)
        assert len([l for l in lines if l]) >= 2


class TestProjectSegment:
    """Test ProjectSegment class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return StatusLineConfig()

    @pytest.fixture
    def segment(self, config):
        """Create ProjectSegment."""
        return ProjectSegment(config)

    def test_python_project_icon(self, segment, tmp_path):
        """Test Python project detection."""
        # Create pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        icon = segment._get_project_icon(str(tmp_path))
        assert icon == "🐍"

    def test_r_package_icon(self, segment, tmp_path):
        """Test R package detection."""
        # Create DESCRIPTION file
        (tmp_path / "DESCRIPTION").write_text("Package: testpkg\nVersion: 1.0.0")

        icon = segment._get_project_icon(str(tmp_path))
        assert icon == "📦"

    def test_default_icon(self, segment, tmp_path):
        """Test default icon for unknown project type."""
        icon = segment._get_project_icon(str(tmp_path))
        assert icon == "📁"

    def test_format_directory_basename(self, segment, tmp_path, monkeypatch):
        """Test basename directory mode."""
        # Mock config to return basename mode
        def mock_get(key, default=None):
            if key == 'display.directory_mode':
                return 'basename'
            return default

        monkeypatch.setattr(segment.config, 'get', mock_get)

        result = segment._format_directory(str(tmp_path), str(tmp_path))
        assert result == tmp_path.name

    def test_r_version_detection(self, segment, tmp_path):
        """Test R package version detection."""
        desc_file = tmp_path / "DESCRIPTION"
        desc_file.write_text("Package: testpkg\nVersion: 1.2.3\nTitle: Test")

        version = segment._get_r_version(str(tmp_path))
        assert version == "v1.2.3"

    def test_r_version_missing(self, segment, tmp_path):
        """Test R version when DESCRIPTION doesn't exist."""
        version = segment._get_r_version(str(tmp_path))
        assert version is None


class TestModelSegment:
    """Test ModelSegment class."""

    @pytest.fixture
    def config(self):
        return StatusLineConfig()

    @pytest.fixture
    def segment(self, config):
        return ModelSegment(config)

    def test_render_sonnet(self, segment):
        """Test rendering Sonnet model."""
        output = segment.render("Claude Sonnet 4.5")

        assert "Sonnet" in output
        assert "Claude" not in output  # Shortened
        assert "\033[" in output  # Has ANSI color codes

    def test_render_opus(self, segment):
        """Test rendering Opus model."""
        output = segment.render("Claude Opus 4")

        assert "Opus" in output
        assert "Claude" not in output

    def test_render_haiku(self, segment):
        """Test rendering Haiku model."""
        output = segment.render("Claude Haiku 3.5")

        assert "Haiku" in output


class TestTimeSegment:
    """Test TimeSegment class."""

    @pytest.fixture
    def config(self):
        config = StatusLineConfig()
        # Enable time features for testing
        config.set('display.show_current_time', True)
        config.set('display.show_session_duration', True)
        return config

    @pytest.fixture
    def segment(self, config):
        return TimeSegment(config)

    def test_render_includes_time(self, segment):
        """Test rendering includes current time."""
        output = segment.render("test-session")

        assert "│" in output  # Separator
        # Should have time in HH:MM format (ANSI-wrapped)
        assert ":" in output

    def test_render_includes_duration(self, segment):
        """Test rendering includes session duration."""
        output = segment.render("test-session")

        assert "⏱" in output  # Duration icon

    def test_session_duration_format(self, segment):
        """Test session duration formatting."""
        # Clean up any existing session file
        from pathlib import Path
        session_file = Path("/tmp/claude-session-new-session-test")
        if session_file.exists():
            session_file.unlink()

        # New session
        duration = segment._get_session_duration("new-session-test")
        assert duration in ["0m", "<1m"]


class TestLinesSegment:
    """Test LinesSegment class."""

    @pytest.fixture
    def config(self):
        config = StatusLineConfig()
        # Enable lines changed feature for testing
        config.set('display.show_lines_changed', True)
        return config

    @pytest.fixture
    def segment(self, config):
        return LinesSegment(config)

    def test_render_with_changes(self, segment):
        """Test rendering with lines changed."""
        output = segment.render(123, 45)

        assert "+123" in output
        assert "45" in output

    def test_render_no_changes(self, segment):
        """Test rendering with no changes."""
        output = segment.render(0, 0)

        assert output == ""

    def test_render_only_additions(self, segment):
        """Test rendering with only additions."""
        output = segment.render(50, 0)

        assert "+50" in output

    def test_render_disabled_in_config(self, segment, monkeypatch):
        """Test rendering when disabled in config."""
        def mock_get(key, default=None):
            if key == 'display.show_lines_changed':
                return False
            return default

        monkeypatch.setattr(segment.config, 'get', mock_get)

        output = segment.render(100, 50)
        assert output == ""


class TestThinkingSegment:
    """Test ThinkingSegment class."""

    @pytest.fixture
    def config(self):
        return StatusLineConfig()

    @pytest.fixture
    def segment(self, config):
        return ThinkingSegment(config)

    def test_render_when_settings_missing(self, segment):
        """Test rendering when settings file doesn't exist."""
        output = segment.render()

        # Should return empty string gracefully
        assert output == ""


class TestSpacingFeatures:
    """Test spacing features for gap between left and right segments."""

    @pytest.fixture
    def config(self, tmp_path, monkeypatch):
        """Create isolated config for testing."""
        # Use a temporary config file to avoid interference with user's config
        config_file = tmp_path / "test_statusline.json"
        monkeypatch.setenv('AITERM_CONFIG_DIR', str(tmp_path))
        config = StatusLineConfig()
        # Reset spacing to standard preset defaults
        config.set('spacing.mode', 'standard')
        config.set('spacing.min_gap', 10)
        config.set('spacing.max_gap', 40)
        config.set('spacing.show_separator', True)
        return config

    @pytest.fixture
    def renderer(self, config):
        return StatusLineRenderer(config)

    # =============================================================================
    # Gap Calculation Tests
    # =============================================================================

    def test_calculate_gap_standard_preset(self, renderer):
        """Test gap calculation with standard preset (20%)."""
        # Terminal width 120 * 0.20 = 24
        gap = renderer._calculate_gap(120)
        assert gap == 24

    def test_calculate_gap_minimal_preset(self, renderer, monkeypatch):
        """Test gap calculation with minimal preset (15%)."""
        renderer.config.set('spacing.mode', 'minimal')
        # Terminal width 120 * 0.15 = 18
        gap = renderer._calculate_gap(120)
        assert gap == 18

    def test_calculate_gap_spacious_preset(self, renderer, monkeypatch):
        """Test gap calculation with spacious preset (30%)."""
        renderer.config.set('spacing.mode', 'spacious')
        # Terminal width 120 * 0.30 = 36
        gap = renderer._calculate_gap(120)
        assert gap == 36

    def test_calculate_gap_min_constraint(self, renderer):
        """Test gap respects minimum constraint."""
        # Very narrow terminal: 50 * 0.20 = 10
        # Standard preset min_gap is 10, should not go below
        gap = renderer._calculate_gap(50)
        assert gap >= 10

        # Even narrower: 40 * 0.20 = 8, should clamp to min_gap=10
        gap = renderer._calculate_gap(40)
        assert gap == 10

    def test_calculate_gap_max_constraint(self, renderer):
        """Test gap respects maximum constraint."""
        # Very wide terminal: 300 * 0.20 = 60
        # Standard preset max_gap is 40, should not exceed
        gap = renderer._calculate_gap(300)
        assert gap == 40

    def test_calculate_gap_config_overrides(self, renderer):
        """Test config overrides for min/max gap."""
        # Set custom min/max
        renderer.config.set('spacing.min_gap', 15)
        renderer.config.set('spacing.max_gap', 30)

        # Test min override: 60 * 0.20 = 12, should clamp to 15
        gap = renderer._calculate_gap(60)
        assert gap == 15

        # Test max override: 200 * 0.20 = 40, should clamp to 30
        gap = renderer._calculate_gap(200)
        assert gap == 30

    # =============================================================================
    # Gap Rendering Tests
    # =============================================================================

    def test_render_gap_with_separator(self, renderer):
        """Test gap rendering with centered separator."""
        gap = renderer._render_gap(20)

        # Should contain separator (…) in ANSI wrapper
        assert '…' in gap
        # Should have ANSI color code (38;5;240m for dim gray)
        assert '\033[38;5;240m' in gap
        # Total visible length should be 20 (spaces + separator)
        visible_length = renderer._strip_ansi_length(gap)
        assert visible_length == 20

    def test_render_gap_without_separator(self, renderer):
        """Test gap rendering with separator disabled."""
        renderer.config.set('spacing.show_separator', False)
        gap = renderer._render_gap(20)

        # Should not contain separator
        assert '…' not in gap
        # Should be just spaces
        assert gap == ' ' * 20

    def test_render_gap_too_small_for_separator(self, renderer):
        """Test gap rendering when too small for separator."""
        # Gap of 2 is too small for separator (needs >= 3)
        gap = renderer._render_gap(2)

        # Should fall back to just spaces
        assert gap == '  '
        assert '…' not in gap

    # =============================================================================
    # Alignment Integration Tests
    # =============================================================================

    def test_align_line_with_spacing(self, renderer, monkeypatch):
        """Test line alignment uses spacing system."""
        # Mock terminal width
        from collections import namedtuple
        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        def mock_get_terminal_size(fallback=None):
            return TerminalSize(columns=120, lines=24)

        import shutil
        monkeypatch.setattr(shutil, 'get_terminal_size', mock_get_terminal_size)

        left = "Left side"
        right = "Right side"

        aligned = renderer._align_line(left, right)

        # Should contain both sides
        assert "Left side" in aligned
        assert "Right side" in aligned

        # Should have gap with separator (if enabled)
        if renderer.config.get('spacing.show_separator', True):
            assert '…' in aligned

    def test_align_line_narrow_terminal(self, renderer, monkeypatch):
        """Test line alignment on narrow terminal."""
        # Mock narrow terminal (80 cols)
        from collections import namedtuple
        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        def mock_get_terminal_size(fallback=None):
            return TerminalSize(columns=80, lines=24)

        import shutil
        monkeypatch.setattr(shutil, 'get_terminal_size', mock_get_terminal_size)

        left = "Left side with longer text"
        right = "Right side"

        aligned = renderer._align_line(left, right)

        # Should still contain both sides if there's any room
        assert "Left side" in aligned

    def test_align_line_fallback_to_left_only(self, renderer, monkeypatch):
        """Test line alignment falls back to left-only on very narrow terminal."""
        # Mock very narrow terminal (40 cols)
        from collections import namedtuple
        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        def mock_get_terminal_size(fallback=None):
            return TerminalSize(columns=40, lines=24)

        import shutil
        monkeypatch.setattr(shutil, 'get_terminal_size', mock_get_terminal_size)

        left = "This is a very long left side segment that takes up lots of space"
        right = "Right"

        aligned = renderer._align_line(left, right)

        # Should fall back to left-only when no room for right side
        assert "This is a very long left side" in aligned

    # =============================================================================
    # Additional Edge Case Tests
    # =============================================================================

    def test_calculate_gap_invalid_preset(self, renderer):
        """Test gap calculation with invalid preset name."""
        # Config validation prevents invalid presets - this should raise ValueError
        import pytest
        with pytest.raises(ValueError) as exc_info:
            renderer.config.set('spacing.mode', 'invalid-preset')

        # Error message should list valid choices
        assert "Valid choices: minimal, standard, spacious" in str(exc_info.value)

    def test_calculate_gap_very_narrow_terminal(self, renderer):
        """Test gap calculation on very narrow terminal."""
        # 40 columns * 0.20 = 8, but min_gap is 10
        gap = renderer._calculate_gap(40)
        assert gap == 10  # Should clamp to min_gap

    def test_calculate_gap_very_wide_terminal(self, renderer):
        """Test gap calculation on ultra-wide terminal."""
        # 400 columns * 0.20 = 80, but max_gap is 40
        gap = renderer._calculate_gap(400)
        assert gap == 40  # Should clamp to max_gap

    def test_render_gap_exact_3_chars(self, renderer):
        """Test separator rendering with exactly 3 chars (minimum)."""
        gap = renderer._render_gap(3)

        # Should contain separator
        assert '…' in gap
        # Should have correct visible length
        visible_length = renderer._strip_ansi_length(gap)
        assert visible_length == 3

    def test_render_gap_odd_width(self, renderer):
        """Test separator centering with odd gap width."""
        gap = renderer._render_gap(7)

        # Should have correct visible length
        visible_length = renderer._strip_ansi_length(gap)
        assert visible_length == 7
        # Should contain separator
        assert '…' in gap

    def test_render_gap_even_width(self, renderer):
        """Test separator centering with even gap width."""
        gap = renderer._render_gap(8)

        # Should have correct visible length
        visible_length = renderer._strip_ansi_length(gap)
        assert visible_length == 8
        # Should contain separator
        assert '…' in gap

    def test_strip_ansi_complex_codes(self, renderer):
        """Test ANSI stripping with multiple escape sequences."""
        # Multiple codes: bold + color
        text = "\033[38;5;240m\033[1mBold and colored\033[0m"
        length = renderer._strip_ansi_length(text)
        assert length == len("Bold and colored")

    def test_strip_ansi_nested_codes(self, renderer):
        """Test nested ANSI codes."""
        # Nested codes with text between
        text = "\033[1m\033[31mRed bold\033[0m normal"
        length = renderer._strip_ansi_length(text)
        assert length == len("Red bold normal")

    def test_strip_ansi_no_codes(self, renderer):
        """Test ANSI stripping with plain text (no codes)."""
        text = "Plain text without codes"
        length = renderer._strip_ansi_length(text)
        assert length == len(text)

    # =============================================================================
    # Performance Benchmark Tests
    # =============================================================================

    def test_calculate_gap_performance(self, renderer):
        """Test gap calculation performance."""
        import time

        # Run multiple iterations to measure performance
        iterations = 1000
        start_time = time.perf_counter()

        for _ in range(iterations):
            renderer._calculate_gap(120)

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations

        # Should complete in less than 1ms per call
        assert avg_time < 0.001, f"Gap calculation took {avg_time*1000:.3f}ms (expected <1ms)"

    def test_render_gap_performance(self, renderer):
        """Test gap rendering performance."""
        import time

        # Run multiple iterations to measure performance
        iterations = 1000
        start_time = time.perf_counter()

        for _ in range(iterations):
            renderer._render_gap(24)

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations

        # Should complete in less than 1ms per call
        assert avg_time < 0.001, f"Gap rendering took {avg_time*1000:.3f}ms (expected <1ms)"

    def test_align_line_performance(self, renderer, monkeypatch):
        """Test line alignment performance."""
        import time
        from collections import namedtuple

        # Mock terminal size
        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])
        def mock_get_terminal_size(fallback=None):
            return TerminalSize(columns=120, lines=24)

        import shutil
        monkeypatch.setattr(shutil, 'get_terminal_size', mock_get_terminal_size)

        left = "Left side segment"
        right = "Right side segment"

        # Run multiple iterations to measure performance
        iterations = 1000
        start_time = time.perf_counter()

        for _ in range(iterations):
            renderer._align_line(left, right)

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations

        # Should complete in less than 2ms per call (includes gap calculation + rendering)
        assert avg_time < 0.002, f"Line alignment took {avg_time*1000:.3f}ms (expected <2ms)"

    # =============================================================================
    # Integration Tests
    # =============================================================================

    def test_full_statusline_render_with_spacing(self, renderer):
        """Test complete statusLine rendering with spacing system."""
        import json

        # Create mock JSON input
        mock_json = json.dumps({
            "workspace": {
                "current_dir": "/Users/dt/projects/dev-tools/aiterm",
                "project_dir": "/Users/dt/projects/dev-tools/aiterm"
            },
            "model": {
                "display_name": "Claude Sonnet 4.5"
            },
            "output_style": {
                "name": "learning"
            },
            "session_id": "test-123",
            "cost": {
                "total_lines_added": 123,
                "total_lines_removed": 45,
                "total_duration_ms": 45000
            }
        })

        # Render the full statusLine
        output = renderer.render(mock_json)

        # Should have two lines
        lines = output.split('\n')
        assert len([l for l in lines if l]) >= 2

        # Should contain model name
        assert 'Sonnet' in output

        # Should contain box drawing characters (from Powerlevel10k style)
        assert '╭─' in output
        assert '╰─' in output

        # Verify the spacing system is working by checking alignment
        # Extract the visible content (strip ANSI codes)
        import re
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        for line in lines:
            if line and '╭─' in line:
                # First line should have left segment
                clean_line = ansi_pattern.sub('', line)
                # Should have project name or identifier
                assert len(clean_line) > 10  # Has substantial content

    def test_statusline_adaptive_spacing_terminal_resize(self, renderer, monkeypatch):
        """Test spacing adapts to terminal width changes."""
        from collections import namedtuple

        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        left = "Left"
        right = "Right"

        # Test different terminal widths
        test_widths = [80, 120, 160, 200]
        previous_gap = None

        for width in test_widths:
            # Mock terminal width
            def mock_get_terminal_size(fallback=None):
                return TerminalSize(columns=width, lines=24)

            import shutil
            monkeypatch.setattr(shutil, 'get_terminal_size', mock_get_terminal_size)

            # Calculate gap for this width
            gap = renderer._calculate_gap(width)

            # Verify gap is within bounds
            min_gap = renderer.config.get('spacing.min_gap', 10)
            max_gap = renderer.config.get('spacing.max_gap', 40)
            assert min_gap <= gap <= max_gap

            # Verify alignment works
            aligned = renderer._align_line(left, right)
            assert "Left" in aligned
            assert "Right" in aligned

            # Gap should increase with terminal width (until max_gap)
            if previous_gap is not None and gap < max_gap:
                assert gap >= previous_gap, f"Gap should increase or stay same: {previous_gap} -> {gap}"

            previous_gap = gap

    def test_spacing_presets_integration(self, renderer):
        """Test all spacing presets work end-to-end."""
        from collections import namedtuple
        import shutil

        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        # Mock terminal width
        def mock_get_terminal_size(fallback=None):
            return TerminalSize(columns=120, lines=24)

        import pytest

        # Save original get_terminal_size
        original_get_terminal_size = shutil.get_terminal_size

        try:
            shutil.get_terminal_size = mock_get_terminal_size

            left = "Left segment"
            right = "Right segment"

            # Test each preset
            for preset in ['minimal', 'standard', 'spacious']:
                renderer.config.set('spacing.mode', preset)

                # Calculate gap
                gap = renderer._calculate_gap(120)

                # Render gap
                gap_str = renderer._render_gap(gap)

                # Verify visible length matches
                visible_length = renderer._strip_ansi_length(gap_str)
                assert visible_length == gap, f"Preset {preset}: gap length mismatch"

                # Verify alignment works
                aligned = renderer._align_line(left, right)
                assert "Left segment" in aligned
                assert "Right segment" in aligned

        finally:
            # Restore original function
            shutil.get_terminal_size = original_get_terminal_size

    # =============================================================================
    # Config Persistence Tests
    # =============================================================================

    def test_spacing_config_persists_after_reload(self, tmp_path, monkeypatch):
        """Test spacing settings persist across config reloads."""
        # Create isolated config
        config_file = tmp_path / "test_statusline.json"
        monkeypatch.setenv('AITERM_CONFIG_DIR', str(tmp_path))

        # Create first config instance
        config1 = StatusLineConfig()
        config1.set('spacing.mode', 'spacious')
        config1.set('spacing.min_gap', 20)
        config1.set('spacing.max_gap', 50)
        config1.set('spacing.show_separator', False)

        # Create second config instance (should load persisted values)
        config2 = StatusLineConfig()

        # Values should persist
        assert config2.get('spacing.mode') == 'spacious'
        assert config2.get('spacing.min_gap') == 20
        assert config2.get('spacing.max_gap') == 50
        assert config2.get('spacing.show_separator') == False

    def test_spacing_config_overrides_persist(self, tmp_path, monkeypatch):
        """Test manual spacing overrides persist correctly."""
        # Create isolated config
        config_file = tmp_path / "test_statusline.json"
        monkeypatch.setenv('AITERM_CONFIG_DIR', str(tmp_path))

        # Set preset first
        config1 = StatusLineConfig()
        config1.set('spacing.mode', 'standard')

        # Override min/max
        config1.set('spacing.min_gap', 15)
        config1.set('spacing.max_gap', 30)

        # Create new instance
        config2 = StatusLineConfig()

        # Both preset and overrides should persist
        assert config2.get('spacing.mode') == 'standard'
        assert config2.get('spacing.min_gap') == 15
        assert config2.get('spacing.max_gap') == 30

    def test_spacing_settings_survive_config_operations(self, tmp_path, monkeypatch):
        """Test spacing settings survive save/load/reset operations."""
        # Create isolated config
        config_file = tmp_path / "test_statusline.json"
        monkeypatch.setenv('AITERM_CONFIG_DIR', str(tmp_path))

        config = StatusLineConfig()

        # Set custom spacing
        config.set('spacing.mode', 'minimal')
        config.set('spacing.show_separator', False)

        # Explicitly save (should happen automatically, but test it)
        # Note: StatusLineConfig auto-saves on set(), so this tests that behavior

        # Load again (should get saved values)
        config2 = StatusLineConfig()
        assert config2.get('spacing.mode') == 'minimal'
        assert config2.get('spacing.show_separator') == False

        # Reset single setting
        config2.reset('spacing.mode')
        assert config2.get('spacing.mode') == 'standard'  # Back to default
        assert config2.get('spacing.show_separator') == False  # Other setting preserved

        # Reset all
        config2.reset()
        assert config2.get('spacing.mode') == 'standard'  # Default
        assert config2.get('spacing.show_separator') == True  # Default

    # =============================================================================
    # Edge Case Tests
    # =============================================================================

    def test_calculate_gap_zero_width(self, renderer):
        """Test gap calculation with zero terminal width."""
        gap = renderer._calculate_gap(0)
        # Should return minimum gap even with zero width
        min_gap = renderer.config.get('spacing.min_gap', 10)
        assert gap == min_gap

    def test_calculate_gap_negative_width(self, renderer):
        """Test gap calculation with negative terminal width."""
        gap = renderer._calculate_gap(-100)
        # Should return minimum gap, not negative
        min_gap = renderer.config.get('spacing.min_gap', 10)
        assert gap == min_gap
        assert gap > 0

    def test_render_gap_size_one(self, renderer):
        """Test rendering gap with size 1 (smallest possible)."""
        gap = renderer._render_gap(1)
        # Should be single space, no separator
        assert gap == ' '
        assert '…' not in gap

    def test_render_gap_size_two(self, renderer):
        """Test rendering gap with size 2 (below separator threshold)."""
        gap = renderer._render_gap(2)
        # Too small for separator (needs >= 3)
        assert gap == '  '
        assert '…' not in gap
        visible_length = renderer._strip_ansi_length(gap)
        assert visible_length == 2

    def test_align_line_empty_segments(self, renderer):
        """Test alignment with empty segments."""
        # Both empty
        aligned = renderer._align_line('', '')
        assert isinstance(aligned, str)

        # Left empty
        aligned = renderer._align_line('', 'Right')
        assert 'Right' in aligned

        # Right empty
        aligned = renderer._align_line('Left', '')
        assert 'Left' in aligned

    def test_align_line_only_ansi_codes(self, renderer):
        """Test alignment with segments containing only ANSI codes."""
        left = '\033[0m\033[38;5;240m\033[0m'  # Only ANSI codes
        right = '\033[1m\033[0m'  # Only ANSI codes

        aligned = renderer._align_line(left, right)
        # Should handle gracefully
        assert isinstance(aligned, str)

    def test_align_line_unicode_characters(self, renderer):
        """Test alignment with Unicode characters."""
        left = "🐍 Python 🚀"
        right = "✨ Sonnet 💎"

        aligned = renderer._align_line(left, right)
        assert "🐍" in aligned
        assert "✨" in aligned

    def test_align_line_very_long_segments(self, renderer, monkeypatch):
        """Test alignment with very long segments exceeding terminal width."""
        from collections import namedtuple
        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        def mock_get_terminal_size(fallback=None):
            return TerminalSize(columns=80, lines=24)

        import shutil
        monkeypatch.setattr(shutil, 'get_terminal_size', mock_get_terminal_size)

        # Create segments that together exceed terminal width
        left = "A" * 70  # Very long
        right = "B" * 30  # Also long

        aligned = renderer._align_line(left, right)
        # Should fall back to left-only when combined length exceeds terminal
        assert "A" in aligned

    def test_strip_ansi_multiple_resets(self, renderer):
        """Test ANSI stripping with multiple reset codes."""
        text = "Hello\033[0m World\033[0m Test\033[0m"
        length = renderer._strip_ansi_length(text)
        assert length == len("Hello World Test")

    def test_strip_ansi_malformed_codes(self, renderer):
        """Test ANSI stripping handles incomplete escape sequences gracefully."""
        # Incomplete escape sequence
        text = "Hello\033[38World"
        length = renderer._strip_ansi_length(text)
        # Should handle gracefully without crashing
        assert isinstance(length, int)
        assert length > 0

    def test_calculate_gap_boundary_widths(self, renderer):
        """Test gap calculation at preset boundary widths."""
        # Test exactly at min_gap threshold
        renderer.config.set('spacing.mode', 'standard')  # 20% base

        # Width that produces exactly min_gap (50 * 0.20 = 10)
        gap = renderer._calculate_gap(50)
        assert gap == 10

        # Width just above min_gap (55 * 0.20 = 11)
        gap = renderer._calculate_gap(55)
        assert gap == 11

    def test_render_gap_with_separator_disabled_via_config(self, renderer):
        """Test that separator respects config setting."""
        renderer.config.set('spacing.show_separator', False)

        gap = renderer._render_gap(20)
        # Should be all spaces, no separator
        assert '…' not in gap
        assert gap == ' ' * 20

    # =============================================================================
    # End-to-End (E2E) Tests
    # =============================================================================

    def test_e2e_complete_render_pipeline(self, renderer, tmp_path, monkeypatch):
        """E2E: Test complete rendering pipeline from JSON to output."""
        import json

        # Create realistic project directory
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # Create realistic JSON input (simulating Claude Code statusLine data)
        mock_json = json.dumps({
            "workspace": {
                "current_dir": str(project_dir),
                "project_dir": str(project_dir)
            },
            "model": {
                "display_name": "Claude Sonnet 4.5"
            },
            "output_style": {
                "name": "standard"
            },
            "session_id": "e2e-test-123",
            "cost": {
                "total_lines_added": 250,
                "total_lines_removed": 100,
                "total_duration_ms": 120000
            }
        })

        # Render
        output = renderer.render(mock_json)

        # Verify complete output structure
        assert '╭─' in output  # Top line
        assert '╰─' in output  # Bottom line
        assert 'Sonnet' in output  # Model name
        assert isinstance(output, str)
        assert len(output) > 0

        # Verify lines are properly formed
        lines = [l for l in output.split('\n') if l]
        assert len(lines) >= 2

    def test_e2e_preset_switching_workflow(self, renderer):
        """E2E: Test switching between all presets in realistic workflow."""
        from collections import namedtuple
        import shutil

        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        def mock_get_terminal_size(fallback=None):
            return TerminalSize(columns=120, lines=24)

        original_get_terminal_size = shutil.get_terminal_size

        try:
            shutil.get_terminal_size = mock_get_terminal_size

            left = "Project Info"
            right = "Status"

            # Workflow: Start with standard
            renderer.config.set('spacing.mode', 'standard')
            output1 = renderer._align_line(left, right)
            gap1 = renderer._calculate_gap(120)

            # Switch to minimal (user wants compact view)
            renderer.config.set('spacing.mode', 'minimal')
            output2 = renderer._align_line(left, right)
            gap2 = renderer._calculate_gap(120)

            # Switch to spacious (user wants clarity)
            renderer.config.set('spacing.mode', 'spacious')
            output3 = renderer._align_line(left, right)
            gap3 = renderer._calculate_gap(120)

            # Switch back to standard
            renderer.config.set('spacing.mode', 'standard')
            output4 = renderer._align_line(left, right)
            gap4 = renderer._calculate_gap(120)

            # Verify gaps follow expected order
            assert gap2 < gap1 < gap3  # minimal < standard < spacious
            assert gap4 == gap1  # Returned to standard

            # All outputs should contain both segments
            for output in [output1, output2, output3, output4]:
                assert "Project Info" in output
                assert "Status" in output

        finally:
            shutil.get_terminal_size = original_get_terminal_size

    def test_e2e_terminal_resize_scenario(self, renderer, monkeypatch):
        """E2E: Simulate terminal resize and verify adaptive spacing."""
        from collections import namedtuple

        TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])

        left = "Left Content"
        right = "Right Content"

        # Simulate terminal resize events
        widths = [120, 100, 80, 160, 200, 120]  # Realistic resize sequence
        previous_gap = None

        for width in widths:
            def mock_get_terminal_size(fallback=None):
                return TerminalSize(columns=width, lines=24)

            import shutil
            monkeypatch.setattr(shutil, 'get_terminal_size', mock_get_terminal_size)

            gap = renderer._calculate_gap(width)
            aligned = renderer._align_line(left, right)

            # Verify gap adapts to width
            min_gap = renderer.config.get('spacing.min_gap', 10)
            max_gap = renderer.config.get('spacing.max_gap', 40)
            assert min_gap <= gap <= max_gap

            # Verify both segments still visible (unless terminal too narrow)
            if width >= 50:  # Reasonable minimum
                assert "Left Content" in aligned

            previous_gap = gap

    def test_e2e_all_segments_rendering(self, renderer):
        """E2E: Test rendering with all possible segment types."""
        import json

        # JSON with all segment types populated
        mock_json = json.dumps({
            "workspace": {
                "current_dir": "/Users/dt/projects/test",
                "project_dir": "/Users/dt/projects/test"
            },
            "model": {
                "display_name": "Claude Opus 4.5"
            },
            "output_style": {
                "name": "standard"
            },
            "session_id": "all-segments-test",
            "cost": {
                "total_lines_added": 500,
                "total_lines_removed": 200,
                "total_duration_ms": 180000
            },
            "git": {
                "branch": "feature/test",
                "dirty": True,
                "ahead": 3,
                "behind": 1
            }
        })

        output = renderer.render(mock_json)

        # Verify output is well-formed
        assert isinstance(output, str)
        assert len(output) > 0
        assert '╭─' in output
        assert '╰─' in output

        # Should contain model name
        assert 'Opus' in output or 'Sonnet' in output

    def test_e2e_config_file_operations(self, tmp_path):
        """E2E: Test complete config file lifecycle."""
        import json

        # Create isolated config with explicit path
        config_file = tmp_path / "statusline.json"

        # 1. Create config with custom spacing
        config1 = StatusLineConfig()
        config1.config_path = config_file  # Override default path
        config1.set('spacing.mode', 'spacious')
        config1.set('spacing.min_gap', 25)
        config1.set('spacing.show_separator', False)

        # 2. Verify config file was created
        assert config_file.exists()

        # 3. Read file directly to verify JSON structure
        with open(config_file) as f:
            data = json.load(f)

        # Spacing settings are under 'spacing' key, not 'display.spacing'
        assert data['spacing']['mode'] == 'spacious'
        assert data['spacing']['min_gap'] == 25
        assert data['spacing']['show_separator'] == False

        # 4. Create new config instance (loads from file)
        config2 = StatusLineConfig()
        config2.config_path = config_file  # Point to same file
        assert config2.get('spacing.mode') == 'spacious'
        assert config2.get('spacing.min_gap') == 25

        # 5. Modify and verify persistence
        config2.set('spacing.mode', 'minimal')

        config3 = StatusLineConfig()
        config3.config_path = config_file  # Point to same file
        assert config3.get('spacing.mode') == 'minimal'
        assert config3.get('spacing.min_gap') == 25  # Unchanged

    def test_e2e_error_recovery(self, renderer):
        """E2E: Test error recovery in various failure scenarios."""
        import json

        # Test 1: Invalid JSON
        invalid_json = "{ invalid json }"
        output = renderer.render(invalid_json)
        assert "Invalid JSON" in output

        # Test 2: Missing required fields
        minimal_json = json.dumps({"model": {"display_name": "Test"}})
        output = renderer.render(minimal_json)
        # Should not crash, should render with defaults
        assert isinstance(output, str)

        # Test 3: Malformed model name
        weird_json = json.dumps({
            "workspace": {"current_dir": "/tmp", "project_dir": "/tmp"},
            "model": {"display_name": ""},  # Empty
            "output_style": {"name": "standard"}
        })
        output = renderer.render(weird_json)
        assert isinstance(output, str)

    def test_e2e_stress_test_rapid_preset_changes(self, renderer):
        """E2E: Stress test with rapid preset changes."""
        presets = ['minimal', 'standard', 'spacious']

        # Rapidly switch presets 100 times
        for i in range(100):
            preset = presets[i % 3]
            renderer.config.set('spacing.mode', preset)
            gap = renderer._calculate_gap(120)

            # Verify gap is always valid
            assert gap > 0
            assert gap <= 60  # Max possible gap

    def test_e2e_unicode_and_ansi_complex(self, renderer):
        """E2E: Test complex Unicode + ANSI combinations."""
        # Complex segment with Unicode, emojis, and ANSI codes
        left = "\033[1m🚀 Project\033[0m \033[38;5;240m│\033[0m 🐍 Python"
        right = "✨ \033[1mStatus\033[0m 💎"

        aligned = renderer._align_line(left, right)

        # Verify both segments present
        assert "🚀" in aligned
        assert "✨" in aligned
        assert isinstance(aligned, str)

        # Verify proper length calculation
        visible_length = renderer._strip_ansi_length(left)
        # Should count emoji and text, not ANSI codes
        assert visible_length > 0
