"""Background agent detection for Claude Code.

This module detects running Task agents launched via run_in_background.

Current implementation uses process detection as a placeholder.
Future improvements could parse transcript files or use Claude Code's internal API.
"""

from pathlib import Path
from typing import Optional
import subprocess
import re


class AgentDetector:
    """Detects running background agents in Claude Code sessions."""

    def __init__(self):
        """Initialize agent detector."""
        pass

    def get_running_count(self, session_id: Optional[str] = None) -> int:
        """Get count of running background agents.

        Args:
            session_id: Optional session ID for filtering

        Returns:
            Number of running agents (0 if detection unavailable)
        """
        # PLACEHOLDER: Multiple detection strategies

        # Strategy 1: Check for agent tracking files
        count = self._check_agent_files(session_id)
        if count > 0:
            return count

        # Strategy 2: Check process tree (less reliable)
        # Disabled for now as it may count unrelated processes
        # count = self._check_processes()
        # if count > 0:
        #     return count

        # No agents detected
        return 0

    def _check_agent_files(self, session_id: Optional[str]) -> int:
        """Check for agent tracking files.

        Claude Code may create files to track background agents.

        Args:
            session_id: Session ID to check

        Returns:
            Number of agents detected via files
        """
        if not session_id:
            return 0

        # Check common locations for agent tracking
        possible_locations = [
            Path.home() / '.claude' / 'sessions' / session_id / 'agents',
            Path.home() / '.claude' / 'agents' / session_id,
            Path(f'/tmp/claude-agents-{session_id}'),
        ]

        for location in possible_locations:
            if location.exists() and location.is_dir():
                # Count agent PID files or status files (use set to avoid duplicates)
                agent_files = list(set(location.glob('*.pid')) | set(location.glob('agent-*')))
                if agent_files:
                    # Filter for running agents (check if PIDs are alive)
                    running = 0
                    for agent_file in agent_files:
                        if self._is_agent_running(agent_file):
                            running += 1
                    return running

        return 0

    def _is_agent_running(self, agent_file: Path) -> bool:
        """Check if agent represented by file is still running.

        Args:
            agent_file: Path to agent tracking file

        Returns:
            True if agent is running, False otherwise
        """
        # If it's a PID file, check if process is alive
        if agent_file.suffix == '.pid':
            try:
                pid = int(agent_file.read_text().strip())
                # Check if process exists (works on Unix-like systems)
                subprocess.run(
                    ['kill', '-0', str(pid)],
                    capture_output=True,
                    check=True
                )
                return True
            except (ValueError, subprocess.CalledProcessError, FileNotFoundError):
                return False

        # For other files, assume they exist = agent running
        # (Future: parse file content for status)
        return True

    def _check_processes(self) -> int:
        """Check process tree for agent processes.

        This is a fallback method that looks for Claude Code subprocesses.
        Less reliable as it may count unrelated processes.

        Returns:
            Estimated number of agent processes
        """
        try:
            # Look for claude processes with 'task' or 'agent' in command
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return 0

            # Count claude processes that look like agents
            # (This is very heuristic and may not be accurate)
            agent_patterns = [
                r'claude.*--agent',
                r'claude.*task.*background',
                r'claude-code.*subagent',
            ]

            count = 0
            for line in result.stdout.split('\n'):
                if 'claude' in line.lower():
                    for pattern in agent_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            count += 1
                            break

            return count

        except Exception:
            return 0


def format_agent_display(count: int, compact: bool = True) -> str:
    """Format background agent count for display.

    Args:
        count: Number of running agents
        compact: Use compact format (default: True)

    Returns:
        Formatted string, or empty if count is 0
    """
    if count == 0:
        return ""

    if compact:
        return f"🤖{count}"
    else:
        plural = "s" if count > 1 else ""
        return f"{count} agent{plural}"
