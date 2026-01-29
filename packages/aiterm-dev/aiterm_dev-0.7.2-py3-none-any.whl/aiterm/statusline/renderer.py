"""StatusLine renderer for Claude Code.

This module provides the main Renderer class that:
- Reads JSON from stdin (from Claude Code)
- Parses and extracts relevant fields
- Delegates to segment renderers
- Outputs formatted 2-line Powerlevel10k-style statusLine
"""

import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from aiterm.statusline.config import StatusLineConfig
from aiterm.statusline.themes import Theme, get_theme


# Spacing presets for gap between left and right segments
SPACING_PRESETS = {
    'minimal': {'base_percent': 0.15, 'min_gap': 5, 'max_gap': 20},
    'standard': {'base_percent': 0.20, 'min_gap': 10, 'max_gap': 40},
    'spacious': {'base_percent': 0.30, 'min_gap': 15, 'max_gap': 60}
}


class StatusLineRenderer:
    """Main renderer for statusLine output."""

    def __init__(self, config: Optional[StatusLineConfig] = None, theme: Optional[Theme] = None):
        """Initialize renderer.

        Args:
            config: StatusLineConfig instance (creates new if None)
            theme: Theme instance (loads from config if None)
        """
        self.config = config or StatusLineConfig()
        self.theme = theme or get_theme(self.config.get('theme.name', 'purple-charcoal'))

    def _get_separator(self) -> str:
        """Get separator pattern based on config.

        Returns:
            Formatted separator with spacing (e.g., " │ " or "  │  ")
        """
        spacing_mode = self.config.get('display.separator_spacing', 'standard')

        # Map spacing mode to number of spaces
        spacing_map = {
            'minimal': 1,
            'standard': 2,
            'relaxed': 3
        }

        spaces = spacing_map.get(spacing_mode, 2)  # Default to 2 (standard)
        space_str = ' ' * spaces

        return f"{space_str}\033[{self.theme.separator_fg}m│\033[0m{space_str}"

    def render(self, json_input: Optional[str] = None) -> str:
        """Render statusLine from JSON input.

        Args:
            json_input: JSON string from Claude Code (reads from stdin if None)

        Returns:
            Formatted statusLine output (2 lines)
        """
        # Read JSON from stdin if not provided
        if json_input is None:
            json_input = sys.stdin.read()

        # Parse JSON
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError as e:
            # Return error message in statusLine format
            return f"╭─ ⚠️  Invalid JSON input\n╰─ Error: {e.msg}"

        # Extract fields (handle None values from Claude Code)
        workspace = data.get('workspace') or {}
        model_data = data.get('model') or {}
        cost_data = data.get('cost') or {}
        output_style = data.get('output_style') or {}
        context_window = data.get('context_window') or {}

        cwd = workspace.get('current_dir', '')
        project_dir = workspace.get('project_dir', cwd)
        model_name = model_data.get('display_name', 'Unknown')
        style_name = output_style.get('name', 'default')
        session_id = data.get('session_id', 'default')
        transcript_path = data.get('transcript_path')

        # Extract cost/usage fields
        lines_added = cost_data.get('total_lines_added', 0)
        lines_removed = cost_data.get('total_lines_removed', 0)
        total_duration_ms = cost_data.get('total_duration_ms', 0)

        # Extract context window data
        context_size = context_window.get('context_window_size', 0)
        current_usage = context_window.get('current_usage') or {}
        input_tokens = current_usage.get('input_tokens', 0)
        output_tokens = current_usage.get('output_tokens', 0)

        # Build line 1 (directory + git)
        line1 = self._build_line1(cwd, project_dir)

        # Build line 2 (model + time + stats)
        line2 = self._build_line2(
            model_name=model_name,
            session_id=session_id,
            lines_added=lines_added,
            lines_removed=lines_removed,
            style_name=style_name,
            transcript_path=transcript_path
        )

        # Set window title
        self._set_window_title(project_dir, model_name)

        return f"{line1}\n{line2}"

    def _build_line1(self, cwd: str, project_dir: str) -> str:
        """Build line 1 (directory + git + optional right-side worktree).

        Args:
            cwd: Current working directory
            project_dir: Project root directory

        Returns:
            Formatted line 1 with optional right-side segments
        """
        # Import here to avoid circular imports
        from aiterm.statusline.segments import (
            ProjectSegment,
            GitSegment
        )

        # Get project segment
        project_segment = ProjectSegment(self.config, self.theme)
        project_output = project_segment.render(cwd, project_dir)

        # Get git segment
        git_segment = GitSegment(self.config, self.theme)
        git_output = git_segment.render(cwd)

        # Assemble left side
        line1_left = f"╭─{project_output}"

        if git_output:
            line1_left += git_output
        else:
            # Close directory segment
            line1_left += "\033[0m\033[38;5;4m▓▒░\033[0m"

        # Build right side (worktree context)
        line1_right = self._build_right_segments(cwd, git_segment)

        if line1_right:
            # Calculate padding for alignment
            return self._align_line(line1_left, line1_right)
        else:
            return line1_left

    def _build_line2(
        self,
        model_name: str,
        session_id: str,
        lines_added: int,
        lines_removed: int,
        style_name: str,
        transcript_path: Optional[str] = None
    ) -> str:
        """Build line 2 (model + time + stats).

        Args:
            model_name: Model display name
            session_id: Session ID for duration tracking
            lines_added: Total lines added
            lines_removed: Total lines removed
            style_name: Output style name
            transcript_path: Optional path to session transcript

        Returns:
            Formatted line 2
        """
        # Import here to avoid circular imports
        from aiterm.statusline.segments import (
            ModelSegment,
            TimeSegment,
            ThinkingSegment,
            LinesSegment,
            UsageSegment
        )

        # Model segment
        model_segment = ModelSegment(self.config, self.theme)
        model_output = model_segment.render(model_name)

        # Thinking mode indicator
        thinking_segment = ThinkingSegment(self.config, self.theme)
        thinking_output = thinking_segment.render()

        # Time segments
        time_segment = TimeSegment(self.config, self.theme)
        time_output = time_segment.render(session_id, transcript_path)

        # Lines changed
        lines_segment = LinesSegment(self.config, self.theme)
        lines_output = lines_segment.render(lines_added, lines_removed)

        # Build line 2
        line2 = f"╰─ {model_output}"

        # Add thinking indicator (includes separator if enabled)
        line2 += thinking_output

        # Add background agents count
        if self.config.get('display.show_background_agents', True):
            from aiterm.statusline.agents import AgentDetector
            detector = AgentDetector()
            agent_count = detector.get_running_count(session_id)
            if agent_count > 0:
                line2 += f"{self._get_separator()}\033[38;5;2m🤖{agent_count}\033[0m"

        # Add time
        line2 += time_output

        # Add usage tracking
        usage_segment = UsageSegment(self.config, self.theme)
        usage_output = usage_segment.render()
        if usage_output:
            line2 += f"{self._get_separator()}{usage_output}"

        # Add lines if available
        if lines_output:
            line2 += f"{self._get_separator()}{lines_output}"

        # Add style if not default
        if style_name and style_name != 'default':
            line2 += f"{self._get_separator()}\033[{self.theme.style_fg}m[{style_name}]\033[0m"

        return line2

    def _build_right_segments(self, cwd: str, git_segment) -> str:
        """Build right-aligned segments (worktree context).

        Args:
            cwd: Current working directory
            git_segment: GitSegment instance for accessing worktree methods

        Returns:
            Right-side content with P10k styling or empty string
        """
        if not self.config.get('git.show_worktrees', True):
            return ""

        worktree_name = git_segment._get_worktree_name(cwd)

        if worktree_name:
            # In a worktree - show name + marker
            content = f"(wt) {worktree_name}"
            return self._render_right_segment(content)
        else:
            # Main branch - optionally show worktree count
            worktree_count = git_segment._get_worktree_count(cwd)
            if worktree_count > 1:
                content = f"🌳 {worktree_count} worktrees"
                return self._render_right_segment(content)

        return ""

    def _render_right_segment(self, content: str) -> str:
        """Render single right-side segment with P10k reversed style.

        Args:
            content: Text content to display

        Returns:
            Formatted segment with reversed powerline arrows
        """
        # Reversed powerline style: ░▒▓ content ▓▒░
        # Using dark gray colors (235 bg, 245 fg)
        bg = '235'
        fg = '245'

        return (
            f"\033[48;5;{bg}m\033[38;5;{fg}m"
            f"░▒▓ {content} ▓▒░"
            f"\033[0m"
        )

    def _calculate_gap(self, terminal_width: int) -> int:
        """Calculate gap size between left and right segments.

        Args:
            terminal_width: Terminal width in columns

        Returns:
            Gap size in characters
        """
        # Get spacing mode from config (minimal/standard/spacious)
        mode = self.config.get('spacing.mode', 'standard')

        # Get preset parameters
        preset = SPACING_PRESETS.get(mode, SPACING_PRESETS['standard'])
        base_percent = preset['base_percent']
        min_gap = preset['min_gap']
        max_gap = preset['max_gap']

        # Allow config overrides
        min_gap = self.config.get('spacing.min_gap', min_gap)
        max_gap = self.config.get('spacing.max_gap', max_gap)

        # Calculate gap as percentage of terminal width
        gap = int(terminal_width * base_percent)

        # Apply constraints
        gap = max(min_gap, min(gap, max_gap))

        return gap

    def _render_gap(self, gap_size: int) -> str:
        """Render gap between left and right segments.

        Args:
            gap_size: Gap size in characters

        Returns:
            Rendered gap (spaces or spaces with centered separator)
        """
        # Check if separator should be shown
        show_separator = self.config.get('spacing.show_separator', True)

        if not show_separator or gap_size < 3:
            # Just return spaces
            return ' ' * gap_size

        # Render with centered separator (…)
        center = gap_size // 2
        left_spaces = center - 1
        right_spaces = gap_size - center

        # Dim gray color for separator (fg=240)
        separator = f"\033[38;5;240m…\033[0m"

        return f"{' ' * left_spaces}{separator}{' ' * right_spaces}"

    def _align_line(self, left: str, right: str) -> str:
        """Align left and right segments with spacing.

        Args:
            left: Left-side content (with ANSI codes)
            right: Right-side content (with ANSI codes)

        Returns:
            Aligned line with proper spacing
        """
        try:
            import shutil
            terminal_width = shutil.get_terminal_size((120, 24)).columns
        except (OSError, ValueError):
            terminal_width = 120  # Fallback

        left_width = self._strip_ansi_length(left)
        right_width = self._strip_ansi_length(right)

        # Calculate desired gap using spacing system
        gap_size = self._calculate_gap(terminal_width)

        # Check if there's enough room for left + gap + right
        total_needed = left_width + gap_size + right_width

        if total_needed <= terminal_width:
            # Perfect fit - use calculated gap with optional separator
            gap = self._render_gap(gap_size)
            return f"{left}{gap}{right}"
        else:
            # Not enough room - calculate available padding
            available_padding = terminal_width - left_width - right_width

            if available_padding > 0:
                # Use available padding (no separator, simpler)
                return f"{left}{' ' * available_padding}{right}"
            else:
                # Not enough room at all - fallback to left-only
                return left

    def _strip_ansi_length(self, text: str) -> int:
        """Get visible character count (strip ANSI codes).

        Args:
            text: Text with ANSI escape codes

        Returns:
            Length of visible characters only
        """
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return len(ansi_escape.sub('', text))

    def _set_window_title(self, project_dir: str, model_name: str) -> None:
        """Set terminal window title.

        Args:
            project_dir: Project directory path
            model_name: Model name
        """
        # Import here to avoid circular imports
        from aiterm.statusline.segments import ProjectSegment

        project_segment = ProjectSegment(self.config, self.theme)
        project_name = Path(project_dir).name
        project_icon = project_segment._get_project_icon(project_dir)

        # ANSI escape sequence for window title
        # Format: ESC ] 0 ; text BEL
        title = f"{project_icon} {project_name} ({model_name})"
        sys.stdout.write(f"\033]0;{title}\007")
        sys.stdout.flush()
