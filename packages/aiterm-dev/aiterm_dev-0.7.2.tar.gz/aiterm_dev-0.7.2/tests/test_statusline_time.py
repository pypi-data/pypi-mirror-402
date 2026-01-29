"""Tests for StatusLine time tracking enhancements.

Tests enhanced time tracking features including:
- Productivity indicators (activity tracking)
- Time-of-day context icons
- Transcript parsing
- Integration with TimeSegment
"""

import json
import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from aiterm.statusline.segments import TimeSegment
from aiterm.statusline.config import StatusLineConfig


class TestProductivityIndicator:
    """Test productivity/activity tracking."""

    @pytest.fixture
    def segment(self):
        config = StatusLineConfig()
        config.set('time.show_productivity_indicator', True)
        return TimeSegment(config)

    def test_no_transcript(self, segment):
        """Should return None when no transcript."""
        result = segment._get_productivity_indicator(None)
        assert result is None

    def test_transcript_not_found(self, segment):
        """Should return None for missing transcript."""
        result = segment._get_productivity_indicator("/nonexistent/path/to/transcript.json")
        assert result is None

    def test_active_session(self, segment, tmp_path):
        """Should return 🟢 for active session (<5min idle)."""
        # Create mock transcript
        transcript = tmp_path / "transcript.json"
        now = int(time.time())
        transcript.write_text(json.dumps({
            "messages": [
                {"timestamp": now - 60}  # 1 minute ago
            ]
        }))

        result = segment._get_productivity_indicator(str(transcript))
        assert result == "🟢"

    def test_idle_session(self, segment, tmp_path):
        """Should return 🟡 for idle session (5-15min)."""
        transcript = tmp_path / "transcript.json"
        now = int(time.time())
        transcript.write_text(json.dumps({
            "messages": [
                {"timestamp": now - 600}  # 10 minutes ago
            ]
        }))

        result = segment._get_productivity_indicator(str(transcript))
        assert result == "🟡"

    def test_long_idle_session(self, segment, tmp_path):
        """Should return 🔴 for long idle session (>15min)."""
        transcript = tmp_path / "transcript.json"
        now = int(time.time())
        transcript.write_text(json.dumps({
            "messages": [
                {"timestamp": now - 1200}  # 20 minutes ago
            ]
        }))

        result = segment._get_productivity_indicator(str(transcript))
        assert result == "🔴"

    def test_boundary_active_idle(self, segment, tmp_path):
        """Should handle boundary between active and idle (5min)."""
        transcript = tmp_path / "transcript.json"
        now = int(time.time())
        transcript.write_text(json.dumps({
            "messages": [
                {"timestamp": now - 299}  # 4m 59s ago (still active)
            ]
        }))

        result = segment._get_productivity_indicator(str(transcript))
        assert result == "🟢"

    def test_boundary_idle_long(self, segment, tmp_path):
        """Should handle boundary between idle and long idle (15min)."""
        transcript = tmp_path / "transcript.json"
        now = int(time.time())
        transcript.write_text(json.dumps({
            "messages": [
                {"timestamp": now - 899}  # 14m 59s ago (still idle)
            ]
        }))

        result = segment._get_productivity_indicator(str(transcript))
        assert result == "🟡"

    def test_empty_messages(self, segment, tmp_path):
        """Should return None for empty message list."""
        transcript = tmp_path / "transcript.json"
        transcript.write_text(json.dumps({"messages": []}))

        result = segment._get_productivity_indicator(str(transcript))
        assert result is None

    def test_invalid_json(self, segment, tmp_path):
        """Should return None for invalid JSON."""
        transcript = tmp_path / "transcript.json"
        transcript.write_text("not valid json{")

        result = segment._get_productivity_indicator(str(transcript))
        assert result is None

    def test_missing_timestamp(self, segment, tmp_path):
        """Should return None when message has no timestamp."""
        transcript = tmp_path / "transcript.json"
        transcript.write_text(json.dumps({
            "messages": [
                {"content": "Hello"}  # No timestamp
            ]
        }))

        result = segment._get_productivity_indicator(str(transcript))
        assert result is None

    def test_disabled_by_config(self, tmp_path):
        """Should return None when config disabled."""
        config = StatusLineConfig()
        config.set('time.show_productivity_indicator', False)
        segment = TimeSegment(config)

        result = segment._get_productivity_indicator("/any/path")
        assert result is None


class TestTimeOfDayIndicator:
    """Test time-of-day context icons."""

    @pytest.fixture
    def segment(self):
        config = StatusLineConfig()
        config.set('time.show_time_of_day', True)
        return TimeSegment(config)

    def test_morning_icon(self, segment):
        """Should return 🌅 for morning hours (6-11am)."""
        with patch('time.strftime', return_value="09"):
            result = segment._get_time_of_day_indicator()
            assert result == "🌅"

    def test_afternoon_icon(self, segment):
        """Should return ☀️ for afternoon hours (12-5pm)."""
        with patch('time.strftime', return_value="14"):
            result = segment._get_time_of_day_indicator()
            assert result == "☀️"

    def test_evening_icon(self, segment):
        """Should return 🌙 for evening hours (6-11pm)."""
        with patch('time.strftime', return_value="20"):
            result = segment._get_time_of_day_indicator()
            assert result == "🌙"

    def test_night_icon(self, segment):
        """Should return 🌃 for night hours (12-5am)."""
        with patch('time.strftime', return_value="02"):
            result = segment._get_time_of_day_indicator()
            assert result == "🌃"

    def test_boundary_morning_start(self, segment):
        """Should handle morning boundary (6am exactly)."""
        with patch('time.strftime', return_value="06"):
            result = segment._get_time_of_day_indicator()
            assert result == "🌅"

    def test_boundary_afternoon_start(self, segment):
        """Should handle afternoon boundary (12pm exactly)."""
        with patch('time.strftime', return_value="12"):
            result = segment._get_time_of_day_indicator()
            assert result == "☀️"

    def test_boundary_evening_start(self, segment):
        """Should handle evening boundary (6pm exactly)."""
        with patch('time.strftime', return_value="18"):
            result = segment._get_time_of_day_indicator()
            assert result == "🌙"

    def test_boundary_night_start(self, segment):
        """Should handle night boundary (12am exactly)."""
        with patch('time.strftime', return_value="00"):
            result = segment._get_time_of_day_indicator()
            assert result == "🌃"

    def test_disabled_by_config(self):
        """Should return None when config disabled."""
        config = StatusLineConfig()
        config.set('time.show_time_of_day', False)
        segment = TimeSegment(config)

        result = segment._get_time_of_day_indicator()
        assert result is None


class TestTimeSegmentIntegration:
    """Test complete TimeSegment with enhancements."""

    def test_render_with_time_of_day(self):
        """Should include time-of-day icon in output."""
        config = StatusLineConfig()
        config.set('time.show_time_of_day', True)
        config.set('display.show_current_time', True)
        segment = TimeSegment(config)

        with patch('time.strftime') as mock_time:
            # First call for time display, second for hour check
            mock_time.side_effect = ["10:30", "10"]
            output = segment.render("test-session")
            assert "🌅" in output

    def test_render_with_productivity(self, tmp_path):
        """Should include productivity indicator in output."""
        config = StatusLineConfig()
        config.set('time.show_productivity_indicator', True)
        config.set('display.show_session_duration', True)
        segment = TimeSegment(config)

        # Create active transcript
        transcript = tmp_path / "transcript.json"
        now = int(time.time())
        transcript.write_text(json.dumps({
            "messages": [{"timestamp": now - 60}]
        }))

        output = segment.render("test-session", str(transcript))
        assert "🟢" in output

    def test_render_with_both_indicators(self, tmp_path):
        """Should include both time-of-day and productivity."""
        config = StatusLineConfig()
        config.set('time.show_time_of_day', True)
        config.set('time.show_productivity_indicator', True)
        config.set('display.show_current_time', True)
        config.set('display.show_session_duration', True)
        segment = TimeSegment(config)

        transcript = tmp_path / "transcript.json"
        now = int(time.time())
        transcript.write_text(json.dumps({
            "messages": [{"timestamp": now - 60}]
        }))

        with patch('time.strftime') as mock_time:
            mock_time.side_effect = ["14:30", "14"]  # Afternoon
            output = segment.render("test-session", str(transcript))
            assert "☀️" in output
            assert "🟢" in output

    def test_render_without_enhancements(self):
        """Should work normally when enhancements disabled."""
        config = StatusLineConfig()
        config.set('time.show_time_of_day', False)
        config.set('time.show_productivity_indicator', False)
        segment = TimeSegment(config)

        output = segment.render("test-session", None)
        # Should not contain enhancement icons
        assert "🌅" not in output
        assert "☀️" not in output
        assert "🌙" not in output
        assert "🌃" not in output
        assert "🟢" not in output
        assert "🟡" not in output
        assert "🔴" not in output

    def test_render_with_missing_transcript(self):
        """Should gracefully handle missing transcript."""
        config = StatusLineConfig()
        config.set('time.show_productivity_indicator', True)
        segment = TimeSegment(config)

        # Should not crash when transcript is None or invalid
        output = segment.render("test-session", None)
        assert output is not None
        assert "🟢" not in output  # No productivity indicator

    def test_render_preserves_existing_functionality(self):
        """Should preserve existing time display functionality."""
        config = StatusLineConfig()
        config.set('display.show_current_time', True)
        config.set('display.show_session_duration', True)
        segment = TimeSegment(config)

        output = segment.render("test-session")
        # Should still show time separator and duration emoji
        assert "│" in output
        assert "⏱" in output
