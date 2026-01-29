"""StatusLine integration for aiterm.

This module provides statusLine functionality for Claude Code,
including rendering, configuration, and theme management.
"""

from aiterm.statusline.config import StatusLineConfig
from aiterm.statusline.renderer import StatusLineRenderer
from aiterm.statusline.segments import (
    ProjectSegment,
    GitSegment,
    ModelSegment,
    TimeSegment,
    ThinkingSegment,
    LinesSegment,
    UsageSegment,
)

__all__ = [
    'StatusLineConfig',
    'StatusLineRenderer',
    'ProjectSegment',
    'GitSegment',
    'ModelSegment',
    'TimeSegment',
    'ThinkingSegment',
    'LinesSegment',
    'UsageSegment',
]
