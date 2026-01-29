"""Tests for StatusLine agent detection.

Tests the background agent detection functionality including:
- PID file detection
- Process validation
- Multi-strategy detection
- Display formatting
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from aiterm.statusline.agents import AgentDetector, format_agent_display


class TestAgentDetector:
    """Test background agent detection."""

    def test_get_running_count_no_session(self):
        """Should return 0 when no session_id provided."""
        detector = AgentDetector()
        assert detector.get_running_count(None) == 0

    def test_get_running_count_no_files(self):
        """Should return 0 when no agent files exist."""
        detector = AgentDetector()
        count = detector.get_running_count("nonexistent-session-xyz")
        assert count == 0

    def test_check_agent_files_with_pid_files(self, tmp_path):
        """Should detect running agents from PID files."""
        detector = AgentDetector()

        # Create mock agent directory
        agent_dir = tmp_path / ".claude" / "agents" / "test-session"
        agent_dir.mkdir(parents=True)

        # Create PID file with current process (guaranteed to be running)
        pid_file = agent_dir / "agent-1.pid"
        pid_file.write_text(str(os.getpid()))

        # Monkey patch to use tmp_path
        with patch.object(Path, 'home', return_value=tmp_path):
            count = detector._check_agent_files("test-session")
            assert count == 1

    def test_check_agent_files_dead_pid(self, tmp_path):
        """Should ignore dead PIDs."""
        detector = AgentDetector()

        agent_dir = tmp_path / ".claude" / "agents" / "test-session"
        agent_dir.mkdir(parents=True)

        # Use PID that definitely doesn't exist
        pid_file = agent_dir / "agent-1.pid"
        pid_file.write_text("999999")

        with patch.object(Path, 'home', return_value=tmp_path):
            count = detector._check_agent_files("test-session")
            assert count == 0

    def test_check_agent_files_multiple_locations(self, tmp_path):
        """Should check all possible locations."""
        detector = AgentDetector()

        # Create agent file in first location
        agent_dir1 = tmp_path / ".claude" / "sessions" / "test-session" / "agents"
        agent_dir1.mkdir(parents=True)
        pid_file1 = agent_dir1 / "agent-1.pid"
        pid_file1.write_text(str(os.getpid()))

        with patch.object(Path, 'home', return_value=tmp_path):
            count = detector._check_agent_files("test-session")
            assert count == 1

    def test_is_agent_running_valid_pid(self, tmp_path):
        """Should return True for valid running PID."""
        detector = AgentDetector()

        pid_file = tmp_path / "agent.pid"
        pid_file.write_text(str(os.getpid()))

        assert detector._is_agent_running(pid_file) is True

    def test_is_agent_running_invalid_pid(self, tmp_path):
        """Should return False for invalid PID."""
        detector = AgentDetector()

        pid_file = tmp_path / "agent.pid"
        pid_file.write_text("not-a-number")

        assert detector._is_agent_running(pid_file) is False

    def test_is_agent_running_dead_pid(self, tmp_path):
        """Should return False for dead process."""
        detector = AgentDetector()

        pid_file = tmp_path / "agent.pid"
        pid_file.write_text("999999")

        assert detector._is_agent_running(pid_file) is False

    def test_is_agent_running_non_pid_file(self, tmp_path):
        """Should return True for non-PID tracking files."""
        detector = AgentDetector()

        agent_file = tmp_path / "agent-task-1"
        agent_file.touch()

        assert detector._is_agent_running(agent_file) is True

    def test_check_agent_files_mixed_pids(self, tmp_path):
        """Should count only running PIDs."""
        detector = AgentDetector()

        agent_dir = tmp_path / ".claude" / "agents" / "test-session"
        agent_dir.mkdir(parents=True)

        # One running PID
        pid_file1 = agent_dir / "agent-1.pid"
        pid_file1.write_text(str(os.getpid()))

        # One dead PID
        pid_file2 = agent_dir / "agent-2.pid"
        pid_file2.write_text("999999")

        with patch.object(Path, 'home', return_value=tmp_path):
            count = detector._check_agent_files("test-session")
            assert count == 1


class TestFormatAgentDisplay:
    """Test agent display formatting."""

    def test_format_agent_display_zero(self):
        """Should return empty string for 0 agents."""
        assert format_agent_display(0) == ""

    def test_format_agent_display_one_compact(self):
        """Should format single agent in compact mode."""
        assert format_agent_display(1, compact=True) == "🤖1"

    def test_format_agent_display_multiple_compact(self):
        """Should format multiple agents in compact mode."""
        assert format_agent_display(3, compact=True) == "🤖3"

    def test_format_agent_display_one_verbose(self):
        """Should format single agent in verbose mode."""
        assert format_agent_display(1, compact=False) == "1 agent"

    def test_format_agent_display_multiple_verbose(self):
        """Should format multiple agents with plural."""
        assert format_agent_display(3, compact=False) == "3 agents"

    def test_format_agent_display_large_count(self):
        """Should handle large agent counts."""
        assert format_agent_display(99, compact=True) == "🤖99"
        assert format_agent_display(99, compact=False) == "99 agents"
