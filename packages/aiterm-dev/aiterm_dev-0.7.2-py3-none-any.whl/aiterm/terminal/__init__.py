"""Terminal detection and integration."""

import os
from enum import Enum
from typing import Optional

from aiterm.context.detector import ContextInfo


class TerminalType(Enum):
    """Supported terminal emulators."""

    ITERM2 = "iterm2"
    GHOSTTY = "ghostty"
    KITTY = "kitty"
    ALACRITTY = "alacritty"
    WEZTERM = "wezterm"
    APPLE_TERMINAL = "apple-terminal"
    UNKNOWN = "unknown"


def detect_terminal() -> TerminalType:
    """Detect which terminal emulator is running.

    Returns:
        TerminalType enum value for the detected terminal.
    """
    term_program = os.environ.get("TERM_PROGRAM", "").lower()

    if term_program == "iterm.app":
        return TerminalType.ITERM2
    elif term_program == "ghostty":
        return TerminalType.GHOSTTY
    elif term_program == "kitty":
        return TerminalType.KITTY
    elif term_program == "alacritty":
        return TerminalType.ALACRITTY
    elif term_program == "wezterm":
        return TerminalType.WEZTERM
    elif term_program == "apple_terminal":
        return TerminalType.APPLE_TERMINAL

    # Check other environment variables
    if os.environ.get("KITTY_WINDOW_ID"):
        return TerminalType.KITTY
    if os.environ.get("WEZTERM_PANE"):
        return TerminalType.WEZTERM

    return TerminalType.UNKNOWN


def apply_context(context: ContextInfo) -> bool:
    """Apply a context to the current terminal.

    Automatically detects the terminal type and applies context appropriately.

    Args:
        context: The context info to apply.

    Returns:
        True if context was applied, False if terminal not supported.
    """
    terminal = detect_terminal()

    if terminal == TerminalType.ITERM2:
        from aiterm.terminal import iterm2

        iterm2.apply_context(context)
        return True

    elif terminal == TerminalType.GHOSTTY:
        from aiterm.terminal import ghostty

        ghostty.apply_context(context)
        return True

    # Other terminals: just set title via standard escape sequence
    elif terminal in (
        TerminalType.KITTY,
        TerminalType.ALACRITTY,
        TerminalType.WEZTERM,
        TerminalType.APPLE_TERMINAL,
    ):
        import sys

        title = context.title
        sys.stdout.write(f"\033]2;{title}\007")
        sys.stdout.flush()
        return True

    return False


def get_terminal_info() -> dict:
    """Get information about the current terminal.

    Returns:
        Dict with terminal type, name, and capabilities.
    """
    terminal = detect_terminal()

    info = {
        "type": terminal.value,
        "name": terminal.name,
        "supports_profiles": terminal == TerminalType.ITERM2,
        "supports_user_vars": terminal == TerminalType.ITERM2,
        "supports_themes": terminal in (TerminalType.GHOSTTY, TerminalType.ITERM2),
        "config_editable": terminal == TerminalType.GHOSTTY,
    }

    # Add version info for supported terminals
    if terminal == TerminalType.GHOSTTY:
        from aiterm.terminal import ghostty

        version = ghostty.get_version()
        if version:
            info["version"] = version

    return info
