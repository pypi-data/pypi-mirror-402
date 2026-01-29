"""StatusLine Hook Templates for Claude Code v2.1+.

This module provides pre-built hook templates that can be installed
to enable automatic statusLine customization based on events:

- on-theme-change: Auto-update colors when terminal theme changes
- on-remote-session: Auto-enable remote indicator for /teleport
- on-error: Show alert when statusLine rendering fails
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
from rich.console import Console

console = Console()


class StatusLineHooks:
    """Pre-built hook templates for Claude Code v2.1+."""

    HOOKS_DIR = Path.home() / ".claude" / "hooks"

    TEMPLATES = {
        "on-theme-change": {
            "name": "on-theme-change",
            "description": "Auto-update statusLine colors when terminal theme changes",
            "hook_type": "PostToolUse",
            "enabled": True,
            "priority": 50,
            "content": """#!/bin/bash
# Hook: StatusLine - Theme Change Detection
# Detects terminal theme changes and updates statusLine colors accordingly
# Requires: iTerm2 or similar with theme reporting

THEME_CACHE="$HOME/.cache/claude-statusline-theme"
mkdir -p "$(dirname "$THEME_CACHE")"

# Detect current terminal theme
detect_theme() {
    if [ -n "$ITERM_PROFILE" ]; then
        # iTerm2: get current profile name
        echo "$ITERM_PROFILE"
    elif command -v ghostty &> /dev/null; then
        # Ghostty: check theme setting
        grep "^theme " ~/.config/ghostty/config 2>/dev/null | cut -d' ' -f2
    else
        echo "unknown"
    fi
}

CURRENT_THEME=$(detect_theme)
CACHED_THEME=$(cat "$THEME_CACHE" 2>/dev/null || echo "")

if [ "$CURRENT_THEME" != "$CACHED_THEME" ]; then
    echo "$CURRENT_THEME" > "$THEME_CACHE"
    # Notify statusLine to update colors
    # The statusLine will auto-detect theme on next render
fi
""",
        },
        "on-remote-session": {
            "name": "on-remote-session",
            "description": "Enable remote indicator when using Claude Code /teleport feature",
            "hook_type": "PreToolUse",
            "enabled": True,
            "priority": 60,
            "content": """#!/bin/bash
# Hook: StatusLine - Remote Session Detection
# Detects when /teleport is used and enables remote indicators
# Works with Claude Code v2.1+

SESSION_DATA="$HOME/.claude/sessions/active/session.json"
REMOTE_MARKER="$HOME/.cache/claude-statusline-remote"

if [ -f "$SESSION_DATA" ]; then
    # Check if session has teleport flag
    TELEPORT=$(jq -r '.features.teleport // false' "$SESSION_DATA" 2>/dev/null)

    if [ "$TELEPORT" = "true" ]; then
        # Mark as remote for statusLine
        mkdir -p "$(dirname "$REMOTE_MARKER")"
        echo "1" > "$REMOTE_MARKER"
    else
        rm -f "$REMOTE_MARKER"
    fi
fi
""",
        },
        "on-error": {
            "name": "on-error",
            "description": "Show alert when statusLine rendering fails",
            "hook_type": "PostToolUse",
            "enabled": False,  # Disabled by default - opt-in
            "priority": 40,
            "content": """#!/bin/bash
# Hook: StatusLine - Error Monitoring
# Watches for statusLine rendering errors and shows alerts
# Opt-in: enable with 'ait statusline hooks add on-error'

LOG_FILE="$HOME/.claude/logs/claude-code.log"
ERROR_MARKER="$HOME/.cache/claude-statusline-error"

if [ -f "$LOG_FILE" ]; then
    # Check recent logs for statusLine errors
    if grep -q "statusLine.*error\\|statusLine.*fail" "$LOG_FILE" 2>/dev/null; then
        mkdir -p "$(dirname "$ERROR_MARKER")"

        # Get error count from marker
        ERROR_COUNT=$(cat "$ERROR_MARKER" 2>/dev/null || echo "0")
        ERROR_COUNT=$((ERROR_COUNT + 1))
        echo "$ERROR_COUNT" > "$ERROR_MARKER"

        # Only show alert every 10 errors to avoid spam
        if [ $((ERROR_COUNT % 10)) -eq 0 ]; then
            echo "⚠️  StatusLine errors detected. Run 'ait statusline doctor' for details."
        fi
    else
        rm -f "$ERROR_MARKER"
    fi
fi
""",
        },
    }

    @classmethod
    def list_templates(cls) -> List[str]:
        """List available hook templates.

        Returns:
            List of template names
        """
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template(cls, name: str) -> Optional[Dict]:
        """Get a specific hook template.

        Args:
            name: Template name

        Returns:
            Template dict or None if not found
        """
        return cls.TEMPLATES.get(name)

    @classmethod
    def validate_template(cls, name: str) -> tuple[bool, Optional[str]]:
        """Validate a hook template before installation.

        Args:
            name: Template name

        Returns:
            Tuple of (valid, error_message)
        """
        template = cls.get_template(name)
        if not template:
            return False, f"Template '{name}' not found"

        # Check required fields
        required_fields = ["name", "description", "hook_type", "content"]
        for field in required_fields:
            if field not in template:
                return False, f"Template missing required field: {field}"

        # Validate hook type
        valid_types = ["PreToolUse", "PostToolUse", "Stop"]
        if template["hook_type"] not in valid_types:
            return False, f"Invalid hook_type: {template['hook_type']}"

        # Check content is not empty
        if not template["content"] or not template["content"].strip():
            return False, "Template content is empty"

        return True, None

    @classmethod
    def install_template(cls, name: str, enable: bool = True) -> tuple[bool, str]:
        """Install a hook template.

        Args:
            name: Template name
            enable: Whether to enable the hook after installation

        Returns:
            Tuple of (success, message)
        """
        # Validate template
        valid, error = cls.validate_template(name)
        if not valid:
            return False, error

        template = cls.get_template(name)
        if not template:
            return False, f"Template '{name}' not found"

        # Create hooks directory if needed
        cls.HOOKS_DIR.mkdir(parents=True, exist_ok=True)

        # Write hook file
        hook_filename = f"statusline-{name}.sh"
        hook_path = cls.HOOKS_DIR / hook_filename

        try:
            hook_path.write_text(template["content"], encoding="utf-8")
            hook_path.chmod(0o755)

            # Register in hook index
            cls._register_hook(name, hook_path, template, enable)

            return True, f"Hook '{name}' installed at {hook_path}"
        except Exception as e:
            return False, f"Failed to install hook: {e}"

    @classmethod
    def _register_hook(
        cls, name: str, path: Path, template: Dict, enable: bool
    ) -> None:
        """Register hook in Claude Code hook index.

        Args:
            name: Hook name
            path: Hook file path
            template: Hook template
            enable: Whether to enable
        """
        # Create hook index in HOOKS_DIR
        index_file = cls.HOOKS_DIR / "index.json"

        index = {}
        if index_file.exists():
            try:
                index = json.loads(index_file.read_text())
            except json.JSONDecodeError:
                index = {}

        index[name] = {
            "path": str(path),
            "enabled": enable,
            "type": template.get("hook_type"),
            "description": template.get("description"),
        }

        # Ensure parent directory exists
        index_file.parent.mkdir(parents=True, exist_ok=True)
        index_file.write_text(json.dumps(index, indent=2), encoding="utf-8")

    @classmethod
    def uninstall_template(cls, name: str) -> tuple[bool, str]:
        """Uninstall a hook template.

        Args:
            name: Template name

        Returns:
            Tuple of (success, message)
        """
        hook_path = cls.HOOKS_DIR / f"statusline-{name}.sh"

        if not hook_path.exists():
            return False, f"Hook '{name}' not installed"

        try:
            hook_path.unlink()

            # Remove from index
            index_file = Path.home() / ".claude" / "hooks" / "index.json"
            if index_file.exists():
                try:
                    index = json.loads(index_file.read_text())
                    index.pop(name, None)
                    index_file.write_text(json.dumps(index, indent=2))
                except json.JSONDecodeError:
                    pass

            return True, f"Hook '{name}' uninstalled"
        except Exception as e:
            return False, f"Failed to uninstall hook: {e}"

    @classmethod
    def list_installed(cls) -> List[Dict]:
        """List installed hooks.

        Returns:
            List of installed hook info dicts
        """
        index_file = cls.HOOKS_DIR / "index.json"

        if not index_file.exists():
            return []

        try:
            index = json.loads(index_file.read_text())
            return [
                {"name": name, **info}
                for name, info in index.items()
            ]
        except json.JSONDecodeError:
            return []

    @classmethod
    def enable_hook(cls, name: str) -> tuple[bool, str]:
        """Enable a hook.

        Args:
            name: Hook name

        Returns:
            Tuple of (success, message)
        """
        index_file = cls.HOOKS_DIR / "index.json"

        if not index_file.exists():
            return False, "No hooks installed"

        try:
            index = json.loads(index_file.read_text())
            if name not in index:
                return False, f"Hook '{name}' not found"

            index[name]["enabled"] = True
            index_file.write_text(json.dumps(index, indent=2))
            return True, f"Hook '{name}' enabled"
        except Exception as e:
            return False, f"Failed to enable hook: {e}"

    @classmethod
    def disable_hook(cls, name: str) -> tuple[bool, str]:
        """Disable a hook.

        Args:
            name: Hook name

        Returns:
            Tuple of (success, message)
        """
        index_file = cls.HOOKS_DIR / "index.json"

        if not index_file.exists():
            return False, "No hooks installed"

        try:
            index = json.loads(index_file.read_text())
            if name not in index:
                return False, f"Hook '{name}' not found"

            index[name]["enabled"] = False
            index_file.write_text(json.dumps(index, indent=2))
            return True, f"Hook '{name}' disabled"
        except Exception as e:
            return False, f"Failed to disable hook: {e}"
