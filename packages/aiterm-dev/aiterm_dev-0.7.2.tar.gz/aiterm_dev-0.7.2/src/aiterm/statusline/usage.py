"""Usage tracking for Claude Code sessions and weekly limits.

This module provides usage tracking functionality for the statusLine.
Currently uses placeholder data until Claude Code provides an official API.

Future integration points:
- Option A: Parse `claude --usage` command output
- Option B: Read from Claude Code internal files/database
- Option C: Use usage fields from JSON input (if added by Claude Code)
"""

from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import subprocess
import urllib.request
import json
from pathlib import Path


@dataclass
class UsageData:
    """Usage tracking data.

    Attributes:
        current: Current usage count
        limit: Maximum allowed usage
        reset_time: Timestamp when usage resets (Unix timestamp)
    """
    current: int
    limit: int
    reset_time: int  # Unix timestamp

    def percent_used(self) -> float:
        """Calculate percentage of usage.

        Returns:
            Percentage (0.0 to 100.0)
        """
        if self.limit == 0:
            return 0.0
        return (self.current / self.limit) * 100

    def time_until_reset(self) -> str:
        """Format time until reset.

        Returns:
            Formatted string like "2h15m", "3d4h", etc.
        """
        now = int(datetime.now().timestamp())
        seconds_left = self.reset_time - now

        if seconds_left <= 0:
            return "now"

        # Convert to appropriate units
        if seconds_left < 3600:  # < 1 hour
            minutes = seconds_left // 60
            return f"{minutes}m"
        elif seconds_left < 86400:  # < 1 day
            hours = seconds_left // 3600
            minutes = (seconds_left % 3600) // 60
            return f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
        else:  # >= 1 day
            days = seconds_left // 86400
            hours = (seconds_left % 86400) // 3600
            return f"{days}d{hours}h" if hours > 0 else f"{days}d"


class UsageTracker:
    """Tracks Claude Code usage limits.

    Fetches usage data from Anthropic API endpoint.
    """

    API_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"

    def __init__(self):
        """Initialize usage tracker."""
        self._api_key = self._get_api_key()
        self._cache_file = Path.home() / '.cache' / 'aiterm' / 'usage.json'
        self._cache_ttl = 60  # Cache for 60 seconds

    def _get_api_key(self) -> Optional[str]:
        """Get Anthropic API key or OAuth token.

        Checks in order:
        1. macOS Keychain (Claude Code OAuth token)
        2. aiterm config (anthropic.api_key)
        3. Environment variable (ANTHROPIC_API_KEY)
        4. Claude Code settings (apiKey) - usually not present

        Returns:
            API key/token or None if not found
        """
        import os
        import subprocess
        import sys

        # Try to get OAuth token from macOS Keychain (Claude Code)
        if sys.platform == 'darwin':
            try:
                result = subprocess.run(
                    ['security', 'find-generic-password', '-s', 'Claude Code-credentials', '-w'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    creds = json.loads(result.stdout.strip())
                    token = creds.get('claudeAiOauth', {}).get('accessToken')
                    if token:
                        return token
            except Exception:
                pass

        # Check aiterm config
        try:
            config_file = Path.home() / '.config' / 'aiterm' / 'statusline.json'
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
                api_key = config.get('anthropic', {}).get('api_key')
                if api_key:
                    return api_key
        except Exception:
            pass

        # Check environment variable
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            return api_key

        # Check Claude Code settings (unlikely to exist)
        try:
            settings_file = Path.home() / '.claude' / 'settings.json'
            if settings_file.exists():
                with open(settings_file) as f:
                    settings = json.load(f)
                return settings.get('apiKey')
        except Exception:
            pass

        return None

    def _fetch_api_usage(self) -> Optional[dict]:
        """Fetch usage data from Anthropic API.

        Returns:
            Usage dict or None if fetch fails
        """
        if not self._api_key:
            return None

        # Check cache first
        if self._cache_file.exists():
            try:
                cache_age = datetime.now().timestamp() - self._cache_file.stat().st_mtime
                if cache_age < self._cache_ttl:
                    with open(self._cache_file) as f:
                        return json.load(f)
            except Exception:
                pass

        # Fetch from API
        try:
            # Determine if using OAuth token or API key
            if self._api_key and self._api_key.startswith('sk-ant-oat'):
                # OAuth token - use Bearer auth
                headers = {
                    'Authorization': f'Bearer {self._api_key}'
                }
            else:
                # API key - use x-api-key header
                headers = {
                    'x-api-key': self._api_key,
                    'anthropic-version': '2023-06-01'
                }

            req = urllib.request.Request(
                self.API_USAGE_URL,
                headers=headers
            )

            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read())

            # Cache the result
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, 'w') as f:
                json.dump(data, f)

            return data

        except Exception:
            return None

    def get_session_usage(self) -> Optional[UsageData]:
        """Get current session usage (5-hour limit).

        Returns:
            UsageData for session usage, or None if not available

        Note: Currently returns None because Claude Code does not expose
        usage limits programmatically. The /usage command shows this data
        in the chat interface, but it's not accessible to external tools.

        Tracking: https://github.com/anthropics/claude-code/issues/5621
        """
        # Claude Code usage limits are not accessible programmatically
        # The /usage slash command uses internal endpoints that are not exposed
        return None

        # When/if Claude Code exposes usage data in JSON input, implement here
        data = self._fetch_api_usage()
        if not data:
            return None

        try:
            five_hour = data.get('five_hour', {})
            utilization = five_hour.get('utilization', {})

            current = utilization.get('used', 0)
            limit = utilization.get('total', 0)
            reset_at = five_hour.get('resets_at', '')

            # Parse ISO timestamp
            if reset_at:
                reset_time = int(datetime.fromisoformat(reset_at.replace('Z', '+00:00')).timestamp())
            else:
                reset_time = int(datetime.now().timestamp()) + (5 * 3600)

            if limit > 0:
                return UsageData(
                    current=current,
                    limit=limit,
                    reset_time=reset_time
                )

        except Exception:
            pass

        return None

    def get_weekly_usage(self) -> Optional[UsageData]:
        """Get current weekly usage (7-day limit).

        Returns:
            UsageData for weekly usage, or None if not available

        Note: Currently returns None because Claude Code does not expose
        usage limits programmatically. See get_session_usage() for details.
        """
        # Claude Code usage limits are not accessible programmatically
        return None

        # When/if Claude Code exposes usage data in JSON input, implement here
        data = self._fetch_api_usage()
        if not data:
            return None

        try:
            seven_day = data.get('seven_day', {})
            utilization = seven_day.get('utilization', {})

            current = utilization.get('used', 0)
            limit = utilization.get('total', 0)
            reset_at = seven_day.get('resets_at', '')

            # Parse ISO timestamp
            if reset_at:
                reset_time = int(datetime.fromisoformat(reset_at.replace('Z', '+00:00')).timestamp())
            else:
                reset_time = int(datetime.now().timestamp()) + (7 * 86400)

            if limit > 0:
                return UsageData(
                    current=current,
                    limit=limit,
                    reset_time=reset_time
                )

        except Exception:
            pass

        return None

    def _parse_claude_usage_command(self) -> Tuple[Optional[UsageData], Optional[UsageData]]:
        """Parse output from `claude --usage` command (if it exists).

        This is a placeholder for future implementation.

        Returns:
            Tuple of (session_usage, weekly_usage)
        """
        # PLACEHOLDER: This command may not exist yet
        #
        # Future implementation:
        # try:
        #     result = subprocess.run(
        #         ['claude', '--usage'],
        #         capture_output=True,
        #         text=True,
        #         timeout=5
        #     )
        #
        #     if result.returncode == 0:
        #         output = result.stdout
        #         # Parse output like:
        #         # Session: 45/100 messages (resets in 2h 15m)
        #         # Weekly: 234/500 messages (resets in 3d 4h)
        #         ...
        #
        # except Exception:
        #     pass

        return (None, None)


def format_usage_display(
    session: Optional[UsageData],
    weekly: Optional[UsageData],
    compact: bool = True
) -> str:
    """Format usage data for statusLine display.

    Args:
        session: Session usage data
        weekly: Weekly usage data
        compact: Use compact format (default: True)

    Returns:
        Formatted string for display, or empty if no data
    """
    if not session and not weekly:
        return ""

    parts = []

    if session:
        if compact:
            # Compact: S:45/100(2h)
            parts.append(f"S:{session.current}/{session.limit}({session.time_until_reset()})")
        else:
            # Verbose: Session:45/100 (2h15m)
            parts.append(f"Session:{session.current}/{session.limit} ({session.time_until_reset()})")

    if weekly:
        if compact:
            # Compact: W:234/500(3d)
            parts.append(f"W:{weekly.current}/{weekly.limit}({weekly.time_until_reset()})")
        else:
            # Verbose: Weekly:234/500 (3d4h)
            parts.append(f"Weekly:{weekly.current}/{weekly.limit} ({weekly.time_until_reset()})")

    return " ".join(parts)


def get_usage_color(usage: UsageData, warning_threshold: int = 80) -> str:
    """Get color code based on usage percentage.

    Args:
        usage: Usage data
        warning_threshold: Percentage threshold for warning (default: 80)

    Returns:
        ANSI color code
    """
    percent = usage.percent_used()

    if percent < 50:
        return "38;5;2"  # Green
    elif percent < warning_threshold:
        return "38;5;3"  # Yellow
    elif percent < 95:
        return "38;5;208"  # Orange
    else:
        return "38;5;1"  # Red
