"""Ghostty terminal management commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    help="Ghostty terminal management commands.",
    no_args_is_help=True,
)

console = Console()


@app.command(
    "status",
    epilog="""
[bold]Examples:[/]
  ait ghostty status      # Check if running in Ghostty
""",
)
def ghostty_status() -> None:
    """Check Ghostty detection and status."""
    from aiterm.terminal import ghostty, detect_terminal, TerminalType

    terminal = detect_terminal()
    is_ghostty = terminal == TerminalType.GHOSTTY

    table = Table(title="Ghostty Status", show_header=False, border_style="cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Detected Terminal", terminal.value)
    table.add_row(
        "Running in Ghostty",
        "[green]Yes[/]" if is_ghostty else "[dim]No[/]",
    )

    # Get version if available
    version = ghostty.get_version()
    if version:
        table.add_row("Ghostty Version", version)

    # Check config
    config_path = ghostty.get_config_path()
    if config_path:
        table.add_row("Config File", str(config_path))
    else:
        table.add_row("Config File", "[dim]Not found[/]")

    console.print(table)


@app.command(
    "config",
    epilog="""
[bold]Examples:[/]
  ait ghostty config         # Show current config
  ait ghostty config --edit  # Open config in editor
""",
)
def ghostty_config(
    edit: bool = typer.Option(
        False,
        "--edit",
        "-e",
        help="Open config file in editor.",
    ),
) -> None:
    """Show or edit Ghostty configuration."""
    from aiterm.terminal import ghostty
    import os
    import subprocess

    config_path = ghostty.get_config_path()

    if edit:
        if not config_path:
            # Create default config path
            config_path = ghostty.get_default_config_path()
            if not config_path.exists():
                config_path.touch()
                console.print(f"[green]Created[/] {config_path}")

        editor = os.environ.get("EDITOR", "vim")
        console.print(f"[dim]Opening in {editor}...[/]")
        subprocess.run([editor, str(config_path)])
        return

    if not config_path or not config_path.exists():
        console.print("[yellow]No Ghostty config found.[/]")
        console.print(f"[dim]Create one at: ~/.config/ghostty/config[/]")
        return

    config = ghostty.parse_config(config_path)

    console.print(
        Panel(
            f"[bold]Config:[/] {config_path}",
            title="Ghostty Configuration",
            border_style="cyan",
        )
    )

    table = Table(show_header=True, border_style="dim")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Font", f"{config.font_family} @ {config.font_size}pt")
    table.add_row("Theme", config.theme or "[dim](default)[/]")
    table.add_row("Padding", f"x={config.window_padding_x}, y={config.window_padding_y}")
    table.add_row("Opacity", str(config.background_opacity))
    table.add_row("Cursor", config.cursor_style)
    table.add_row("Titlebar Style", config.macos_titlebar_style)
    table.add_row("Background Image", config.background_image or "[dim]None[/]")
    table.add_row("Scroll Multiplier", str(config.mouse_scroll_multiplier))

    console.print(table)

    # Show raw config if there are extra values
    extra_keys = set(config.raw_config.keys()) - {
        "font-family",
        "font-size",
        "theme",
        "window-padding-x",
        "window-padding-y",
        "background-opacity",
        "cursor-style",
        "macos-titlebar-style",
        "background-image",
        "mouse-scroll-multiplier",
    }
    if extra_keys:
        console.print("\n[bold]Other settings:[/]")
        for key in sorted(extra_keys):
            console.print(f"  {key} = {config.raw_config[key]}")


# Theme sub-commands
theme_app = typer.Typer(help="Theme management for Ghostty.")
app.add_typer(theme_app, name="theme")


@theme_app.command(
    "list",
    epilog="""
[bold]Examples:[/]
  ait ghostty theme list   # Show available themes
""",
)
def theme_list() -> None:
    """List available Ghostty themes."""
    from aiterm.terminal import ghostty

    themes = ghostty.list_themes()
    current_config = ghostty.parse_config()
    current_theme = current_config.theme

    console.print("[bold cyan]Available Ghostty Themes[/]\n")

    table = Table(show_header=True, border_style="dim")
    table.add_column("Theme", style="bold")
    table.add_column("Status")

    for theme in themes:
        if theme == current_theme:
            table.add_row(theme, "[green]● active[/]")
        else:
            table.add_row(theme, "[dim]○[/]")

    console.print(table)
    console.print(f"\n[dim]Total: {len(themes)} built-in themes[/]")
    console.print("[dim]Use 'ait ghostty theme apply <name>' to change theme[/]")


@theme_app.command(
    "apply",
    epilog="""
[bold]Examples:[/]
  ait ghostty theme apply catppuccin-mocha   # Apply theme
  ait ghostty theme apply nord               # Switch to Nord
""",
)
def theme_apply(
    theme_name: str = typer.Argument(..., help="Name of theme to apply."),
) -> None:
    """Apply a theme to Ghostty."""
    from aiterm.terminal import ghostty

    # Validate theme exists (or allow custom)
    builtin_themes = ghostty.list_themes()
    is_builtin = theme_name in builtin_themes

    if ghostty.set_theme(theme_name):
        console.print(f"[green]✓[/] Theme set to: [bold]{theme_name}[/]")
        if not is_builtin:
            console.print("[yellow]Note: This is not a built-in theme.[/]")
        console.print("[dim]Ghostty will auto-reload the config.[/]")
    else:
        console.print("[red]Failed to set theme.[/]")
        raise typer.Exit(1)


@theme_app.command(
    "show",
    epilog="""
[bold]Examples:[/]
  ait ghostty theme show   # Show current theme
""",
)
def theme_show() -> None:
    """Show currently active theme."""
    from aiterm.terminal import ghostty

    config = ghostty.parse_config()

    if config.theme:
        console.print(f"[bold]Current theme:[/] {config.theme}")
    else:
        console.print("[dim]No theme set (using Ghostty defaults)[/]")


# Font sub-commands
font_app = typer.Typer(help="Font settings for Ghostty.")
app.add_typer(font_app, name="font")


@font_app.command(
    "show",
    epilog="""
[bold]Examples:[/]
  ait ghostty font show   # Show current font settings
""",
)
def font_show() -> None:
    """Show current font settings."""
    from aiterm.terminal import ghostty

    config = ghostty.parse_config()
    console.print(f"[bold]Font:[/] {config.font_family} @ {config.font_size}pt")


@font_app.command(
    "set",
    epilog="""
[bold]Examples:[/]
  ait ghostty font set "JetBrains Mono"        # Set font family
  ait ghostty font set "Fira Code" --size 16   # Set font and size
""",
)
def font_set(
    font_family: str = typer.Argument(..., help="Font family name."),
    size: Optional[int] = typer.Option(
        None,
        "--size",
        "-s",
        help="Font size in points.",
    ),
) -> None:
    """Set font family and optionally size."""
    from aiterm.terminal import ghostty

    success = ghostty.set_config_value("font-family", font_family)
    if success:
        console.print(f"[green]✓[/] Font family: {font_family}")
    else:
        console.print("[red]Failed to set font family.[/]")
        raise typer.Exit(1)

    if size:
        success = ghostty.set_config_value("font-size", str(size))
        if success:
            console.print(f"[green]✓[/] Font size: {size}pt")
        else:
            console.print("[red]Failed to set font size.[/]")
            raise typer.Exit(1)

    console.print("[dim]Ghostty will auto-reload the config.[/]")


@app.command(
    "set",
    epilog="""
[bold]Examples:[/]
  ait ghostty set background-opacity 0.9      # Set opacity
  ait ghostty set window-padding-x 10         # Set padding
  ait ghostty set cursor-style bar            # Set cursor
""",
)
def ghostty_set(
    key: str = typer.Argument(..., help="Configuration key."),
    value: str = typer.Argument(..., help="Value to set."),
) -> None:
    """Set a Ghostty configuration value."""
    from aiterm.terminal import ghostty

    if ghostty.set_config_value(key, value):
        console.print(f"[green]✓[/] Set {key} = {value}")
        console.print("[dim]Ghostty will auto-reload the config.[/]")
    else:
        console.print(f"[red]Failed to set {key}.[/]")
        raise typer.Exit(1)


# =============================================================================
# Profile Management (v0.4.0)
# =============================================================================

profile_app = typer.Typer(help="Profile management for Ghostty.")
app.add_typer(profile_app, name="profile")


@profile_app.command(
    "list",
    epilog="""
[bold]Examples:[/]
  ait ghostty profile list   # List saved profiles
""",
)
def profile_list() -> None:
    """List available Ghostty profiles."""
    from aiterm.terminal import ghostty

    profiles = ghostty.list_profiles()

    if not profiles:
        console.print("[dim]No profiles saved yet.[/]")
        console.print("\n[bold]Create your first profile:[/]")
        console.print("  ait ghostty profile create my-profile")
        return

    console.print("[bold cyan]Saved Profiles[/]\n")

    table = Table(show_header=True, border_style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Theme")
    table.add_column("Font")
    table.add_column("Description")

    for profile in profiles:
        font_info = ""
        if profile.font_family:
            font_info = profile.font_family
            if profile.font_size:
                font_info += f" @ {profile.font_size}pt"

        table.add_row(
            profile.name,
            profile.theme or "[dim]-[/]",
            font_info or "[dim]-[/]",
            profile.description[:40] + "..." if len(profile.description) > 40 else profile.description or "[dim]-[/]",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(profiles)} profile(s)[/]")


@profile_app.command(
    "show",
    epilog="""
[bold]Examples:[/]
  ait ghostty profile show coding    # Show profile details
""",
)
def profile_show(
    name: str = typer.Argument(..., help="Profile name to show."),
) -> None:
    """Show details of a specific profile."""
    from aiterm.terminal import ghostty

    profile = ghostty.get_profile(name)
    if not profile:
        console.print(f"[red]Profile not found:[/] {name}")
        raise typer.Exit(1)

    console.print(Panel(f"[bold]{profile.name}[/]", title="Profile Details", border_style="cyan"))

    table = Table(show_header=False, border_style="dim")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    if profile.description:
        table.add_row("Description", profile.description)
    if profile.created_at:
        table.add_row("Created", profile.created_at)
    if profile.theme:
        table.add_row("Theme", profile.theme)
    if profile.font_family:
        font = profile.font_family
        if profile.font_size:
            font += f" @ {profile.font_size}pt"
        table.add_row("Font", font)
    if profile.background_opacity > 0:
        table.add_row("Opacity", str(profile.background_opacity))
    if profile.window_padding_x or profile.window_padding_y:
        table.add_row("Padding", f"x={profile.window_padding_x}, y={profile.window_padding_y}")
    if profile.cursor_style:
        table.add_row("Cursor", profile.cursor_style)
    if profile.macos_titlebar_style:
        table.add_row("Titlebar Style", profile.macos_titlebar_style)
    if profile.background_image:
        table.add_row("Background Image", profile.background_image)
    if profile.mouse_scroll_multiplier > 0:
        table.add_row("Scroll Multiplier", str(profile.mouse_scroll_multiplier))

    console.print(table)

    if profile.custom_settings:
        console.print("\n[bold]Custom settings:[/]")
        for key, value in profile.custom_settings.items():
            console.print(f"  {key} = {value}")


@profile_app.command(
    "create",
    epilog="""
[bold]Examples:[/]
  ait ghostty profile create coding                      # Create from current config
  ait ghostty profile create coding -d "My coding setup" # With description
""",
)
def profile_create(
    name: str = typer.Argument(..., help="Name for the new profile."),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Optional description for the profile.",
    ),
) -> None:
    """Create a new profile from current Ghostty config."""
    from aiterm.terminal import ghostty

    # Check if profile already exists
    existing = ghostty.get_profile(name)
    if existing:
        console.print(f"[red]Profile already exists:[/] {name}")
        console.print("[dim]Use 'ait ghostty profile delete' first to replace.[/]")
        raise typer.Exit(1)

    profile = ghostty.create_profile_from_current(name, description)

    console.print(f"[green]✓[/] Created profile: [bold]{profile.name}[/]")
    if profile.theme:
        console.print(f"  Theme: {profile.theme}")
    if profile.font_family:
        console.print(f"  Font: {profile.font_family} @ {profile.font_size}pt")

    profile_path = ghostty.get_profiles_dir() / f"{name}.conf"
    console.print(f"\n[dim]Saved to: {profile_path}[/]")


@profile_app.command(
    "apply",
    epilog="""
[bold]Examples:[/]
  ait ghostty profile apply coding         # Apply profile
  ait ghostty profile apply coding --no-backup  # Skip backup
""",
)
def profile_apply(
    name: str = typer.Argument(..., help="Profile name to apply."),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        help="Skip backing up current config.",
    ),
) -> None:
    """Apply a saved profile to Ghostty config."""
    from aiterm.terminal import ghostty

    if ghostty.apply_profile(name, backup=not no_backup):
        console.print(f"[green]✓[/] Applied profile: [bold]{name}[/]")
        console.print("[dim]Ghostty will auto-reload the config.[/]")
    else:
        console.print(f"[red]Profile not found:[/] {name}")
        raise typer.Exit(1)


@profile_app.command(
    "delete",
    epilog="""
[bold]Examples:[/]
  ait ghostty profile delete old-profile   # Delete a profile
""",
)
def profile_delete(
    name: str = typer.Argument(..., help="Profile name to delete."),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation.",
    ),
) -> None:
    """Delete a saved profile."""
    from aiterm.terminal import ghostty

    profile = ghostty.get_profile(name)
    if not profile:
        console.print(f"[red]Profile not found:[/] {name}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete profile '{name}'?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    if ghostty.delete_profile(name):
        console.print(f"[green]✓[/] Deleted profile: {name}")
    else:
        console.print(f"[red]Failed to delete profile:[/] {name}")
        raise typer.Exit(1)


# =============================================================================
# Backup Management (v0.4.0)
# =============================================================================

@app.command(
    "backup",
    epilog="""
[bold]Examples:[/]
  ait ghostty backup                     # Create timestamped backup
  ait ghostty backup --suffix before-update  # With custom suffix
""",
)
def ghostty_backup(
    suffix: Optional[str] = typer.Option(
        None,
        "--suffix",
        "-s",
        help="Optional suffix for backup filename.",
    ),
) -> None:
    """Create a backup of Ghostty config."""
    from aiterm.terminal import ghostty

    backup_path = ghostty.backup_config(suffix)

    if backup_path:
        console.print(f"[green]✓[/] Backup created: {backup_path.name}")
        console.print(f"[dim]Location: {backup_path}[/]")
    else:
        console.print("[yellow]No config file to backup.[/]")
        raise typer.Exit(1)


@app.command(
    "restore",
    epilog="""
[bold]Examples:[/]
  ait ghostty restore                      # List backups to choose from
  ait ghostty restore config.backup.20251230  # Restore specific backup
""",
)
def ghostty_restore(
    backup_name: Optional[str] = typer.Argument(
        None,
        help="Backup filename to restore (optional).",
    ),
) -> None:
    """Restore Ghostty config from a backup."""
    from aiterm.terminal import ghostty

    backups = ghostty.list_backups()

    if not backups:
        console.print("[yellow]No backups found.[/]")
        raise typer.Exit(1)

    if not backup_name:
        # Show available backups
        console.print("[bold cyan]Available Backups[/]\n")

        table = Table(show_header=True, border_style="dim")
        table.add_column("#", style="dim")
        table.add_column("Backup File", style="bold")
        table.add_column("Date")

        for i, backup in enumerate(backups, 1):
            # Parse timestamp from filename
            parts = backup.name.replace("config.backup.", "").split(".")
            timestamp = parts[0] if parts else "unknown"
            table.add_row(str(i), backup.name, timestamp)

        console.print(table)
        console.print("\n[dim]Use 'ait ghostty restore <backup-name>' to restore[/]")
        return

    # Find the backup
    backup_path = None
    config_path = ghostty.get_config_path()
    if config_path:
        backup_path = config_path.parent / backup_name

    if not backup_path or not backup_path.exists():
        console.print(f"[red]Backup not found:[/] {backup_name}")
        raise typer.Exit(1)

    confirm = typer.confirm(f"Restore from '{backup_name}'? (current config will be saved as .pre-restore)")
    if not confirm:
        console.print("[dim]Cancelled.[/]")
        raise typer.Exit(0)

    if ghostty.restore_backup(backup_path):
        console.print(f"[green]✓[/] Restored from: {backup_name}")
        console.print("[dim]Ghostty will auto-reload the config.[/]")
    else:
        console.print("[red]Failed to restore backup.[/]")
        raise typer.Exit(1)


# =============================================================================
# Keybind Management (v0.4.0)
# =============================================================================

keybind_app = typer.Typer(help="Keybind management for Ghostty.")
app.add_typer(keybind_app, name="keybind")


@keybind_app.command(
    "list",
    epilog="""
[bold]Examples:[/]
  ait ghostty keybind list   # List configured keybindings
""",
)
def keybind_list() -> None:
    """List configured keybindings."""
    from aiterm.terminal import ghostty

    keybinds = ghostty.list_keybinds()

    if not keybinds:
        console.print("[dim]No custom keybindings configured.[/]")
        console.print("\n[bold]Add keybindings:[/]")
        console.print("  ait ghostty keybind add ctrl+t new_tab")
        console.print("  ait ghostty keybind preset vim")
        return

    console.print("[bold cyan]Configured Keybindings[/]\n")

    table = Table(show_header=True, border_style="dim")
    table.add_column("Trigger", style="bold")
    table.add_column("Action")
    table.add_column("Prefix", style="dim")

    for kb in keybinds:
        table.add_row(kb.trigger, kb.action, kb.prefix or "-")

    console.print(table)
    console.print(f"\n[dim]Total: {len(keybinds)} keybinding(s)[/]")


@keybind_app.command(
    "add",
    epilog="""
[bold]Examples:[/]
  ait ghostty keybind add ctrl+t new_tab               # Add keybind
  ait ghostty keybind add ctrl+d new_split:right       # Split right
  ait ghostty keybind add ctrl+g reload_config --global # Global keybind
""",
)
def keybind_add(
    trigger: str = typer.Argument(..., help="Key trigger (e.g., ctrl+t, cmd+shift+n)."),
    action: str = typer.Argument(..., help="Action to perform (e.g., new_tab, new_split:right)."),
    global_bind: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Make keybind global (works even when Ghostty not focused).",
    ),
    unconsumed: bool = typer.Option(
        False,
        "--unconsumed",
        "-u",
        help="Don't consume the input (send to program too).",
    ),
) -> None:
    """Add a keybinding to Ghostty config."""
    from aiterm.terminal import ghostty

    prefix = ""
    if global_bind and unconsumed:
        prefix = "global:unconsumed:"
    elif global_bind:
        prefix = "global:"
    elif unconsumed:
        prefix = "unconsumed:"

    if ghostty.add_keybind(trigger, action, prefix):
        console.print(f"[green]✓[/] Added keybind: [bold]{trigger}[/] → {action}")
        if prefix:
            console.print(f"  Prefix: {prefix}")
        console.print("[dim]Ghostty will auto-reload the config.[/]")
    else:
        console.print("[red]Failed to add keybind.[/]")
        raise typer.Exit(1)


@keybind_app.command(
    "remove",
    epilog="""
[bold]Examples:[/]
  ait ghostty keybind remove ctrl+t   # Remove keybind
""",
)
def keybind_remove(
    trigger: str = typer.Argument(..., help="Key trigger to remove."),
) -> None:
    """Remove a keybinding from Ghostty config."""
    from aiterm.terminal import ghostty

    if ghostty.remove_keybind(trigger):
        console.print(f"[green]✓[/] Removed keybind: {trigger}")
        console.print("[dim]Ghostty will auto-reload the config.[/]")
    else:
        console.print(f"[yellow]Keybind not found:[/] {trigger}")
        raise typer.Exit(1)


@keybind_app.command(
    "preset",
    epilog="""
[bold]Examples:[/]
  ait ghostty keybind preset vim      # Apply vim-style keybinds
  ait ghostty keybind preset tmux     # Apply tmux-style keybinds
  ait ghostty keybind preset macos    # Apply macOS-native keybinds
  ait ghostty keybind preset emacs    # Apply emacs-style keybinds
""",
)
def keybind_preset(
    name: Optional[str] = typer.Argument(
        None,
        help="Preset name (vim, emacs, tmux, macos).",
    ),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        help="Skip backing up current config.",
    ),
) -> None:
    """Apply a keybind preset."""
    from aiterm.terminal import ghostty

    presets = ghostty.get_keybind_presets()

    if not name:
        # List available presets
        console.print("[bold cyan]Available Keybind Presets[/]\n")

        table = Table(show_header=True, border_style="dim")
        table.add_column("Preset", style="bold")
        table.add_column("Keybinds")
        table.add_column("Style")

        preset_info = {
            "vim": ("10", "Vim-style navigation (ctrl+hjkl, ctrl+w splits)"),
            "emacs": ("7", "Emacs-style (ctrl+x prefix, buffer navigation)"),
            "tmux": ("11", "tmux-style (ctrl+b prefix, pane management)"),
            "macos": ("8", "macOS-native (cmd+t, cmd+d splits)"),
        }

        for p in presets:
            count, desc = preset_info.get(p, ("?", ""))
            table.add_row(p, count, desc)

        console.print(table)
        console.print("\n[dim]Use 'ait ghostty keybind preset <name>' to apply[/]")
        return

    if name not in presets:
        console.print(f"[red]Unknown preset:[/] {name}")
        console.print(f"[dim]Available: {', '.join(presets)}[/]")
        raise typer.Exit(1)

    preset_keybinds = ghostty.get_keybind_preset(name)
    if not preset_keybinds:
        console.print("[red]Failed to load preset.[/]")
        raise typer.Exit(1)

    console.print(f"[bold]Applying preset:[/] {name}")
    console.print(f"[dim]This will add {len(preset_keybinds)} keybindings.[/]\n")

    # Show what will be added
    table = Table(show_header=True, border_style="dim")
    table.add_column("Trigger", style="bold")
    table.add_column("Action")

    for kb in preset_keybinds:
        table.add_row(kb.trigger, kb.action)

    console.print(table)
    console.print()

    confirm = typer.confirm("Apply this preset?")
    if not confirm:
        console.print("[dim]Cancelled.[/]")
        raise typer.Exit(0)

    if ghostty.apply_keybind_preset(name, backup=not no_backup):
        console.print(f"\n[green]✓[/] Applied preset: [bold]{name}[/]")
        console.print("[dim]Ghostty will auto-reload the config.[/]")
    else:
        console.print("[red]Failed to apply preset.[/]")
        raise typer.Exit(1)


# =============================================================================
# Session Management (v0.4.0)
# =============================================================================

session_app = typer.Typer(help="Session management for Ghostty.")
app.add_typer(session_app, name="session")


@session_app.command(
    "list",
    epilog="""
[bold]Examples:[/]
  ait ghostty session list   # List saved sessions
""",
)
def session_list() -> None:
    """List saved sessions."""
    from aiterm.terminal import ghostty

    sessions = ghostty.list_sessions()

    if not sessions:
        console.print("[dim]No sessions saved yet.[/]")
        console.print("\n[bold]Save your first session:[/]")
        console.print("  ait ghostty session save my-project")
        return

    console.print("[bold cyan]Saved Sessions[/]\n")

    table = Table(show_header=True, border_style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Layout")
    table.add_column("Directories")
    table.add_column("Created")

    for session in sessions:
        dirs_display = ", ".join(session.working_dirs[:2])
        if len(session.working_dirs) > 2:
            dirs_display += f" (+{len(session.working_dirs) - 2})"

        # Format date
        created = session.created_at[:10] if session.created_at else "-"

        table.add_row(
            session.name,
            session.layout,
            dirs_display or "[dim]-[/]",
            created,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(sessions)} session(s)[/]")


@session_app.command(
    "show",
    epilog="""
[bold]Examples:[/]
  ait ghostty session show my-project   # Show session details
""",
)
def session_show(
    name: str = typer.Argument(..., help="Session name to show."),
) -> None:
    """Show details of a saved session."""
    from aiterm.terminal import ghostty

    session = ghostty.get_session(name)
    if not session:
        console.print(f"[red]Session not found:[/] {name}")
        raise typer.Exit(1)

    console.print(Panel(f"[bold]{session.name}[/]", title="Session Details", border_style="cyan"))

    table = Table(show_header=False, border_style="dim")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    if session.description:
        table.add_row("Description", session.description)
    table.add_row("Layout", session.layout)
    table.add_row("Created", session.created_at or "-")

    console.print(table)

    if session.working_dirs:
        console.print("\n[bold]Working Directories:[/]")
        for i, dir_path in enumerate(session.working_dirs, 1):
            exists = "[green]✓[/]" if Path(dir_path).exists() else "[red]✗[/]"
            console.print(f"  {i}. {dir_path} {exists}")


@session_app.command(
    "save",
    epilog="""
[bold]Examples:[/]
  ait ghostty session save my-project                    # Save with current dir
  ait ghostty session save dev -d "Development setup"    # With description
  ait ghostty session save multi --dirs /path1 /path2    # Multiple directories
""",
)
def session_save(
    name: str = typer.Argument(..., help="Session name."),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Optional description.",
    ),
    dirs: Optional[list[str]] = typer.Option(
        None,
        "--dirs",
        help="Working directories to save.",
    ),
    layout: str = typer.Option(
        "single",
        "--layout",
        "-l",
        help="Layout type (single, split-h, split-v, grid).",
    ),
) -> None:
    """Save current session."""
    from aiterm.terminal import ghostty

    # Check if session already exists
    existing = ghostty.get_session(name)
    if existing:
        console.print(f"[yellow]Session already exists:[/] {name}")
        confirm = typer.confirm("Overwrite?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    working_dirs = list(dirs) if dirs else None

    session = ghostty.create_session(
        name=name,
        working_dirs=working_dirs,
        description=description,
        layout=layout,
    )

    console.print(f"[green]✓[/] Saved session: [bold]{session.name}[/]")
    console.print(f"  Layout: {session.layout}")
    console.print(f"  Directories: {len(session.working_dirs)}")

    session_path = ghostty.get_sessions_dir() / f"{name}.json"
    console.print(f"\n[dim]Saved to: {session_path}[/]")


@session_app.command(
    "restore",
    epilog="""
[bold]Examples:[/]
  ait ghostty session restore my-project   # Restore session
""",
)
def session_restore(
    name: str = typer.Argument(..., help="Session name to restore."),
) -> None:
    """Restore a saved session."""
    from aiterm.terminal import ghostty

    session = ghostty.get_session(name)
    if not session:
        console.print(f"[red]Session not found:[/] {name}")
        raise typer.Exit(1)

    console.print(f"[bold]Restoring session:[/] {name}")
    console.print(f"  Layout: {session.layout}")
    console.print(f"  Directories: {len(session.working_dirs)}")

    # Show directories to restore
    if session.working_dirs:
        console.print("\n[bold]Working directories:[/]")
        for i, dir_path in enumerate(session.working_dirs, 1):
            exists = Path(dir_path).exists()
            status = "[green]✓[/]" if exists else "[red]missing[/]"
            console.print(f"  {i}. {dir_path} {status}")

    # Note about Ghostty limitations
    console.print("\n[yellow]Note:[/] Full session restoration with splits requires")
    console.print("manual setup. Use 'ait ghostty session split' to create splits.")

    # Change to first directory
    if session.working_dirs:
        first_dir = session.working_dirs[0]
        if Path(first_dir).exists():
            console.print(f"\n[dim]Changed to: {first_dir}[/]")
            # Note: os.chdir in a subprocess won't affect parent shell
            # This is informational - user should cd manually
            console.print(f"[bold]Run:[/] cd {first_dir}")


@session_app.command(
    "delete",
    epilog="""
[bold]Examples:[/]
  ait ghostty session delete old-session   # Delete session
""",
)
def session_delete(
    name: str = typer.Argument(..., help="Session name to delete."),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation.",
    ),
) -> None:
    """Delete a saved session."""
    from aiterm.terminal import ghostty

    session = ghostty.get_session(name)
    if not session:
        console.print(f"[red]Session not found:[/] {name}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete session '{name}'?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    if ghostty.delete_session(name):
        console.print(f"[green]✓[/] Deleted session: {name}")
    else:
        console.print(f"[red]Failed to delete session:[/] {name}")
        raise typer.Exit(1)


@session_app.command(
    "split",
    epilog="""
[bold]Examples:[/]
  ait ghostty session split right   # Split horizontally (right)
  ait ghostty session split down    # Split vertically (down)
  ait ghostty session split h       # Alias for right
  ait ghostty session split v       # Alias for down
""",
)
def session_split(
    direction: str = typer.Argument(
        "right",
        help="Split direction (right, down, h, v).",
    ),
) -> None:
    """Create a terminal split."""
    from aiterm.terminal import ghostty

    valid_directions = ["right", "down", "left", "up", "h", "v"]
    if direction.lower() not in valid_directions:
        console.print(f"[red]Invalid direction:[/] {direction}")
        console.print(f"[dim]Valid: {', '.join(valid_directions)}[/]")
        raise typer.Exit(1)

    if ghostty.split_terminal(direction):
        console.print(f"[green]✓[/] Split created: {direction}")
    else:
        if not ghostty.is_ghostty():
            console.print("[yellow]Not running in Ghostty terminal.[/]")
        else:
            console.print("[yellow]Could not create split.[/]")
            console.print("[dim]Ensure Ghostty is focused and has split keybinds configured.[/]")
        raise typer.Exit(1)
