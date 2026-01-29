"""StatusLine configuration management.

This module handles loading, saving, and validating statusLine configuration.
Configuration is stored at ~/.config/aiterm/statusline.json in XDG-compliant location.
"""

from pathlib import Path
from typing import Any, Optional
import json


class StatusLineConfig:
    """Manages statusLine configuration."""

    def __init__(self):
        """Initialize config manager."""
        # XDG-compliant config path
        config_dir = Path.home() / ".config" / "aiterm"
        self.config_path = config_dir / "statusline.json"
        self._schema = self._load_schema()
        self._config = None

    def load(self) -> dict:
        """Load config with defaults.

        Returns:
            Configuration dict with all settings.
        """
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            self._config = self._get_defaults()
            return self._config

        try:
            with open(self.config_path) as f:
                user_config = json.load(f)

            # Merge with defaults (user config takes precedence)
            defaults = self._get_defaults()
            self._config = self._deep_merge(defaults, user_config)
            return self._config

        except (json.JSONDecodeError, OSError) as e:
            # If config file is invalid, return defaults
            # Caller can check validate() to see the error
            return self._get_defaults()

    def save(self, config: dict) -> None:
        """Save config to disk.

        Args:
            config: Configuration dict to save.
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

        self._config = config

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with dot notation.

        Args:
            key: Setting key with dot notation (e.g., "display.show_git")
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config.get("display.show_git")  # Returns bool
            True
        """
        config = self.load()
        keys = key.split('.')

        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set config value with dot notation.

        Validates value against schema before setting.

        Args:
            key: Setting key with dot notation
            value: New value (will be type-checked against schema)

        Raises:
            ValueError: If value is invalid for the key
        """
        config = self.load()

        # Validate
        if not self._validate_value(key, value):
            schema_def = self._schema.get(key, {})
            expected_type = schema_def.get('type', 'unknown')
            actual_type = type(value).__name__

            error_msg = f"Invalid value for {key}: {value}"
            if 'choices' in schema_def:
                choices = ', '.join(str(c) for c in schema_def['choices'])
                error_msg += f"\nValid choices: {choices}"
            else:
                error_msg += f"\nExpected type: {expected_type}, got: {actual_type}"

            raise ValueError(error_msg)

        # Set nested value
        keys = key.split('.')
        target = config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

        self.save(config)

    def reset(self, key: Optional[str] = None) -> None:
        """Reset to defaults.

        Args:
            key: If provided, reset only this setting. If None, reset entire config.
        """
        if key is None:
            # Reset entire config
            self.save(self._get_defaults())
        else:
            # Reset single key
            defaults = self._get_defaults()
            default_value = self._get_nested(defaults, key.split('.'))
            if default_value is not None:
                self.set(key, default_value)

    def validate(self) -> tuple[bool, list[str]]:
        """Validate current config.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Check if file exists and is valid JSON
        if not self.config_path.exists():
            return (True, [])  # No file is valid (will use defaults)

        try:
            with open(self.config_path) as f:
                user_config = json.load(f)
        except json.JSONDecodeError as e:
            return (False, [f"Invalid JSON: {e.msg} at line {e.lineno}"])
        except OSError as e:
            return (False, [f"Cannot read config file: {e}"])

        # Validate each setting against schema
        config = self.load()
        errors = []

        for key, schema_def in self._schema.items():
            value = self.get(key)

            if not self._validate_value(key, value):
                expected_type = schema_def['type']
                actual_type = type(value).__name__
                errors.append(
                    f"{key}: expected {expected_type}, got {actual_type} ({value})"
                )

        return (len(errors) == 0, errors)

    def get_schema(self) -> dict:
        """Get configuration schema.

        Returns:
            Dict mapping keys to schema definitions. Each schema def includes:
            - type: str, bool, int, list
            - default: default value
            - description: human-readable description
            - category: grouping (display, git, project, usage, theme, time)
            - choices: valid choices (if applicable)
        """
        return self._schema

    def list_settings(self, category: Optional[str] = None) -> list[dict]:
        """List all settings with metadata.

        Args:
            category: If provided, filter by category

        Returns:
            List of dicts with keys:
            - key: setting key
            - value: current value
            - type: data type
            - default: default value
            - description: description
            - category: category name
        """
        config = self.load()
        schema = self.get_schema()

        settings = []
        for key, meta in schema.items():
            if category and meta.get('category') != category:
                continue

            settings.append({
                'key': key,
                'value': self.get(key),
                'type': meta['type'],
                'default': meta['default'],
                'description': meta['description'],
                'category': meta.get('category', 'other')
            })

        return settings

    # Private methods

    def _load_schema(self) -> dict:
        """Load configuration schema.

        Returns:
            Schema dict mapping keys to metadata.
        """
        return {
            'display.directory_mode': {
                'type': 'str',
                'default': 'smart',
                'choices': ['smart', 'basename', 'full'],
                'description': 'Directory display mode',
                'category': 'display'
            },
            'display.show_git': {
                'type': 'bool',
                'default': True,
                'description': 'Show git information',
                'category': 'display'
            },
            'display.show_thinking_indicator': {
                'type': 'bool',
                'default': True,
                'description': 'Show thinking mode indicator',
                'category': 'display'
            },
            'display.show_background_agents': {
                'type': 'bool',
                'default': True,
                'description': 'Show background agent count',
                'category': 'display'
            },
            'display.show_output_style': {
                'type': 'str',
                'default': 'auto',
                'choices': ['auto', 'always', 'never'],
                'description': 'When to show output style',
                'category': 'display'
            },
            'display.show_session_duration': {
                'type': 'bool',
                'default': True,
                'description': 'Show session duration',
                'category': 'display'
            },
            'display.show_current_time': {
                'type': 'bool',
                'default': True,
                'description': 'Show current time',
                'category': 'display'
            },
            'display.show_lines_changed': {
                'type': 'bool',
                'default': True,
                'description': 'Show lines added/removed',
                'category': 'display'
            },
            'display.show_r_version': {
                'type': 'bool',
                'default': True,
                'description': 'Show R package version',
                'category': 'display'
            },
            'display.show_session_usage': {
                'type': 'bool',
                'default': True,
                'description': 'Show session usage stats',
                'category': 'display'
            },
            'display.show_weekly_usage': {
                'type': 'bool',
                'default': True,
                'description': 'Show weekly usage stats',
                'category': 'display'
            },
            'display.max_directory_length': {
                'type': 'int',
                'default': 50,
                'description': 'Max directory name length',
                'category': 'display'
            },
            'display.separator_spacing': {
                'type': 'str',
                'default': 'standard',
                'choices': ['minimal', 'standard', 'relaxed'],
                'description': 'Spacing around separators (minimal=1, standard=2, relaxed=3 spaces)',
                'category': 'display'
            },
            'spacing.mode': {
                'type': 'str',
                'default': 'standard',
                'choices': ['minimal', 'standard', 'spacious'],
                'description': 'Gap size between left and right segments',
                'category': 'display'
            },
            'spacing.min_gap': {
                'type': 'int',
                'default': 10,
                'description': 'Minimum gap in chars (narrow terminal fallback)',
                'category': 'display'
            },
            'spacing.max_gap': {
                'type': 'int',
                'default': 40,
                'description': 'Maximum gap in chars (wide terminal cap)',
                'category': 'display'
            },
            'spacing.show_separator': {
                'type': 'bool',
                'default': True,
                'description': 'Show subtle separator (…) in gap center',
                'category': 'display'
            },
            'usage.show_reset_timer': {
                'type': 'bool',
                'default': True,
                'description': 'Show time until usage reset',
                'category': 'usage'
            },
            'usage.warning_threshold': {
                'type': 'int',
                'default': 80,
                'description': 'Usage warning threshold (%)',
                'category': 'usage'
            },
            'usage.compact_format': {
                'type': 'bool',
                'default': True,
                'description': 'Use compact usage display',
                'category': 'usage'
            },
            'theme.name': {
                'type': 'str',
                'default': 'purple-charcoal',
                'choices': ['purple-charcoal', 'cool-blues', 'forest-greens'],
                'description': 'Color theme',
                'category': 'theme'
            },
            'git.show_ahead_behind': {
                'type': 'bool',
                'default': True,
                'description': 'Show ahead/behind indicators',
                'category': 'git'
            },
            'git.show_untracked_count': {
                'type': 'bool',
                'default': True,
                'description': 'Show untracked file count',
                'category': 'git'
            },
            'git.show_stash_count': {
                'type': 'bool',
                'default': False,
                'description': 'Show stash count',
                'category': 'git'
            },
            'git.show_remote_status': {
                'type': 'bool',
                'default': False,
                'description': 'Show remote tracking branch',
                'category': 'git'
            },
            'git.truncate_branch_length': {
                'type': 'int',
                'default': 32,
                'description': 'Max branch name length',
                'category': 'git'
            },
            'git.show_worktrees': {
                'type': 'bool',
                'default': True,
                'description': 'Show worktree count and indicator',
                'category': 'git'
            },
            'project.detect_python_env': {
                'type': 'bool',
                'default': False,
                'description': 'Show Python environment',
                'category': 'project'
            },
            'project.detect_node_version': {
                'type': 'bool',
                'default': False,
                'description': 'Show Node.js version',
                'category': 'project'
            },
            'project.detect_r_package_health': {
                'type': 'bool',
                'default': False,
                'description': 'Show R package health',
                'category': 'project'
            },
            'project.show_dependency_warnings': {
                'type': 'bool',
                'default': False,
                'description': 'Show outdated dependency warnings',
                'category': 'project'
            },
            'time.session_duration_format': {
                'type': 'str',
                'default': 'compact',
                'choices': ['compact', 'verbose'],
                'description': 'Session duration format',
                'category': 'time'
            },
            'time.show_productivity_indicator': {
                'type': 'bool',
                'default': False,
                'description': 'Show activity level indicator',
                'category': 'time'
            },
            'time.show_time_of_day': {
                'type': 'bool',
                'default': False,
                'description': 'Show time-of-day icon',
                'category': 'time'
            },
            'time.time_format': {
                'type': 'str',
                'default': '24h',
                'choices': ['24h', '12h'],
                'description': 'Time format',
                'category': 'time'
            }
        }

    def _get_defaults(self) -> dict:
        """Generate default config from schema.

        Returns:
            Default configuration dict.
        """
        config = {}

        for key, meta in self._schema.items():
            keys = key.split('.')
            target = config

            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]

            target[keys[-1]] = meta['default']

        return config

    def _validate_value(self, key: str, value: Any) -> bool:
        """Validate value against schema.

        Args:
            key: Setting key
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        if key not in self._schema:
            return False

        schema_def = self._schema[key]
        expected_type = schema_def['type']

        # Type check
        type_map = {
            'str': str,
            'bool': bool,
            'int': int,
            'list': list
        }

        if expected_type not in type_map:
            return False

        if not isinstance(value, type_map[expected_type]):
            return False

        # Choices check
        if 'choices' in schema_def:
            if value not in schema_def['choices']:
                return False

        return True

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dicts.

        Args:
            base: Base dict
            override: Override dict (takes precedence)

        Returns:
            Merged dict
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _get_nested(self, d: dict, keys: list[str]) -> Any:
        """Get nested value from dict.

        Args:
            d: Dict to search
            keys: List of keys for nested access

        Returns:
            Value or None if not found
        """
        value = d
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
