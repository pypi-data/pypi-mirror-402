"""Craft plugin management commands for Claude Code."""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Craft plugin management for Claude Code.")
console = Console()

# Constants
PLUGINS_DIR = Path.home() / ".claude" / "plugins"
CRAFT_PLUGIN_DIR = PLUGINS_DIR / "craft"
CRAFT_SOURCE_DIR = Path.home() / "projects" / "dev-tools" / "claude-plugins" / "craft"


def get_craft_config() -> Optional[dict]:
    """Get the craft plugin configuration."""
    # Try plugin.json first (newer format), then config.json (older format)
    for filename in ["plugin.json", "config.json"]:
        config_file = CRAFT_PLUGIN_DIR / ".claude-plugin" / filename
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except (json.JSONDecodeError, IOError):
                pass
    return None


def get_craft_version() -> Optional[str]:
    """Get the installed craft plugin version."""
    config = get_craft_config()
    return config.get("version") if config else None


def is_craft_installed() -> bool:
    """Check if craft plugin is installed."""
    return CRAFT_PLUGIN_DIR.exists()


def get_craft_commands() -> list[str]:
    """Get list of available craft commands."""
    commands_dir = CRAFT_PLUGIN_DIR / "commands"
    if not commands_dir.exists():
        return []

    commands = []
    for item in sorted(commands_dir.iterdir()):
        if item.is_dir():
            # Subdirectory = command namespace (e.g., git, docs)
            commands.append(item.name)
        elif item.suffix == ".md":
            # Markdown file = command (e.g., check.md)
            commands.append(item.stem)
    return commands


def get_craft_skills() -> list[str]:
    """Get list of available craft skills."""
    skills_dir = CRAFT_PLUGIN_DIR / "skills"
    if not skills_dir.exists():
        return []

    return sorted([d.name for d in skills_dir.iterdir() if d.is_dir()])


def get_craft_agents() -> list[str]:
    """Get list of available craft agents."""
    agents_dir = CRAFT_PLUGIN_DIR / "agents"
    if not agents_dir.exists():
        return []

    agents = []
    for item in sorted(agents_dir.iterdir()):
        if item.suffix == ".md":
            agents.append(item.stem)
    return agents


@app.command()
def status():
    """Show craft plugin status and overview."""
    if not is_craft_installed():
        print("[red]Craft plugin is not installed[/red]")
        print("\nInstall with: [cyan]ait craft install[/cyan]")
        raise typer.Exit(1)

    config = get_craft_config()
    version = config.get("version", "unknown") if config else "unknown"
    description = config.get("description", "") if config else ""

    # Check if it's a symlink
    is_symlink = CRAFT_PLUGIN_DIR.is_symlink()
    source_path = os.readlink(CRAFT_PLUGIN_DIR) if is_symlink else str(CRAFT_PLUGIN_DIR)

    # Get counts
    commands = get_craft_commands()
    skills = get_craft_skills()
    agents = get_craft_agents()

    # Build status panel
    status_text = f"""[bold]Craft Plugin[/bold] v{version}

[dim]{description}[/dim]

[bold]Location:[/bold] {CRAFT_PLUGIN_DIR}
[bold]Source:[/bold] {source_path}
[bold]Type:[/bold] {'Symlink' if is_symlink else 'Directory'}

[bold]Components:[/bold]
  Commands: {len(commands)}
  Skills: {len(skills)}
  Agents: {len(agents)}"""

    print(Panel(status_text, title="Craft Status", border_style="cyan"))


@app.command("list")
def list_commands(
    commands_only: bool = typer.Option(False, "--commands", "-c", help="Show only commands"),
    skills_only: bool = typer.Option(False, "--skills", "-s", help="Show only skills"),
    agents_only: bool = typer.Option(False, "--agents", "-a", help="Show only agents"),
):
    """List available craft commands, skills, and agents."""
    if not is_craft_installed():
        print("[red]Craft plugin is not installed[/red]")
        raise typer.Exit(1)

    show_all = not (commands_only or skills_only or agents_only)

    if show_all or commands_only:
        commands = get_craft_commands()
        table = Table(title="Craft Commands", show_header=True)
        table.add_column("Command", style="cyan")
        table.add_column("Type")

        commands_dir = CRAFT_PLUGIN_DIR / "commands"
        for cmd in commands:
            cmd_path = commands_dir / cmd
            if cmd_path.is_dir():
                # Count subcommands
                subcmds = len([f for f in cmd_path.iterdir() if f.suffix == ".md"])
                table.add_row(f"/craft:{cmd}", f"Namespace ({subcmds} subcommands)")
            else:
                table.add_row(f"/craft:{cmd}", "Command")

        console.print(table)
        print()

    if show_all or skills_only:
        skills = get_craft_skills()
        table = Table(title="Craft Skills", show_header=True)
        table.add_column("Skill", style="green")
        table.add_column("Category")

        for skill in skills:
            table.add_row(skill, "Skill Category")

        console.print(table)
        print()

    if show_all or agents_only:
        agents = get_craft_agents()
        table = Table(title="Craft Agents", show_header=True)
        table.add_column("Agent", style="yellow")

        for agent in agents:
            table.add_row(agent)

        console.print(table)


@app.command()
def install(
    source: Optional[Path] = typer.Option(
        None, "--source", "-s",
        help="Source directory for craft plugin"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install or reinstall craft plugin."""
    if is_craft_installed() and not force:
        print("[yellow]Craft plugin is already installed[/yellow]")
        print("Use --force to reinstall")
        raise typer.Exit(0)

    # Determine source
    source_dir = source or CRAFT_SOURCE_DIR
    if not source_dir.exists():
        print(f"[red]Source directory not found: {source_dir}[/red]")
        raise typer.Exit(1)

    # Ensure plugins directory exists
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    # Remove existing if force
    if force and CRAFT_PLUGIN_DIR.exists():
        if CRAFT_PLUGIN_DIR.is_symlink():
            CRAFT_PLUGIN_DIR.unlink()
        else:
            import shutil
            shutil.rmtree(CRAFT_PLUGIN_DIR)
        print("[dim]Removed existing installation[/dim]")

    # Create symlink
    try:
        CRAFT_PLUGIN_DIR.symlink_to(source_dir)
        print(f"[green]Craft plugin installed[/green]")
        print(f"  Source: {source_dir}")
        print(f"  Link: {CRAFT_PLUGIN_DIR}")

        # Show version
        version = get_craft_version()
        if version:
            print(f"  Version: {version}")
    except OSError as e:
        print(f"[red]Failed to create symlink: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update():
    """Update craft plugin (git pull in source directory)."""
    if not is_craft_installed():
        print("[red]Craft plugin is not installed[/red]")
        raise typer.Exit(1)

    # Get source directory
    if not CRAFT_PLUGIN_DIR.is_symlink():
        print("[yellow]Craft is not installed as symlink, cannot auto-update[/yellow]")
        raise typer.Exit(1)

    source_dir = Path(os.readlink(CRAFT_PLUGIN_DIR))
    if not source_dir.exists():
        print(f"[red]Source directory not found: {source_dir}[/red]")
        raise typer.Exit(1)

    # Check if it's a git repo
    git_dir = source_dir / ".git"
    if not git_dir.exists():
        print("[yellow]Source is not a git repository[/yellow]")
        raise typer.Exit(1)

    # Get current version
    old_version = get_craft_version()

    # Run git pull
    print(f"[dim]Updating from {source_dir}...[/dim]")
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=source_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[red]Git pull failed: {result.stderr}[/red]")
            raise typer.Exit(1)

        print(result.stdout)

        # Check new version
        new_version = get_craft_version()
        if old_version != new_version:
            print(f"[green]Updated: {old_version} → {new_version}[/green]")
        else:
            print(f"[green]Already up to date: v{new_version}[/green]")

    except FileNotFoundError:
        print("[red]Git not found in PATH[/red]")
        raise typer.Exit(1)


@app.command()
def sync(
    project_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Project type (auto-detected if not specified)"
    ),
):
    """Sync craft configuration with project context.

    Analyzes the current project and suggests craft commands/modes.
    """
    if not is_craft_installed():
        print("[red]Craft plugin is not installed[/red]")
        raise typer.Exit(1)

    # Detect project type
    from aiterm.context.detector import detect_context

    cwd = Path.cwd()
    context = detect_context(cwd)
    detected_type = project_type or context.type.value

    print(f"[bold]Project Context[/bold]")
    print(f"  Directory: {cwd}")
    print(f"  Type: {detected_type}")
    print()

    # Suggest relevant craft commands based on project type
    suggestions = {
        "python": ["/craft:test:run", "/craft:code:lint", "/craft:docs:generate"],
        "node": ["/craft:test:run", "/craft:code:lint", "/craft:ci:validate"],
        "r-package": ["/craft:test:run", "/craft:docs:generate"],
        "git": ["/craft:git:worktree", "/craft:git:clean"],
    }

    recommended = suggestions.get(detected_type, ["/craft:check", "/craft:smart-help"])

    print("[bold]Recommended Commands:[/bold]")
    for cmd in recommended:
        print(f"  [cyan]{cmd}[/cyan]")

    # Check for craft modes
    print()
    print("[bold]Available Modes:[/bold]")
    modes = ["default", "debug", "optimize", "release"]
    for mode in modes:
        print(f"  [dim]{mode}[/dim]")

    print()
    print("[dim]Set mode with: /craft:mode <name>[/dim]")


@app.command("run")
def run_command(
    command: str = typer.Argument(..., help="Craft command to run (e.g., 'check', 'test:run')"),
    args: Optional[str] = typer.Argument(None, help="Additional arguments"),
):
    """Execute a craft command (requires active Claude Code session).

    Note: Craft commands run within Claude Code context. This command
    shows how to invoke them but cannot execute them directly.
    """
    if not is_craft_installed():
        print("[red]Craft plugin is not installed[/red]")
        raise typer.Exit(1)

    # Normalize command
    if not command.startswith("/craft:"):
        command = f"/craft:{command}"

    full_command = f"{command} {args}" if args else command

    print(Panel(
        f"""[bold]Craft Command:[/bold] [cyan]{full_command}[/cyan]

[dim]To run this command:[/dim]

1. Start Claude Code: [yellow]claude[/yellow]
2. Enter the command: [cyan]{full_command}[/cyan]

Or use the Skill tool in Claude Code to invoke craft skills.""",
        title="Run Craft Command",
        border_style="cyan"
    ))


@app.command()
def commands(
    namespace: Optional[str] = typer.Argument(None, help="Show commands in namespace (e.g., 'git', 'docs')"),
):
    """Show detailed craft command information."""
    if not is_craft_installed():
        print("[red]Craft plugin is not installed[/red]")
        raise typer.Exit(1)

    commands_dir = CRAFT_PLUGIN_DIR / "commands"

    if namespace:
        # Show commands in specific namespace
        ns_dir = commands_dir / namespace
        if not ns_dir.exists():
            print(f"[red]Namespace not found: {namespace}[/red]")
            raise typer.Exit(1)

        print(f"[bold]/craft:{namespace} Commands[/bold]\n")
        for item in sorted(ns_dir.iterdir()):
            if item.suffix == ".md":
                cmd_name = item.stem
                # Read first line for description
                first_line = item.read_text().split("\n")[0].strip("# ")
                print(f"  [cyan]/craft:{namespace}:{cmd_name}[/cyan]")
                print(f"    {first_line}")

    else:
        # Show all top-level namespaces
        print("[bold]Craft Command Namespaces[/bold]\n")
        for item in sorted(commands_dir.iterdir()):
            if item.is_dir():
                subcmds = len([f for f in item.iterdir() if f.suffix == ".md"])
                print(f"  [cyan]/craft:{item.name}[/cyan] ({subcmds} commands)")
            elif item.suffix == ".md":
                first_line = item.read_text().split("\n")[0].strip("# ")
                print(f"  [cyan]/craft:{item.stem}[/cyan]")
                print(f"    {first_line}")

        print("\n[dim]Use 'ait craft commands <namespace>' for details[/dim]")
