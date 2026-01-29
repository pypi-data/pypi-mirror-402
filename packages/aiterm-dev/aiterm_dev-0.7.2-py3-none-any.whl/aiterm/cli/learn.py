"""CLI commands for interactive tutorials."""

from typing import Optional

import typer
from rich.console import Console

from aiterm.utils.tutorial import (
    TutorialLevel,
    get_tutorial,
    list_tutorials,
    parse_level,
)

app = typer.Typer(
    help="Interactive tutorials for learning aiterm.",
    invoke_without_command=True,
)

console = Console()


def _run_tutorial(level_str: str, step: int = 1) -> None:
    """Run a tutorial by level string."""
    tutorial_level = parse_level(level_str)
    if tutorial_level is None:
        console.print(f"[red]Unknown tutorial level: {level_str}[/]")
        console.print("[dim]Available: getting-started, intermediate, advanced[/]")
        raise typer.Exit(1)

    # Get and run the tutorial
    tutorial = get_tutorial(tutorial_level)

    # Validate step number
    if step < 1 or step > len(tutorial.steps):
        console.print(f"[red]Invalid step: {step}[/]")
        console.print(f"[dim]Valid steps: 1-{len(tutorial.steps)}[/]")
        raise typer.Exit(1)

    # Run tutorial
    completed = tutorial.run(start_step=step)

    if not completed:
        raise typer.Exit(0)  # User exited, but not an error


@app.callback(invoke_without_command=True)
def learn_callback(ctx: typer.Context) -> None:
    """
    Interactive tutorials for learning aiterm.

    Run 'ait learn' to see available tutorials, or 'ait learn start <level>' to start one.
    """
    if ctx.invoked_subcommand is None:
        # Show list of tutorials
        list_tutorials()


@app.command("list")
def learn_list() -> None:
    """List all available tutorials."""
    list_tutorials()


@app.command(
    "start",
    epilog="""
[bold]Examples:[/]
  ait learn start getting-started      # Start beginner tutorial
  ait learn start intermediate         # Start intermediate tutorial
  ait learn start advanced --step 5    # Resume from step 5
"""
)
def learn_start(
    level: str = typer.Argument(..., help="Tutorial level: getting-started, intermediate, or advanced."),
    step: int = typer.Option(
        1,
        "--step",
        "-s",
        help="Start from a specific step (for resuming).",
    ),
) -> None:
    """Start an interactive tutorial."""
    _run_tutorial(level, step)


@app.command("info")
def learn_info(
    level: str = typer.Argument(..., help="Tutorial level to get info about."),
) -> None:
    """Show detailed information about a specific tutorial."""
    tutorial_level = parse_level(level)
    if tutorial_level is None:
        console.print(f"[red]Unknown tutorial level: {level}[/]")
        raise typer.Exit(1)

    tutorial = get_tutorial(tutorial_level)

    # Show intro without running
    tutorial.show_intro()

    # Show step list
    console.print("[bold]Steps:[/]")
    for step in tutorial.steps:
        cmd_hint = f" [dim]({step.command})[/]" if step.command else ""
        console.print(f"  {step.number}. {step.title}{cmd_hint}")

    console.print()
    console.print(f"[cyan]Start:[/] ait learn start {level}")
