"""StatusLine configuration management CLI.

This module provides CLI commands for managing statusLine configuration,
themes, and settings. Part of the statusLine → aiterm integration.
"""

from typing import Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
import subprocess
import os

from aiterm.statusline.config import StatusLineConfig
from aiterm.statusline.interactive import InteractiveConfigMenu
from aiterm.statusline.hooks import StatusLineHooks

app = typer.Typer(
    help="Manage statusLine configuration for Claude Code.",
    no_args_is_help=False,  # Allow running without args to show interactive menu
)
console = Console()

# Config subcommand group
config_app = typer.Typer(name="config", help="Manage statusLine configuration")
app.add_typer(config_app, name="config")

# Theme subcommand group
theme_app = typer.Typer(name="theme", help="Manage statusLine themes")
app.add_typer(theme_app, name="theme")

# Hooks subcommand group (v0.7.0 - Claude Code v2.1+)
hooks_app = typer.Typer(name="hooks", help="Manage statusLine hooks (Claude Code v2.1+)")
app.add_typer(hooks_app, name="hooks")


# =============================================================================
# Config Commands
# =============================================================================


@config_app.callback(invoke_without_command=True)
def config_main(ctx: typer.Context):
    """Manage statusLine configuration.

    When run without a subcommand, opens interactive menu.

    \b
    Examples:
        ait statusline config              # Interactive menu
        ait statusline config list         # List all settings
        ait statusline config get <key>    # Get value
    """
    if ctx.invoked_subcommand is None:
        # No subcommand - run interactive menu
        config = StatusLineConfig()
        menu = InteractiveConfigMenu(config)
        menu.run()


@config_app.command(
    "list",
    epilog="""
\b
Examples:
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
        title = "StatusLine Configuration"
        if category:
            title += f" ({category})"

        table = Table(title=title)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Description")

        for s in settings:
            # Format value for display
            value_str = str(s['value'])
            if isinstance(s['value'], bool):
                value_str = "✓" if s['value'] else "✗"

            table.add_row(
                s['key'],
                value_str,
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
\b
Examples:
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
\b
Examples:
  ait statusline config set display.show_git false
  ait statusline config set theme.name cool-blues
  ait statusline config set --interactive  # Browse settings with fzf
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
            # Format current value
            val_str = str(s['value'])
            if isinstance(s['value'], bool):
                val_str = "✓" if s['value'] else "✗"

            fzf_lines.append(
                f"{s['key']} = {val_str} ({s['type']}) - {s['description']}"
            )

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
                value = Confirm.ask(f"Enable {key}?", default=current)
            elif 'choices' in schema_def:
                choices_str = ", ".join(str(c) for c in schema_def['choices'])
                console.print(f"[dim]Choices: {choices_str}[/]")
                value = Prompt.ask(
                    "New value",
                    choices=[str(c) for c in schema_def['choices']],
                    default=str(current)
                )
            else:
                value = Prompt.ask(f"New value for {key}", default=str(current))

        except subprocess.CalledProcessError:
            console.print("[yellow]Cancelled[/]")
            raise typer.Exit(0)
        except FileNotFoundError:
            console.print("[red]fzf not found. Install with: brew install fzf[/]")
            console.print("[dim]Or use: ait statusline config (without --interactive)[/]")
            raise typer.Exit(1)

    if key is None or value is None:
        console.print("[red]Error: key and value required[/]")
        console.print("[dim]Use: ait statusline config set <key> <value>[/]")
        console.print("[dim]Or:  ait statusline config --interactive[/]")
        raise typer.Exit(1)

    # Parse value based on type
    schema_def = config.get_schema().get(key)
    if not schema_def:
        console.print(f"[red]Unknown setting: {key}[/]")
        console.print("[dim]Use 'ait statusline config list' to see available settings[/]")
        raise typer.Exit(1)

    # Type conversion
    if schema_def['type'] == 'bool':
        if isinstance(value, bool):
            # Already bool (from interactive mode)
            pass
        else:
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
\b
Examples:
  ait statusline config reset                    # Reset entire config
  ait statusline config reset display.show_git   # Reset single setting
"""
)
def config_reset(
    key: Optional[str] = typer.Argument(
        None,
        help="Setting key to reset (or all if not specified)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation"
    )
):
    """Reset configuration to defaults."""
    config = StatusLineConfig()

    if key:
        msg = f"Reset {key} to default?"
    else:
        msg = "Reset entire configuration to defaults?"

    if not force:
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
\b
Examples:
  ait statusline config edit  # Open config in $EDITOR
"""
)
def config_edit():
    """Open configuration file in editor."""
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
\b
Examples:
  ait statusline config wizard  # Interactive setup
"""
)
def config_wizard():
    """Interactive configuration wizard."""
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
                value = Prompt.ask(
                    "  Choose",
                    choices=[str(c) for c in choices],
                    default=str(current)
                )
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
\b
Examples:
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


@config_app.command(
    "preset",
    epilog="""
\b
Examples:
  ait statusline config preset minimal    # Minimal statusLine (no bloat)
  ait statusline config preset default    # Restore default settings
"""
)
def config_preset(
    preset_name: str = typer.Argument(
        ...,
        help="Preset name (minimal, default)"
    )
):
    """Apply configuration preset.

    Presets:
      minimal - Clean statusLine without time-tracking bloat
      default - Restore all default settings
    """
    config = StatusLineConfig()

    presets = {
        'minimal': {
            'display.show_session_duration': False,
            'display.show_current_time': False,
            'display.show_lines_changed': False,
            'display.show_session_usage': False,
            'display.show_weekly_usage': False,
            'usage.show_reset_timer': False,
        },
        'default': {}  # Will trigger full reset
    }

    if preset_name not in presets:
        console.print(f"[red]Unknown preset: {preset_name}[/]")
        console.print("\n[dim]Available presets:[/]")
        for name in presets.keys():
            console.print(f"  • {name}")
        raise typer.Exit(1)

    if preset_name == 'default':
        # Full reset to defaults
        if Confirm.ask("Reset entire configuration to defaults?", default=False):
            config.reset()
            console.print("[green]✓[/] Configuration reset to defaults")
        else:
            console.print("[yellow]Cancelled[/]")
        return

    # Apply preset changes
    changes = presets[preset_name]
    console.print(f"[bold]Applying preset:[/] {preset_name}\n")

    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Old", style="dim")
    table.add_column("New", style="green")

    for key, new_value in changes.items():
        old_value = config.get(key)
        if old_value != new_value:
            table.add_row(key, str(old_value), str(new_value))
            config.set(key, new_value)

    console.print(table)
    console.print(f"\n[green]✓[/] Preset '{preset_name}' applied")
    console.print("\n[dim]Restart Claude Code to see changes[/]")


@config_app.command(
    "spacing",
    epilog="""
\b
Examples:
  ait statusline config spacing minimal    # Tight spacing (15% gap)
  ait statusline config spacing standard   # Balanced spacing (20% gap)
  ait statusline config spacing spacious   # Wide spacing (30% gap)
"""
)
def config_spacing(
    preset_name: str = typer.Argument(
        ...,
        help="Spacing preset (minimal, standard, spacious)"
    )
):
    """Configure gap spacing between left and right segments.

    Presets:
      minimal  - Tight spacing (15% of terminal width, 5-20 char gap)
      standard - Balanced spacing (20% of terminal width, 10-40 char gap)
      spacious - Wide spacing (30% of terminal width, 15-60 char gap)

    The gap creates visual separation between left and right statusLine segments,
    making it easier to distinguish project info from worktree context.
    """
    config = StatusLineConfig()

    valid_presets = ['minimal', 'standard', 'spacious']

    if preset_name not in valid_presets:
        console.print(f"[red]Unknown spacing preset: {preset_name}[/]")
        console.print("\n[dim]Available presets:[/]")
        for name in valid_presets:
            console.print(f"  • {name}")
        raise typer.Exit(1)

    # Get current value
    old_value = config.get('spacing.mode', 'standard')

    # Set new value
    config.set('spacing.mode', preset_name)

    # Show change
    console.print(f"[bold]Spacing preset updated[/]\n")

    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Old", style="dim")
    table.add_column("New", style="green")

    table.add_row("spacing.mode", old_value, preset_name)

    console.print(table)
    console.print(f"\n[green]✓[/] Spacing set to '{preset_name}'")
    console.print("\n[dim]Run 'ait statusline test' to preview the new spacing[/]")


# =============================================================================
# Theme Commands
# =============================================================================


@theme_app.command(
    "list",
    epilog="""
\b
Examples:
  ait statusline theme list  # List all available themes
"""
)
def theme_list():
    """List available themes."""
    from aiterm.statusline.themes import ThemeManager

    config = StatusLineConfig()
    manager = ThemeManager(config)
    themes = manager.list_available_themes()

    # Create table
    table = Table(title="Available Themes")
    table.add_column("Theme", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")

    for theme in themes:
        status = "✓ Active" if theme['active'] else ""
        table.add_row(
            theme['name'],
            status,
            theme['description']
        )

    console.print(table)


@theme_app.command(
    "set",
    epilog="""
\b
Examples:
  ait statusline theme set cool-blues     # Switch to cool-blues theme
  ait statusline theme set purple-charcoal  # Switch to default theme
"""
)
def theme_set(
    name: str = typer.Argument(..., help="Theme name to activate")
):
    """Set active theme."""
    from aiterm.statusline.themes import ThemeManager

    config = StatusLineConfig()
    manager = ThemeManager(config)

    try:
        old_theme = manager.get_current_theme().name
        manager.set_theme(name)
        console.print(f"[green]✓[/] Theme changed: [dim]{old_theme}[/] → [green]{name}[/]")
        console.print("\n[dim]Restart Claude Code to see changes[/]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/]")
        console.print("\n[dim]Use 'ait statusline theme list' to see available themes[/]")
        raise typer.Exit(1)


@theme_app.command(
    "show",
    epilog="""
\b
Examples:
  ait statusline theme show  # Show current theme colors
"""
)
def theme_show():
    """Show current theme colors."""
    from aiterm.statusline.themes import ThemeManager

    config = StatusLineConfig()
    manager = ThemeManager(config)
    theme = manager.get_current_theme()

    console.print(f"[bold]Current Theme:[/] {theme.name}\n")

    # Create color samples table
    table = Table(title="Theme Colors")
    table.add_column("Category", style="cyan")
    table.add_column("Attribute", style="yellow")
    table.add_column("ANSI Code", style="dim")
    table.add_column("Sample")

    # Directory segment
    table.add_row("Directory", "Background", theme.dir_bg, f"\033[{theme.dir_bg}m    \033[0m")
    table.add_row("", "Foreground", theme.dir_fg, f"\033[{theme.dir_fg}m████\033[0m")

    # VCS segment
    table.add_row("VCS", "Clean BG", theme.vcs_clean_bg, f"\033[{theme.vcs_clean_bg}m    \033[0m")
    table.add_row("", "Modified BG", theme.vcs_modified_bg, f"\033[{theme.vcs_modified_bg}m    \033[0m")
    table.add_row("", "Foreground", theme.vcs_fg, f"\033[{theme.vcs_fg}m████\033[0m")

    # Model colors
    table.add_row("Model", "Sonnet", theme.model_sonnet, f"\033[{theme.model_sonnet}m████\033[0m")
    table.add_row("", "Opus", theme.model_opus, f"\033[{theme.model_opus}m████\033[0m")
    table.add_row("", "Haiku", theme.model_haiku, f"\033[{theme.model_haiku}m████\033[0m")

    # Time/duration
    table.add_row("Time", "Time", theme.time_fg, f"\033[{theme.time_fg}m████\033[0m")
    table.add_row("", "Duration", theme.duration_fg, f"\033[{theme.duration_fg}m████\033[0m")

    # Lines changed
    table.add_row("Lines", "Added", theme.lines_added_fg, f"\033[{theme.lines_added_fg}m████\033[0m")
    table.add_row("", "Removed", theme.lines_removed_fg, f"\033[{theme.lines_removed_fg}m████\033[0m")

    # UI elements
    table.add_row("UI", "Separator", theme.separator_fg, f"\033[{theme.separator_fg}m████\033[0m")
    table.add_row("", "Thinking", theme.thinking_fg, f"\033[{theme.thinking_fg}m████\033[0m")
    table.add_row("", "Style", theme.style_fg, f"\033[{theme.style_fg}m████\033[0m")

    console.print(table)


# =============================================================================
# Hooks Commands (v0.7.0 - Claude Code v2.1+)
# =============================================================================


@hooks_app.command(
    "list",
    epilog="""
\b
Examples:
  ait statusline hooks list           # Show available templates
  ait statusline hooks list --installed # Show installed hooks
"""
)
def hooks_list(
    installed: bool = typer.Option(
        False,
        "--installed",
        help="Show installed hooks instead of templates"
    )
):
    """List available or installed hook templates."""
    if installed:
        # Show installed hooks
        hooks = StatusLineHooks.list_installed()
        if not hooks:
            console.print("[yellow]No hooks installed yet[/]")
            console.print("\nUse [bold]ait statusline hooks add <name>[/] to install a hook")
            return

        console.print("\n[bold]Installed StatusLine Hooks:[/]\n")
        table = Table(title="StatusLine Hooks")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Enabled", style="green")
        table.add_column("Description")

        for hook in hooks:
            enabled = "[green]✓[/]" if hook.get("enabled") else "[red]✗[/]"
            table.add_row(
                hook["name"],
                hook.get("type", "unknown"),
                enabled,
                hook.get("description", "")
            )

        console.print(table)
    else:
        # Show available templates
        console.print("\n[bold]Available StatusLine Hook Templates:[/]\n")

        templates = StatusLineHooks.TEMPLATES
        for name, template in templates.items():
            enabled_mark = " [green]✓ enabled[/]" if template.get("enabled", True) else " [red]✗ disabled[/]"
            console.print(f"[bold cyan]{name}{enabled_mark}[/]")
            console.print(f"  Type: {template['hook_type']}")
            console.print(f"  {template['description']}")
            console.print()

        console.print("[dim]Use 'ait statusline hooks add <name>' to install a hook[/]")


@hooks_app.command(
    "add",
    epilog="""
\b
Examples:
  ait statusline hooks add on-theme-change    # Install theme change hook
  ait statusline hooks add on-remote-session  # Install remote session hook
"""
)
def hooks_add(
    name: str = typer.Argument(..., help="Hook template name")
):
    """Install a hook template."""
    # Validate
    valid, error = StatusLineHooks.validate_template(name)
    if not valid:
        console.print(f"[red]✗[/] {error}")
        raise typer.Exit(1)

    # Confirm installation
    template = StatusLineHooks.get_template(name)
    console.print(f"\n[bold]Installing: {name}[/]")
    console.print(f"Type: {template['hook_type']}")
    console.print(f"{template['description']}")
    console.print()

    if not Confirm.ask("Install this hook?", default=True):
        console.print("[yellow]Cancelled[/]")
        return

    # Install
    success, message = StatusLineHooks.install_template(name, enable=True)
    if success:
        console.print(f"[green]✓[/] {message}")
    else:
        console.print(f"[red]✗[/] {message}")
        raise typer.Exit(1)


@hooks_app.command(
    "remove",
    epilog="""
\b
Examples:
  ait statusline hooks remove on-theme-change
"""
)
def hooks_remove(
    name: str = typer.Argument(..., help="Hook name to remove")
):
    """Remove an installed hook."""
    if not Confirm.ask(f"Remove hook '{name}'?", default=False):
        console.print("[yellow]Cancelled[/]")
        return

    success, message = StatusLineHooks.uninstall_template(name)
    if success:
        console.print(f"[green]✓[/] {message}")
    else:
        console.print(f"[red]✗[/] {message}")
        raise typer.Exit(1)


@hooks_app.command(
    "enable",
    epilog="""
\b
Examples:
  ait statusline hooks enable on-error
"""
)
def hooks_enable(
    name: str = typer.Argument(..., help="Hook name to enable")
):
    """Enable a hook."""
    success, message = StatusLineHooks.enable_hook(name)
    if success:
        console.print(f"[green]✓[/] {message}")
    else:
        console.print(f"[red]✗[/] {message}")
        raise typer.Exit(1)


@hooks_app.command(
    "disable",
    epilog="""
\b
Examples:
  ait statusline hooks disable on-error
"""
)
def hooks_disable(
    name: str = typer.Argument(..., help="Hook name to disable")
):
    """Disable a hook."""
    success, message = StatusLineHooks.disable_hook(name)
    if success:
        console.print(f"[green]✓[/] {message}")
    else:
        console.print(f"[red]✗[/] {message}")
        raise typer.Exit(1)


# =============================================================================
# Gateway Commands (Setup & Customize - v0.7.0)
# =============================================================================


@app.command(
    "setup",
    epilog="""
\b
Examples:
  ait statusline setup        # Interactive gateway menu

The setup command is the recommended entry point for new users.
It guides you through configuration with clear options.
"""
)
def statusline_setup():
    """Quick gateway to statusLine customization.

    Single command for discovering and applying all statusLine customizations:
    - Visual customization (display options like git, time, session)
    - Theme selection
    - Spacing adjustment
    - Preset application
    - View all settings
    - Advanced editing

    This is the recommended way for new users to configure statusLine.
    """
    from rich.panel import Panel
    from rich.align import Align

    console.print()
    console.print(Panel.fit(
        "[bold]StatusLine Configuration[/]",
        border_style="cyan"
    ))
    console.print()

    options = [
        ("Customize display options", "git, time, session, lines changed, etc."),
        ("Change color theme", "select from available themes"),
        ("Adjust spacing", "minimal, standard, spacious"),
        ("Apply a preset", "pre-configured profiles"),
        ("View all settings", "see current configuration"),
        ("Edit raw config", "advanced JSON editing"),
    ]

    for i, (title, desc) in enumerate(options, 1):
        console.print(f"  [bold cyan]{i}.[/] {title}")
        console.print(f"     [dim]{desc}[/]")
    console.print()

    choice = Prompt.ask(
        "What would you like to do?",
        choices=["1", "2", "3", "4", "5", "6"],
        default="1"
    )

    # Route to appropriate command
    routing = {
        "1": lambda: config_wizard(),
        "2": lambda: theme_set(None),
        "3": lambda: config_spacing(None),
        "4": lambda: config_preset(None),
        "5": lambda: config_list(None, "table"),
        "6": config_edit,
    }

    try:
        routing[choice]()
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled[/]")

    # Offer to continue or exit
    console.print()
    if Confirm.ask("Configure another setting?", default=False):
        statusline_setup()  # Recursive call for another round


@app.command(
    "customize",
    epilog="""
\b
Examples:
  ait statusline customize    # Open unified customization menu

Unified menu combining display, theme, spacing, and advanced options.
Everything in one place!
"""
)
def statusline_customize():
    """Unified customization menu combining all options.

    Interactive menu showing:
    - Display settings (git, time, session info, etc.)
    - Theme selection
    - Spacing adjustment
    - Advanced options (reset, load preset, edit raw)

    All options are in one place - no jumping between commands!
    """
    from rich.panel import Panel
    from rich.align import Align

    config = StatusLineConfig()

    while True:
        console.print()
        console.print(Panel.fit(
            "[bold]StatusLine Customization[/]",
            border_style="cyan"
        ))
        console.print()

        # Show current status
        console.print("[bold]Current Configuration:[/]")
        console.print(f"  Theme: [yellow]{config.get('theme.name')}[/]")
        console.print(f"  Spacing: [yellow]{config.get('display.separator_spacing')}[/]")
        console.print()

        menu_options = [
            ("Display Options", "Choose what to show (git, time, session, etc.)"),
            ("Theme Selection", "Browse and select themes"),
            ("Spacing", "Adjust spacing between left and right sections"),
            ("Advanced", "Reset, load preset, or edit raw config"),
            ("Done", "Exit customization menu"),
        ]

        for i, (title, desc) in enumerate(menu_options, 1):
            console.print(f"  [bold cyan]{i}.[/] {title}")
            console.print(f"     [dim]{desc}[/]")
        console.print()

        choice = Prompt.ask(
            "Choose option",
            choices=["1", "2", "3", "4", "5"],
            default="5"
        )

        if choice == "1":
            # Display options - show settings from display category
            menu = InteractiveConfigMenu(config)
            menu.run(category="display")
        elif choice == "2":
            # Theme selection
            console.print()
            console.print("[bold]Available Themes:[/]")
            try:
                themes = config.get_available_themes()
                for theme in themes:
                    current = " [green]✓[/]" if theme == config.get('theme.name') else ""
                    console.print(f"  • {theme}{current}")
                console.print()
                new_theme = Prompt.ask("Select theme", choices=themes)
                config.set('theme.name', new_theme)
                console.print(f"[green]✓[/] Theme changed to [bold]{new_theme}[/]")
            except Exception as e:
                console.print(f"[red]Error loading themes: {e}[/]")
        elif choice == "3":
            # Spacing options
            spacing_options = ["minimal", "standard", "spacious"]
            console.print()
            console.print("[bold]Spacing Presets:[/]")
            console.print("  • minimal - tight spacing (1 space)")
            console.print("  • standard - normal spacing (2 spaces)")
            console.print("  • spacious - relaxed spacing (3 spaces)")
            console.print()
            spacing = Prompt.ask("Choose spacing", choices=spacing_options)
            config.set('display.separator_spacing', spacing)
            console.print(f"[green]✓[/] Spacing set to [bold]{spacing}[/]")
        elif choice == "4":
            # Advanced menu
            console.print()
            console.print("[bold]Advanced Options:[/]")
            console.print("  1. Edit raw config file")
            console.print("  2. Reset to defaults")
            console.print("  3. Load preset")
            console.print("  4. Cancel")
            console.print()
            adv_choice = Prompt.ask("Choose", choices=["1", "2", "3", "4"], default="4")
            if adv_choice == "1":
                config_edit()
            elif adv_choice == "2":
                if Confirm.ask("Reset all settings to defaults?", default=False):
                    config.reset()
                    console.print("[green]✓[/] Reset to defaults")
            elif adv_choice == "3":
                presets = ["minimal", "default", "verbose"]
                preset = Prompt.ask("Choose preset", choices=presets)
                config.load_preset(preset)
                console.print(f"[green]✓[/] Preset '{preset}' applied")
        elif choice == "5":
            console.print("[green]✓[/] Done!")
            break


# =============================================================================
# Main statusline commands (render, install, test, etc.)
# =============================================================================


@app.command("render")
def statusline_render():
    """Render statusLine output (called by Claude Code).

    This command reads JSON from stdin and outputs formatted statusLine.
    """
    from aiterm.statusline.renderer import StatusLineRenderer

    # Create renderer
    renderer = StatusLineRenderer()

    # Render (reads from stdin)
    try:
        output = renderer.render()
        # Print directly to stdout (no Rich formatting)
        import sys
        sys.stdout.write(output)
        sys.stdout.flush()
    except Exception as e:
        # On error, output minimal statusLine
        import sys
        sys.stdout.write(f"╭─ ⚠️  StatusLine Error\n╰─ {str(e)[:50]}")
        sys.stdout.flush()


@app.command(
    "install",
    epilog="""
\b
Examples:
  ait statusline install  # Update Claude Code settings
"""
)
def statusline_install():
    """Update Claude Code settings.json to use aiterm statusLine.

    This command will:
    1. Locate Claude Code settings.json
    2. Backup existing settings
    3. Update statusLine.command to use 'ait statusline render'
    4. Verify the installation
    """
    import json
    import shutil
    from datetime import datetime

    # Locate settings file
    settings_file = Path.home() / '.claude' / 'settings.json'

    if not settings_file.exists():
        console.print("[red]Error: Claude Code settings.json not found[/]")
        console.print(f"[dim]Expected location: {settings_file}[/]")
        console.print("\n[yellow]Is Claude Code installed?[/]")
        raise typer.Exit(1)

    # Read current settings
    try:
        with open(settings_file) as f:
            settings = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in settings.json: {e}[/]")
        raise typer.Exit(1)

    # Create backup
    backup_file = settings_file.parent / f"settings.json.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.copy(settings_file, backup_file)
    console.print(f"[dim]Created backup: {backup_file.name}[/]")

    # Check current statusLine config
    current_statusline = settings.get('statusLine', {})

    if current_statusline.get('command') == 'ait statusline render':
        console.print("[yellow]StatusLine already installed![/]")
        console.print("\n[dim]Current configuration:[/]")
        console.print(json.dumps(current_statusline, indent=2))
        return

    # Update settings
    settings['statusLine'] = {
        "type": "command",
        "command": "ait statusline render"
    }

    # Save updated settings
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')  # Add trailing newline

    console.print("[green]✓[/] StatusLine installed successfully!")
    console.print("\n[bold]Configuration:[/]")
    console.print(json.dumps(settings['statusLine'], indent=2))

    if current_statusline:
        console.print("\n[dim]Previous configuration:[/]")
        console.print(json.dumps(current_statusline, indent=2))

    console.print("\n[yellow]Next steps:[/]")
    console.print("  1. Restart Claude Code to see the new statusLine")
    console.print("  2. Run 'ait statusline config' to customize display")
    console.print("  3. Run 'ait statusline theme list' to see available themes")


@app.command(
    "test",
    epilog="""
\b
Examples:
  ait statusline test              # Test with default mock data
  ait statusline test --theme cool-blues  # Test with specific theme
"""
)
def statusline_test(
    theme: Optional[str] = typer.Option(
        None,
        "--theme", "-t",
        help="Test with specific theme"
    )
):
    """Test statusLine with mock data.

    Renders statusLine using mock JSON data to verify installation and theme.
    """
    import json
    from aiterm.statusline.renderer import StatusLineRenderer

    # Create mock JSON data
    mock_data = {
        "workspace": {
            "current_dir": str(Path.cwd()),
            "project_dir": str(Path.cwd())
        },
        "model": {
            "display_name": "Claude Sonnet 4.5",
            "id": "claude-sonnet-4-5-20250929"
        },
        "output_style": {
            "name": "learning"
        },
        "session_id": "test-session",
        "cost": {
            "total_cost_usd": 0.15,
            "total_duration_ms": 45000,
            "total_lines_added": 123,
            "total_lines_removed": 45
        }
    }

    # Override theme if specified
    if theme:
        config = StatusLineConfig()
        config.set('theme.name', theme)
        renderer = StatusLineRenderer(config)
    else:
        renderer = StatusLineRenderer()

    # Render
    json_input = json.dumps(mock_data)
    output = renderer.render(json_input)

    console.print("[bold]StatusLine Test[/]")
    if theme:
        console.print(f"[dim]Theme: {theme}[/]")
    console.print()

    # Print the rendered output
    import sys
    sys.stdout.write(output + '\n')
    sys.stdout.flush()

    console.print()
    console.print("[green]✓[/] StatusLine rendered successfully!")
    console.print("\n[dim]This is how your statusLine will look in Claude Code[/]")


@app.command(
    "doctor",
    epilog="""
\b
Examples:
  ait statusline doctor  # Validate statusLine setup
"""
)
def statusline_doctor():
    """Validate statusLine setup and configuration.

    Checks:
    - Claude Code settings.json configuration
    - StatusLine config file validity
    - Theme configuration
    - Dependencies
    """
    import json
    import shutil

    console.print("[bold]StatusLine Health Check[/]\n")

    issues = []
    warnings = []

    # Check 1: Claude Code settings.json
    console.print("1. Checking Claude Code settings...")
    settings_file = Path.home() / '.claude' / 'settings.json'

    if not settings_file.exists():
        console.print("   [red]✗[/] Settings file not found")
        issues.append("Claude Code settings.json not found")
    else:
        console.print("   [green]✓[/] Settings file exists")

        try:
            with open(settings_file) as f:
                settings = json.load(f)

            statusline_config = settings.get('statusLine', {})

            if not statusline_config:
                console.print("   [yellow]⚠[/] No statusLine configuration")
                warnings.append("StatusLine not configured (run 'ait statusline install')")
            elif statusline_config.get('command') == 'ait statusline render':
                console.print("   [green]✓[/] StatusLine configured correctly")
            else:
                console.print("   [yellow]⚠[/] StatusLine using different command")
                warnings.append(f"StatusLine command: {statusline_config.get('command')}")

        except json.JSONDecodeError:
            console.print("   [red]✗[/] Invalid JSON in settings file")
            issues.append("Settings file contains invalid JSON")

    # Check 2: StatusLine config
    console.print("\n2. Checking statusLine config...")
    config = StatusLineConfig()

    is_valid, errors = config.validate()

    if is_valid:
        console.print("   [green]✓[/] Config file is valid")
    else:
        console.print("   [red]✗[/] Config file has errors")
        for error in errors:
            issues.append(f"Config error: {error}")

    # Check 3: Theme configuration
    console.print("\n3. Checking theme...")
    theme_name = config.get('theme.name', 'purple-charcoal')

    try:
        from aiterm.statusline.themes import get_theme
        theme = get_theme(theme_name)
        console.print(f"   [green]✓[/] Theme '{theme_name}' is valid")
    except ValueError:
        console.print(f"   [red]✗[/] Invalid theme: {theme_name}")
        issues.append(f"Theme '{theme_name}' not found")

    # Check 4: Dependencies
    console.print("\n4. Checking dependencies...")

    # Check git
    if shutil.which('git'):
        console.print("   [green]✓[/] git available")
    else:
        console.print("   [yellow]⚠[/] git not found")
        warnings.append("Git not available (git status won't work)")

    # Check 5: Renderer test
    console.print("\n5. Testing renderer...")
    try:
        from aiterm.statusline.renderer import StatusLineRenderer
        renderer = StatusLineRenderer()

        mock_data = json.dumps({
            "workspace": {"current_dir": "/tmp", "project_dir": "/tmp"},
            "model": {"display_name": "Claude Sonnet 4.5"},
            "output_style": {"name": "default"},
            "session_id": "test",
            "cost": {"total_lines_added": 0, "total_lines_removed": 0}
        })

        output = renderer.render(mock_data)
        if output:
            console.print("   [green]✓[/] Renderer works correctly")
        else:
            console.print("   [red]✗[/] Renderer returned empty output")
            issues.append("Renderer test failed")

    except Exception as e:
        console.print(f"   [red]✗[/] Renderer error: {e}")
        issues.append(f"Renderer test failed: {e}")

    # Summary
    console.print("\n" + "="*50)

    if not issues and not warnings:
        console.print("\n[bold green]✓ StatusLine is healthy![/]")
        console.print("\n[dim]Everything looks good. StatusLine should work correctly.[/]")
    elif issues:
        console.print(f"\n[bold red]✗ Found {len(issues)} issue(s)[/]")
        for issue in issues:
            console.print(f"  [red]•[/] {issue}")

        if warnings:
            console.print(f"\n[yellow]⚠ {len(warnings)} warning(s)[/]")
            for warning in warnings:
                console.print(f"  [yellow]•[/] {warning}")

        raise typer.Exit(1)
    else:
        console.print(f"\n[yellow]⚠ Found {len(warnings)} warning(s)[/]")
        for warning in warnings:
            console.print(f"  [yellow]•[/] {warning}")

        console.print("\n[dim]StatusLine should work, but consider addressing warnings[/]")
