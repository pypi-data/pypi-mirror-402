# SPEC: StatusLine Configuration UX

**Status:** Draft
**Created:** 2025-12-31
**Author:** Claude Code (based on user requirements)
**Related:** SPEC-statusline-integration-2025-12-31.md

---

## 1. Overview

### 1.1 Purpose

This specification defines the user experience and implementation details for the `ait statusline config` command group, focusing on discoverability and ease of use for the 15+ configuration options in the statusLine system.

### 1.2 Goals

- **Discoverability**: Users can easily find available settings without reading documentation
- **Ease of Use**: Simple commands for common tasks (list, get, set)
- **Power User Support**: Advanced features (fzf, tab completion, batch editing)
- **Safety**: Validation, previews, and confirmations before applying changes
- **Consistency**: Follows aiterm CLI patterns and Typer conventions

### 1.3 Non-Goals

- GUI configuration interface
- Web-based configuration
- Real-time preview of statusLine changes (future enhancement)

---

## 2. User Stories

### 2.1 New User Exploring

**As a** new aiterm user
**I want to** see what statusLine settings are available
**So that** I can customize my statusLine without reading full documentation

**Acceptance Criteria:**
- Running `ait statusline config` with no arguments shows an interactive menu
- Menu groups settings by category (display, git, project, usage, theme, time)
- Each setting shows its current value and data type
- User can navigate with arrow keys and select with Enter
- Selecting a setting allows immediate editing

### 2.2 Power User Tweaking

**As a** power user familiar with statusLine
**I want to** quickly find and change a specific setting
**So that** I can adjust configuration without navigating menus

**Acceptance Criteria:**
- `ait statusline config set <key> <value>` works for direct changes
- Tab completion suggests available keys with current values
- fzf fuzzy search available via `--interactive` flag
- Changes are validated before applying
- Invalid values show helpful error messages

### 2.3 Batch Configuration

**As a** user setting up statusLine for the first time
**I want to** configure multiple settings at once
**So that** I don't have to run commands repeatedly

**Acceptance Criteria:**
- `ait statusline config wizard` guides through initial setup
- `ait statusline config edit` opens full config in editor
- Changes are validated after editing
- User can preview changes before applying

### 2.4 Discovery by Listing

**As a** user who prefers CLI output
**I want to** see all settings in a table format
**So that** I can review configuration without interaction

**Acceptance Criteria:**
- `ait statusline config list` shows all settings in Rich table
- Table includes: key, current value, type, description
- `--category` flag filters by category (display, git, etc.)
- `--format json` outputs machine-readable format
- Output fits terminal width (responsive table)

---

## 3. Architecture

### 3.1 Command Structure

```
ait statusline config
├── list [--category] [--format]     # List all settings
├── get <key>                         # Get single value
├── set <key> <value> [--interactive] # Set single value
├── reset [<key>]                     # Reset to defaults
├── edit                              # Open in editor
├── wizard                            # Interactive setup
└── validate                          # Validate current config
```

### 3.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ait statusline config                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐   ┌──────────┐
    │   list   │    │   set    │   │  wizard  │
    └────┬─────┘    └────┬─────┘   └────┬─────┘
         │               │              │
         ▼               ▼              ▼
    ┌─────────────────────────────────────────┐
    │       StatusLineConfig (Python)         │
    ├─────────────────────────────────────────┤
    │ - load()                                │
    │ - save(config)                          │
    │ - get(key, default)                     │
    │ - set(key, value)                       │
    │ - validate()                            │
    │ - get_schema()                          │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   ~/.config/aiterm/statusline.json      │
    └─────────────────────────────────────────┘
```

### 3.3 Data Flow

```
User Command
    │
    ▼
Typer CLI Parser
    │
    ▼
StatusLineConfig.load()
    │
    ├─► Validate schema
    ├─► Apply defaults
    └─► Return config dict
    │
    ▼
Command Handler
    │
    ├─► list: Format as table
    ├─► set: Validate + save
    ├─► wizard: Interactive prompts
    └─► edit: Open editor + validate
    │
    ▼
StatusLineConfig.save()
    │
    └─► Write JSON to disk
```

---

## 4. API Design

### 4.1 Python API

#### 4.1.1 StatusLineConfig Class

```python
# src/aiterm/statusline/config.py

from pathlib import Path
from typing import Any, Optional
import json

class StatusLineConfig:
    """Manages statusLine configuration."""

    def __init__(self):
        self.config_path = Path.home() / ".config/aiterm/statusline.json"
        self._schema = self._load_schema()
        self._config = None

    def load(self) -> dict:
        """Load config with defaults."""
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            self._config = self._get_defaults()
            return self._config

        with open(self.config_path) as f:
            user_config = json.load(f)

        # Merge with defaults
        defaults = self._get_defaults()
        self._config = self._deep_merge(defaults, user_config)
        return self._config

    def save(self, config: dict) -> None:
        """Save config to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

        self._config = config

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with dot notation.

        Example:
            config.get("display.show_git")  # Returns bool
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
        """
        config = self.load()

        # Validate
        if not self._validate_value(key, value):
            raise ValueError(f"Invalid value for {key}: {value}")

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
        """Reset to defaults."""
        if key is None:
            # Reset entire config
            self.save(self._get_defaults())
        else:
            # Reset single key
            defaults = self._get_defaults()
            default_value = self._get_nested(defaults, key.split('.'))
            self.set(key, default_value)

    def validate(self) -> tuple[bool, list[str]]:
        """Validate current config.

        Returns:
            (is_valid, error_messages)
        """
        config = self.load()
        errors = []

        for key, schema_def in self._schema.items():
            value = self.get(key)

            if not self._validate_value(key, value):
                errors.append(f"{key}: expected {schema_def['type']}, got {type(value).__name__}")

        return (len(errors) == 0, errors)

    def get_schema(self) -> dict:
        """Get configuration schema.

        Returns dict with keys:
            - type: str, bool, int, list
            - default: default value
            - description: human-readable description
            - category: grouping (display, git, project, etc.)
        """
        return self._schema

    def list_settings(self, category: Optional[str] = None) -> list[dict]:
        """List all settings with metadata.

        Returns list of dicts:
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
        """Load configuration schema."""
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
            'time.time_format': {
                'type': 'str',
                'default': '24h',
                'choices': ['24h', '12h'],
                'description': 'Time format',
                'category': 'time'
            }
        }

    def _get_defaults(self) -> dict:
        """Generate default config from schema."""
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
        """Validate value against schema."""
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
        """Deep merge two dicts."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _get_nested(self, d: dict, keys: list[str]) -> Any:
        """Get nested value from dict."""
        value = d
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
```

#### 4.1.2 Interactive Menu Helper

```python
# src/aiterm/statusline/interactive.py

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from typing import Optional

class InteractiveConfigMenu:
    """Interactive configuration menu."""

    def __init__(self, config: 'StatusLineConfig'):
        self.config = config
        self.console = Console()

    def run(self, category: Optional[str] = None) -> None:
        """Run interactive menu."""
        while True:
            settings = self.config.list_settings(category=category)

            # Display settings table
            table = self._create_table(settings)
            self.console.print(table)

            # Prompt for selection
            self.console.print("\n[bold]Select a setting to edit (number), or 'q' to quit:[/]")
            choice = Prompt.ask("Choice", default="q")

            if choice.lower() == 'q':
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(settings):
                    self._edit_setting(settings[idx])
                else:
                    self.console.print("[red]Invalid selection[/]")
            except ValueError:
                self.console.print("[red]Invalid input[/]")

    def _create_table(self, settings: list[dict]) -> Table:
        """Create settings table."""
        table = Table(title="StatusLine Configuration", show_header=True)

        table.add_column("#", style="dim", width=3)
        table.add_column("Setting", style="cyan")
        table.add_column("Current Value", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Description")

        for idx, setting in enumerate(settings, 1):
            table.add_row(
                str(idx),
                setting['key'],
                str(setting['value']),
                setting['type'],
                setting['description']
            )

        return table

    def _edit_setting(self, setting: dict) -> None:
        """Edit a single setting."""
        key = setting['key']
        current = setting['value']
        schema_def = self.config.get_schema()[key]

        self.console.print(f"\n[bold]Editing:[/] {key}")
        self.console.print(f"[dim]Description: {setting['description']}[/]")
        self.console.print(f"[dim]Current value: {current}[/]")

        if setting['type'] == 'bool':
            new_value = Confirm.ask("Enable?", default=current)
        elif 'choices' in schema_def:
            choices_str = ", ".join(schema_def['choices'])
            self.console.print(f"[dim]Choices: {choices_str}[/]")
            new_value = Prompt.ask("New value", choices=schema_def['choices'], default=str(current))
        elif setting['type'] == 'int':
            while True:
                try:
                    new_value = int(Prompt.ask("New value", default=str(current)))
                    break
                except ValueError:
                    self.console.print("[red]Please enter a valid integer[/]")
        else:
            new_value = Prompt.ask("New value", default=str(current))

        # Confirm change
        if new_value != current:
            if Confirm.ask(f"Change {key} from {current} to {new_value}?", default=True):
                try:
                    self.config.set(key, new_value)
                    self.console.print("[green]✓ Setting updated[/]")
                except ValueError as e:
                    self.console.print(f"[red]Error: {e}[/]")
```

### 4.2 CLI Commands

#### 4.2.1 Main Config Command

```python
# src/aiterm/cli/statusline.py (extending existing)

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
import subprocess

from aiterm.statusline.config import StatusLineConfig
from aiterm.statusline.interactive import InteractiveConfigMenu

config_app = typer.Typer(name="config", help="Manage statusLine configuration")
console = Console()

@config_app.callback(invoke_without_command=True)
def config_main(
    ctx: typer.Context,
):
    """
    Manage statusLine configuration.

    When run without a subcommand, opens interactive menu.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand - run interactive menu
        config = StatusLineConfig()
        menu = InteractiveConfigMenu(config)
        menu.run()

@config_app.command(
    "list",
    epilog="""
[bold]Examples:[/]
  ait statusline config list                # List all settings
  ait statusline config list --category git # List only git settings
  ait statusline config list --format json  # JSON output
"""
)
def config_list(
    category: Optional[str] = typer.Option(
        None,
        "--category", "-c",
        help="Filter by category (display, git, project, usage, theme, time)"
    ),
    format: str = typer.Option(
        "table",
        "--format", "-f",
        help="Output format (table, json)"
    )
):
    """List all configuration settings."""
    config = StatusLineConfig()
    settings = config.list_settings(category=category)

    if format == "json":
        import json
        output = {s['key']: s['value'] for s in settings}
        console.print_json(data=output)
    else:
        # Table format
        table = Table(title=f"StatusLine Configuration{f' ({category})' if category else ''}")

        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Description")

        for s in settings:
            table.add_row(
                s['key'],
                str(s['value']),
                s['type'],
                s['description']
            )

        console.print(table)

        # Show categories available
        if not category:
            categories = sorted(set(s['category'] for s in settings))
            console.print(f"\n[dim]Categories: {', '.join(categories)}[/]")
            console.print("[dim]Use --category to filter[/]")

@config_app.command(
    "get",
    epilog="""
[bold]Examples:[/]
  ait statusline config get display.show_git
  ait statusline config get theme.name
"""
)
def config_get(
    key: str = typer.Argument(..., help="Setting key (use dot notation)")
):
    """Get a single configuration value."""
    config = StatusLineConfig()

    value = config.get(key)
    if value is None:
        console.print(f"[red]Setting not found: {key}[/]")
        raise typer.Exit(1)

    console.print(f"[cyan]{key}[/] = [green]{value}[/]")

@config_app.command(
    "set",
    epilog="""
[bold]Examples:[/]
  ait statusline config set display.show_git false
  ait statusline config set theme.name cool-blues
  ait statusline config set --interactive  # Browse settings
"""
)
def config_set(
    key: Optional[str] = typer.Argument(None, help="Setting key (use dot notation)"),
    value: Optional[str] = typer.Argument(None, help="New value"),
    interactive: bool = typer.Option(
        False,
        "--interactive", "-i",
        help="Use fzf to select setting"
    )
):
    """Set a configuration value."""
    config = StatusLineConfig()

    if interactive or key is None:
        # Interactive mode - use fzf
        settings = config.list_settings()

        # Create fzf input
        fzf_lines = []
        for s in settings:
            fzf_lines.append(f"{s['key']} = {s['value']} ({s['type']}) - {s['description']}")

        try:
            result = subprocess.run(
                ['fzf', '--prompt', 'Select setting: ', '--height', '40%'],
                input='\n'.join(fzf_lines),
                capture_output=True,
                text=True,
                check=True
            )

            # Parse selected line
            selected_line = result.stdout.strip()
            key = selected_line.split(' = ')[0]

            # Now get the value
            schema_def = config.get_schema()[key]
            current = config.get(key)

            if schema_def['type'] == 'bool':
                from rich.prompt import Confirm
                value = Confirm.ask(f"Enable {key}?", default=current)
            elif 'choices' in schema_def:
                from rich.prompt import Prompt
                choices_str = ", ".join(schema_def['choices'])
                console.print(f"[dim]Choices: {choices_str}[/]")
                value = Prompt.ask("New value", choices=schema_def['choices'], default=str(current))
            else:
                from rich.prompt import Prompt
                value = Prompt.ask(f"New value for {key}", default=str(current))

        except subprocess.CalledProcessError:
            console.print("[yellow]Cancelled[/]")
            raise typer.Exit(0)
        except FileNotFoundError:
            console.print("[red]fzf not found. Install with: brew install fzf[/]")
            raise typer.Exit(1)

    if key is None or value is None:
        console.print("[red]Error: key and value required[/]")
        raise typer.Exit(1)

    # Parse value based on type
    schema_def = config.get_schema().get(key)
    if not schema_def:
        console.print(f"[red]Unknown setting: {key}[/]")
        raise typer.Exit(1)

    # Type conversion
    if schema_def['type'] == 'bool':
        value = value.lower() in ('true', '1', 'yes', 'on')
    elif schema_def['type'] == 'int':
        try:
            value = int(value)
        except ValueError:
            console.print(f"[red]Invalid integer: {value}[/]")
            raise typer.Exit(1)

    # Validate and set
    try:
        old_value = config.get(key)
        config.set(key, value)
        console.print(f"[green]✓[/] {key}: [dim]{old_value}[/] → [green]{value}[/]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)

@config_app.command(
    "reset",
    epilog="""
[bold]Examples:[/]
  ait statusline config reset                    # Reset entire config
  ait statusline config reset display.show_git   # Reset single setting
"""
)
def config_reset(
    key: Optional[str] = typer.Argument(None, help="Setting key to reset (or all if not specified)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Reset configuration to defaults."""
    config = StatusLineConfig()

    if key:
        msg = f"Reset {key} to default?"
    else:
        msg = "Reset entire configuration to defaults?"

    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(msg, default=False):
            console.print("[yellow]Cancelled[/]")
            raise typer.Exit(0)

    config.reset(key)

    if key:
        new_value = config.get(key)
        console.print(f"[green]✓[/] {key} reset to [green]{new_value}[/]")
    else:
        console.print("[green]✓[/] Configuration reset to defaults")

@config_app.command(
    "edit",
    epilog="""
[bold]Examples:[/]
  ait statusline config edit  # Open config in $EDITOR
"""
)
def config_edit():
    """Open configuration file in editor."""
    import os
    config = StatusLineConfig()

    # Ensure file exists
    if not config.config_path.exists():
        config.save(config.load())

    editor = os.environ.get('EDITOR', 'vim')

    try:
        subprocess.run([editor, str(config.config_path)], check=True)

        # Validate after editing
        is_valid, errors = config.validate()

        if not is_valid:
            console.print("[red]Configuration errors detected:[/]")
            for error in errors:
                console.print(f"  [red]•[/] {error}")

            from rich.prompt import Confirm
            if Confirm.ask("Errors found. Reset to last valid config?", default=True):
                config.reset()
                console.print("[green]✓[/] Configuration reset")
        else:
            console.print("[green]✓[/] Configuration valid")

    except subprocess.CalledProcessError:
        console.print("[red]Editor exited with error[/]")
        raise typer.Exit(1)

@config_app.command(
    "wizard",
    epilog="""
[bold]Examples:[/]
  ait statusline config wizard  # Interactive setup
"""
)
def config_wizard():
    """Interactive configuration wizard."""
    from rich.prompt import Prompt, Confirm

    config = StatusLineConfig()
    console.print("[bold cyan]StatusLine Configuration Wizard[/]\n")

    # Display options
    console.print("What information do you want in your statusLine?\n")

    categories = {
        'display': [
            'display.show_git',
            'display.show_thinking_indicator',
            'display.show_session_duration',
            'display.show_current_time',
            'display.show_lines_changed',
            'display.show_session_usage',
            'display.show_weekly_usage'
        ],
        'git': [
            'git.show_ahead_behind',
            'git.show_untracked_count',
            'git.show_stash_count'
        ],
        'theme': [
            'theme.name'
        ]
    }

    changes = []

    for category, keys in categories.items():
        console.print(f"\n[bold]{category.title()}[/]")

        for key in keys:
            schema_def = config.get_schema()[key]
            description = schema_def['description']
            current = config.get(key)

            if schema_def['type'] == 'bool':
                value = Confirm.ask(f"  {description}?", default=current)
            elif 'choices' in schema_def:
                choices = schema_def['choices']
                console.print(f"  {description}")
                value = Prompt.ask("  Choose", choices=choices, default=str(current))
            else:
                continue

            if value != current:
                changes.append((key, value))

    # Preview changes
    if changes:
        console.print("\n[bold]Preview changes:[/]")
        table = Table()
        table.add_column("Setting")
        table.add_column("Old")
        table.add_column("New")

        for key, new_value in changes:
            old_value = config.get(key)
            table.add_row(key, str(old_value), str(new_value))

        console.print(table)

        if Confirm.ask("\nApply changes?", default=True):
            for key, value in changes:
                config.set(key, value)
            console.print(f"[green]✓[/] Applied {len(changes)} changes")
        else:
            console.print("[yellow]Cancelled[/]")
    else:
        console.print("\n[dim]No changes made[/]")

@config_app.command(
    "validate",
    epilog="""
[bold]Examples:[/]
  ait statusline config validate  # Check config file
"""
)
def config_validate():
    """Validate configuration file."""
    config = StatusLineConfig()

    is_valid, errors = config.validate()

    if is_valid:
        console.print("[green]✓[/] Configuration is valid")
    else:
        console.print("[red]Configuration errors:[/]")
        for error in errors:
            console.print(f"  [red]•[/] {error}")
        raise typer.Exit(1)
```

### 4.3 Tab Completion

```bash
# completions/_ait_statusline_config.zsh

#compdef ait

_ait_statusline_config_keys() {
    local keys=(
        'display.directory_mode:Directory display mode (smart|basename|full)'
        'display.show_git:Show git information (bool)'
        'display.show_thinking_indicator:Show thinking mode indicator (bool)'
        'display.show_output_style:When to show output style (auto|always|never)'
        'display.show_session_duration:Show session duration (bool)'
        'display.show_current_time:Show current time (bool)'
        'display.show_lines_changed:Show lines added/removed (bool)'
        'display.show_r_version:Show R package version (bool)'
        'display.show_session_usage:Show session usage stats (bool)'
        'display.show_weekly_usage:Show weekly usage stats (bool)'
        'display.max_directory_length:Max directory name length (int)'
        'usage.show_reset_timer:Show time until usage reset (bool)'
        'usage.warning_threshold:Usage warning threshold % (int)'
        'usage.compact_format:Use compact usage display (bool)'
        'theme.name:Color theme (purple-charcoal|cool-blues|forest-greens)'
        'git.show_ahead_behind:Show ahead/behind indicators (bool)'
        'git.show_untracked_count:Show untracked file count (bool)'
        'git.show_stash_count:Show stash count (bool)'
        'git.show_remote_status:Show remote tracking branch (bool)'
        'git.truncate_branch_length:Max branch name length (int)'
        'project.detect_python_env:Show Python environment (bool)'
        'project.detect_node_version:Show Node.js version (bool)'
        'project.detect_r_package_health:Show R package health (bool)'
        'project.show_dependency_warnings:Show outdated dependency warnings (bool)'
        'time.session_duration_format:Session duration format (compact|verbose)'
        'time.show_productivity_indicator:Show activity level indicator (bool)'
        'time.time_format:Time format (24h|12h)'
    )

    _describe 'config keys' keys
}

_ait_statusline_config_categories() {
    local categories=(
        'display:Display settings'
        'usage:Usage tracking settings'
        'theme:Theme settings'
        'git:Git settings'
        'project:Project detection settings'
        'time:Time display settings'
    )

    _describe 'categories' categories
}

_ait_statusline_config() {
    local -a commands

    commands=(
        'list:List all configuration settings'
        'get:Get a single configuration value'
        'set:Set a configuration value'
        'reset:Reset configuration to defaults'
        'edit:Open configuration file in editor'
        'wizard:Interactive configuration wizard'
        'validate:Validate configuration file'
    )

    case $CURRENT in
        2)
            _describe 'commands' commands
            ;;
        3)
            case $words[2] in
                list)
                    _arguments \
                        '--category[Filter by category]:category:_ait_statusline_config_categories' \
                        '--format[Output format]:format:(table json)'
                    ;;
                get|reset)
                    _ait_statusline_config_keys
                    ;;
                set)
                    if [[ $CURRENT -eq 3 ]]; then
                        _ait_statusline_config_keys
                    fi
                    ;;
            esac
            ;;
    esac
}
```

---

## 5. UI/UX Specifications

### 5.1 Interactive Menu (No Args)

**Command:** `ait statusline config`

**Display:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━ StatusLine Configuration ━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  #  Setting                           Value    Type   Description          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│  1  display.directory_mode            smart    str    Directory display..  │
│  2  display.show_git                  True     bool   Show git informati.. │
│  3  display.show_thinking_indicator   True     bool   Show thinking mode.. │
│  4  display.show_output_style         auto     str    When to show outpu.. │
│  5  display.show_session_duration     True     bool   Show session durat.. │
│  6  display.show_current_time         True     bool   Show current time    │
│  7  display.show_lines_changed        True     bool   Show lines added/..  │
│  8  display.show_r_version            True     bool   Show R package ver.. │
│  9  display.show_session_usage        True     bool   Show session usage.. │
│ 10  display.show_weekly_usage         True     bool   Show weekly usage..  │
│ 11  display.max_directory_length      50       int    Max directory name.. │
│ 12  usage.show_reset_timer            True     bool   Show time until u..  │
│ 13  usage.warning_threshold           80       int    Usage warning thre.. │
│ 14  usage.compact_format              True     bool   Use compact usage..  │
│ 15  theme.name                        purple.. str    Color theme          │
│ 16  git.show_ahead_behind             True     bool   Show ahead/behind..  │
│ 17  git.show_untracked_count          True     bool   Show untracked fil.. │
│ 18  git.show_stash_count              False    bool   Show stash count     │
│ 19  git.show_remote_status            False    bool   Show remote tracki.. │
│ 20  git.truncate_branch_length        32       int    Max branch name l..  │
└──────────────────────────────────────────────────────────────────────────────┘

Select a setting to edit (number), or 'q' to quit:
```

**Interaction flow:**
1. User enters number (1-20)
2. Show edit prompt for that setting:
   ```
   Editing: display.show_git
   Description: Show git information
   Current value: True
   Enable? [Y/n]:
   ```
3. After change, return to menu with updated value
4. User can continue editing or press 'q' to quit

### 5.2 List Command

**Command:** `ait statusline config list`

**Output:** (Same table as interactive mode, but non-interactive)

**With category filter:**
```bash
ait statusline config list --category git
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━ StatusLine Configuration (git) ━━━━━━━━━━━━━━━━━━━┓
┃ Setting                      Value   Type   Description                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ git.show_ahead_behind        True    bool   Show ahead/behind indicators     │
│ git.show_untracked_count     True    bool   Show untracked file count        │
│ git.show_stash_count         False   bool   Show stash count                 │
│ git.show_remote_status       False   bool   Show remote tracking branch      │
│ git.truncate_branch_length   32      int    Max branch name length           │
└──────────────────────────────────────────────────────────────────────────────┘

Categories: display, usage, theme, git, project, time
Use --category to filter
```

### 5.3 Get Command

**Command:** `ait statusline config get display.show_git`

**Output:**
```
display.show_git = True
```

### 5.4 Set Command (Direct)

**Command:** `ait statusline config set display.show_git false`

**Output:**
```
✓ display.show_git: True → false
```

### 5.5 Set Command (Interactive with fzf)

**Command:** `ait statusline config set --interactive`

**fzf interface:**
```
  display.directory_mode = smart (str) - Directory display mode
  display.show_git = True (bool) - Show git information
> display.show_thinking_indicator = True (bool) - Show thinking mode indicator
  display.show_output_style = auto (str) - When to show output style
  ...

  20/25
> Select setting: _
```

**After selection (e.g., display.show_git):**
```
Enable display.show_git? [Y/n]:
```

**After confirmation:**
```
✓ display.show_git: True → False
```

### 5.6 Reset Command

**Command:** `ait statusline config reset display.show_git`

**Output:**
```
✓ display.show_git reset to True
```

**Reset all:**
```bash
ait statusline config reset
```

**Output:**
```
Reset entire configuration to defaults? [y/N]: y
✓ Configuration reset to defaults
```

### 5.7 Edit Command

**Command:** `ait statusline config edit`

**Behavior:**
1. Opens `~/.config/aiterm/statusline.json` in `$EDITOR`
2. After closing editor, validates JSON
3. If invalid:
   ```
   Configuration errors detected:
     • display.show_git: expected bool, got str

   Errors found. Reset to last valid config? [Y/n]:
   ```

### 5.8 Wizard Command

**Command:** `ait statusline config wizard`

**Output:**
```
StatusLine Configuration Wizard

What information do you want in your statusLine?

Display
  Show git information? [Y/n]: y
  Show thinking mode indicator? [Y/n]: y
  Show session duration? [Y/n]: y
  Show current time? [Y/n]: n
  Show lines changed? [Y/n]: y
  Show session usage stats? [Y/n]: y
  Show weekly usage stats? [Y/n]: y

Git
  Show ahead/behind indicators? [Y/n]: y
  Show untracked file count? [Y/n]: y
  Show stash count? [y/N]: n

Theme
  Color theme
  Choose (purple-charcoal/cool-blues/forest-greens) [purple-charcoal]:

Preview changes:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting                      Old    New            ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ display.show_current_time    True   False          │
└─────────────────────────────────────────────────────┘

Apply changes? [Y/n]: y
✓ Applied 1 changes
```

### 5.9 Tab Completion Examples

**Typing:** `ait statusline config set <TAB>`

**Completion shows:**
```
display.directory_mode       -- Directory display mode (smart|basename|full)
display.show_git             -- Show git information (bool)
display.show_thinking_ind... -- Show thinking mode indicator (bool)
...
```

**Typing:** `ait statusline config set display.<TAB>`

**Completion shows:**
```
display.directory_mode           -- Directory display mode (smart|basename|full)
display.show_git                 -- Show git information (bool)
display.show_thinking_indicator  -- Show thinking mode indicator (bool)
display.show_output_style        -- When to show output style (auto|always|never)
display.show_session_duration    -- Show session duration (bool)
display.show_current_time        -- Show current time (bool)
display.show_lines_changed       -- Show lines added/removed (bool)
display.show_r_version           -- Show R package version (bool)
display.show_session_usage       -- Show session usage stats (bool)
display.show_weekly_usage        -- Show weekly usage stats (bool)
display.max_directory_length     -- Max directory name length (int)
```

---

## 6. Error Handling

### 6.1 Invalid Key

**Command:** `ait statusline config get invalid.key`

**Output:**
```
Setting not found: invalid.key
```

**Exit code:** 1

### 6.2 Invalid Value Type

**Command:** `ait statusline config set display.show_git not_a_bool`

**Output:**
```
Error: Invalid value for display.show_git: not_a_bool
Expected: bool (true/false)
```

**Exit code:** 1

### 6.3 Invalid Choice

**Command:** `ait statusline config set theme.name invalid-theme`

**Output:**
```
Error: Invalid value for theme.name: invalid-theme
Valid choices: purple-charcoal, cool-blues, forest-greens
```

**Exit code:** 1

### 6.4 Invalid JSON in Config File

**Scenario:** User manually edits config file and introduces JSON syntax error

**Command:** `ait statusline config list`

**Output:**
```
Error: Invalid JSON in config file
/Users/dt/.config/aiterm/statusline.json

Details: Expecting ',' delimiter: line 5 column 3

Would you like to reset to defaults? [y/N]:
```

### 6.5 Missing fzf for Interactive Mode

**Command:** `ait statusline config set --interactive`

**Output:**
```
fzf not found. Install with: brew install fzf
```

**Exit code:** 1

---

## 7. Dependencies

### 7.1 Python Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| typer | ≥0.9.0 | CLI framework |
| rich | ≥13.0.0 | Terminal formatting |
| pathlib | stdlib | Path handling |
| json | stdlib | JSON parsing |
| subprocess | stdlib | Running external tools |

### 7.2 External Tools (Optional)

| Tool | Purpose | Fallback |
|------|---------|----------|
| fzf | Interactive setting selection | Menu-based selection |

### 7.3 System Requirements

- Python 3.10+
- macOS, Linux, or WSL2

---

## 8. Testing Strategy

### 8.1 Unit Tests

**File:** `tests/test_statusline_config.py`

```python
def test_config_load_defaults():
    """Test loading default configuration."""
    config = StatusLineConfig()
    data = config.load()

    assert data['display']['show_git'] == True
    assert data['theme']['name'] == 'purple-charcoal'

def test_config_get_nested():
    """Test getting nested values with dot notation."""
    config = StatusLineConfig()

    assert config.get('display.show_git') == True
    assert config.get('theme.name') == 'purple-charcoal'

def test_config_set_valid():
    """Test setting valid values."""
    config = StatusLineConfig()

    config.set('display.show_git', False)
    assert config.get('display.show_git') == False

def test_config_set_invalid_type():
    """Test setting invalid type raises error."""
    config = StatusLineConfig()

    with pytest.raises(ValueError):
        config.set('display.show_git', 'not_a_bool')

def test_config_set_invalid_choice():
    """Test setting invalid choice raises error."""
    config = StatusLineConfig()

    with pytest.raises(ValueError):
        config.set('theme.name', 'invalid-theme')

def test_config_reset_single():
    """Test resetting single setting."""
    config = StatusLineConfig()

    config.set('display.show_git', False)
    config.reset('display.show_git')

    assert config.get('display.show_git') == True

def test_config_reset_all():
    """Test resetting entire config."""
    config = StatusLineConfig()

    config.set('display.show_git', False)
    config.set('theme.name', 'cool-blues')
    config.reset()

    assert config.get('display.show_git') == True
    assert config.get('theme.name') == 'purple-charcoal'

def test_config_validate():
    """Test configuration validation."""
    config = StatusLineConfig()

    is_valid, errors = config.validate()
    assert is_valid == True
    assert errors == []

def test_config_list_settings():
    """Test listing all settings."""
    config = StatusLineConfig()

    settings = config.list_settings()

    assert len(settings) > 0
    assert all('key' in s for s in settings)
    assert all('value' in s for s in settings)

def test_config_list_settings_by_category():
    """Test listing settings filtered by category."""
    config = StatusLineConfig()

    git_settings = config.list_settings(category='git')

    assert all(s['category'] == 'git' for s in git_settings)
    assert len(git_settings) == 5  # 5 git settings
```

### 8.2 CLI Integration Tests

**File:** `tests/test_statusline_config_cli.py`

```python
from typer.testing import CliRunner
from aiterm.cli.statusline import config_app

runner = CliRunner()

def test_config_list():
    """Test config list command."""
    result = runner.invoke(config_app, ["list"])

    assert result.exit_code == 0
    assert "display.show_git" in result.stdout

def test_config_get():
    """Test config get command."""
    result = runner.invoke(config_app, ["get", "display.show_git"])

    assert result.exit_code == 0
    assert "True" in result.stdout

def test_config_set():
    """Test config set command."""
    result = runner.invoke(config_app, ["set", "display.show_git", "false"])

    assert result.exit_code == 0
    assert "✓" in result.stdout

def test_config_reset():
    """Test config reset command."""
    # First change a value
    runner.invoke(config_app, ["set", "display.show_git", "false"])

    # Then reset
    result = runner.invoke(config_app, ["reset", "display.show_git"], input="y\n")

    assert result.exit_code == 0
    assert "✓" in result.stdout

def test_config_validate():
    """Test config validate command."""
    result = runner.invoke(config_app, ["validate"])

    assert result.exit_code == 0
    assert "valid" in result.stdout.lower()
```

### 8.3 Test Coverage Goals

- Unit tests: ≥90% coverage for `StatusLineConfig` class
- CLI tests: All commands tested with happy path + error cases
- Integration tests: End-to-end workflows (wizard, edit, etc.)

---

## 9. Implementation Phases

### Phase 1: Core Config System (Week 1)

**Tasks:**
1. Create `StatusLineConfig` class with schema
2. Implement `load()`, `save()`, `get()`, `set()` methods
3. Add validation logic
4. Write 15 unit tests

**Deliverable:** Config system working, tests passing

### Phase 2: List Command (Week 1)

**Tasks:**
1. Implement `config list` command
2. Add category filtering
3. Add JSON output format
4. Style with Rich tables

**Deliverable:** `ait statusline config list` working

### Phase 3: Get/Set Commands (Week 2)

**Tasks:**
1. Implement `config get <key>`
2. Implement `config set <key> <value>`
3. Add type conversion and validation
4. Add helpful error messages

**Deliverable:** Direct get/set working

### Phase 4: Interactive Menu (Week 2)

**Tasks:**
1. Create `InteractiveConfigMenu` class
2. Implement menu display with Rich tables
3. Add edit prompts for each type
4. Handle menu navigation

**Deliverable:** `ait statusline config` (no args) shows menu

### Phase 5: Advanced Features (Week 3)

**Tasks:**
1. Add fzf integration for `set --interactive`
2. Implement `config edit` with validation
3. Create `config wizard` flow
4. Add `config reset` command

**Deliverable:** All commands working

### Phase 6: Tab Completion (Week 3)

**Tasks:**
1. Write ZSH completion script
2. Document completion installation
3. Test completions in ZSH

**Deliverable:** Tab completion working

---

## 10. Documentation

### 10.1 CLI Help Text

All commands include:
- Short description
- Detailed help with `--help`
- Examples in epilog

### 10.2 User Documentation

**File:** `docs/statusline-config.md`

Sections:
1. Quick Start (list, get, set)
2. Interactive Menu
3. Wizard for First-Time Setup
4. Advanced Usage (edit, fzf)
5. Tab Completion Setup
6. Troubleshooting

### 10.3 Reference Documentation

**File:** `docs/reference/statusline-settings.md`

Table of all settings with:
- Key
- Type
- Default
- Description
- Category
- Valid choices (if applicable)

---

## 11. Acceptance Criteria

### 11.1 Functional

- [ ] `ait statusline config` (no args) shows interactive menu
- [ ] `ait statusline config list` displays all settings in table
- [ ] `ait statusline config list --category git` filters by category
- [ ] `ait statusline config get <key>` returns value
- [ ] `ait statusline config set <key> <value>` updates setting
- [ ] `ait statusline config set --interactive` uses fzf
- [ ] `ait statusline config reset` resets to defaults
- [ ] `ait statusline config edit` opens in editor and validates
- [ ] `ait statusline config wizard` guides through setup
- [ ] `ait statusline config validate` checks config file
- [ ] Tab completion suggests keys with descriptions
- [ ] All invalid inputs show helpful error messages

### 11.2 Non-Functional

- [ ] Config loads in <50ms
- [ ] Interactive menu responsive (<100ms refresh)
- [ ] All operations preserve JSON formatting
- [ ] Config file uses 2-space indentation
- [ ] Error messages include suggested fixes
- [ ] All commands have `--help` with examples

### 11.3 Testing

- [ ] ≥90% unit test coverage for `StatusLineConfig`
- [ ] All CLI commands have integration tests
- [ ] Invalid config files handled gracefully
- [ ] Validation catches all schema violations

---

## 12. Future Enhancements

### 12.1 Preview Mode

**Feature:** Real-time preview of statusLine as you configure

**Implementation:**
- Run `ait statusline render` with test data after each change
- Display preview below menu

### 12.2 Config Profiles

**Feature:** Multiple config profiles (work, minimal, verbose)

**Implementation:**
```bash
ait statusline config profile create work
ait statusline config profile switch minimal
ait statusline config profile list
```

### 12.3 Import/Export

**Feature:** Share configurations

**Implementation:**
```bash
ait statusline config export > my-config.json
ait statusline config import my-config.json
```

### 12.4 Recommended Presets

**Feature:** Curated presets for common use cases

**Implementation:**
```bash
ait statusline config preset apply minimal
ait statusline config preset apply developer
ait statusline config preset apply max-plan-user
```

---

## Appendix A: Configuration Schema Reference

See Section 4.1.1 for full schema definition in `StatusLineConfig._load_schema()`.

**Categories:**
- `display` (11 settings)
- `usage` (3 settings)
- `theme` (1 setting)
- `git` (5 settings)
- `project` (4 settings)
- `time` (3 settings)

**Total:** 27 configurable settings

---

## Appendix B: File Paths

| Path | Purpose |
|------|---------|
| `~/.config/aiterm/statusline.json` | User configuration |
| `src/aiterm/statusline/config.py` | Config class |
| `src/aiterm/statusline/interactive.py` | Interactive menu |
| `src/aiterm/cli/statusline.py` | CLI commands |
| `tests/test_statusline_config.py` | Unit tests |
| `tests/test_statusline_config_cli.py` | CLI tests |
| `completions/_ait_statusline_config.zsh` | ZSH completions |
| `docs/statusline-config.md` | User guide |
| `docs/reference/statusline-settings.md` | Settings reference |

---

**END OF SPECIFICATION**
