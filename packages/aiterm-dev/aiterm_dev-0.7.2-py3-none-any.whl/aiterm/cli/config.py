"""Config management CLI commands."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Configuration management commands.")
console = Console()


@app.command(
    "path",
    epilog="""
[bold]Examples:[/]
  ait config path       # Show config directory path
  ait config path --all # Show all config paths
"""
)
def config_path(
    all_paths: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all configuration paths.",
    ),
) -> None:
    """Show configuration file paths."""
    import os
    from aiterm.config import (
        get_config_home,
        get_config_file,
    )
    from aiterm.config.paths import (
        get_profiles_dir,
        get_themes_dir,
        get_cache_dir,
    )

    config_home = get_config_home()

    if not all_paths:
        console.print(str(config_home))
        return

    # Build paths table
    table = Table(title="Configuration Paths", show_header=True, border_style="cyan")
    table.add_column("Path Type", style="bold")
    table.add_column("Location")
    table.add_column("Exists")

    paths = [
        ("Config Home", config_home),
        ("Config File", get_config_file()),
        ("Profiles", get_profiles_dir()),
        ("Themes", get_themes_dir()),
        ("Cache", get_cache_dir()),
    ]

    for name, path in paths:
        exists = "[green]yes[/]" if path.exists() else "[dim]no[/]"
        table.add_row(name, str(path), exists)

    console.print(table)

    # Show environment variable status
    console.print()
    env_home = os.environ.get("AITERM_CONFIG_HOME")
    xdg_home = os.environ.get("XDG_CONFIG_HOME")

    if env_home:
        console.print(f"[bold]AITERM_CONFIG_HOME:[/] {env_home}")
    elif xdg_home:
        console.print(f"[bold]XDG_CONFIG_HOME:[/] {xdg_home}/aiterm")
    else:
        console.print("[dim]Using default: ~/.config/aiterm[/]")


@app.command(
    "show",
    epilog="""
[bold]Examples:[/]
  ait config show   # Display current configuration
"""
)
def config_show() -> None:
    """Display current configuration settings."""
    from aiterm.config import get_config_file

    config_file = get_config_file()

    if not config_file.exists():
        console.print("[yellow]No configuration file found.[/]")
        console.print(f"Expected at: {config_file}")
        console.print("\nRun [bold]ait config init[/] to create one.")
        return

    # Read and display config
    content = config_file.read_text()
    console.print(Panel(
        content,
        title=str(config_file),
        border_style="cyan",
    ))


@app.command(
    "init",
    epilog="""
[bold]Examples:[/]
  ait config init        # Create default config
  ait config init --force  # Overwrite existing config
"""
)
def config_init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration.",
    ),
) -> None:
    """Initialize configuration directory and files."""
    from aiterm.config import ensure_config_dir, get_config_file

    config_dir = ensure_config_dir()
    config_file = get_config_file()

    console.print(f"[bold]Config directory:[/] {config_dir}")

    if config_file.exists() and not force:
        console.print(f"[yellow]Config file already exists:[/] {config_file}")
        console.print("Use [bold]--force[/] to overwrite.")
        return

    # Create default config
    default_config = """\
# aiterm configuration
# https://data-wise.github.io/aiterm/

[general]
# Default terminal (auto, iterm2, ghostty)
default_terminal = "auto"

# Quiet mode - suppress non-essential output
quiet_mode = false

[profiles]
# Default profile name
default = "default"

# Auto-switch profiles based on context
auto_switch = true

[flow_cli]
# Enable flow-cli integration
enabled = true

# Dispatcher name (tm)
dispatcher = "tm"

[claude]
# Manage Claude Code settings
manage_settings = true

# Create backups before modifying settings
backup_on_change = true
"""

    config_file.write_text(default_config)
    console.print(f"[green]Created:[/] {config_file}")


@app.command(
    "edit",
    epilog="""
[bold]Examples:[/]
  ait config edit   # Open config in $EDITOR
"""
)
def config_edit() -> None:
    """Open configuration file in editor."""
    import os
    import subprocess

    from aiterm.config import get_config_file, ensure_config_dir

    config_file = get_config_file()

    if not config_file.exists():
        console.print("[yellow]No config file found. Creating default...[/]")
        ensure_config_dir()
        config_init(force=False)

    editor = os.environ.get("EDITOR", "nano")
    console.print(f"Opening {config_file} with {editor}...")

    try:
        subprocess.run([editor, str(config_file)], check=True)
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to open editor: {editor}[/]")
    except FileNotFoundError:
        console.print(f"[red]Editor not found: {editor}[/]")
        console.print("Set $EDITOR environment variable to your preferred editor.")
