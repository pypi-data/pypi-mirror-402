"""Interactive tutorial system for aiterm.

Provides progressive learning tutorials with 3 levels:
- Getting Started (7 steps, ~10 min)
- Intermediate (11 steps, ~20 min)
- Advanced (13 steps, ~35 min)

Based on the Nexus CLI tutorial pattern.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box
import questionary

console = Console()


class TutorialLevel(Enum):
    """Tutorial difficulty levels."""

    GETTING_STARTED = "getting-started"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    @property
    def display_name(self) -> str:
        """Human-readable level name."""
        names = {
            TutorialLevel.GETTING_STARTED: "Getting Started",
            TutorialLevel.INTERMEDIATE: "Intermediate",
            TutorialLevel.ADVANCED: "Advanced",
        }
        return names[self]

    @property
    def step_count(self) -> int:
        """Number of steps in this level."""
        counts = {
            TutorialLevel.GETTING_STARTED: 7,
            TutorialLevel.INTERMEDIATE: 11,
            TutorialLevel.ADVANCED: 13,
        }
        return counts[self]

    @property
    def duration(self) -> str:
        """Estimated duration."""
        durations = {
            TutorialLevel.GETTING_STARTED: "~10 min",
            TutorialLevel.INTERMEDIATE: "~20 min",
            TutorialLevel.ADVANCED: "~35 min",
        }
        return durations[self]

    @property
    def description(self) -> str:
        """Level description."""
        descriptions = {
            TutorialLevel.GETTING_STARTED: "Essential commands and basic setup",
            TutorialLevel.INTERMEDIATE: "Claude Code, workflows, and sessions",
            TutorialLevel.ADVANCED: "Release automation, craft, and integrations",
        }
        return descriptions[self]


@dataclass
class TutorialStep:
    """A single step in a tutorial."""

    number: int
    title: str
    description: str
    command: Optional[str] = None
    hint: Optional[str] = None
    interactive: bool = False
    gif_path: Optional[str] = None
    diagram: Optional[str] = None
    validate: Optional[Callable[[], bool]] = None
    follow_up: Optional[str] = None


@dataclass
class Tutorial:
    """A complete tutorial with multiple steps."""

    level: TutorialLevel
    title: str
    description: str
    prerequisites: List[str] = field(default_factory=list)
    steps: List[TutorialStep] = field(default_factory=list)

    def show_intro(self) -> None:
        """Display tutorial introduction."""
        console.print()
        console.print(Panel(
            f"[bold]{self.title}[/bold]\n\n"
            f"{self.description}\n\n"
            f"[dim]Steps:[/] {len(self.steps)} | "
            f"[dim]Duration:[/] {self.level.duration}",
            title=f"📚 {self.level.display_name} Tutorial",
            border_style="cyan",
        ))

        if self.prerequisites:
            console.print()
            console.print("[bold]Prerequisites:[/]")
            for prereq in self.prerequisites:
                console.print(f"  • {prereq}")

        console.print()

    def show_step(self, step_num: int) -> TutorialStep:
        """Display a specific step."""
        if step_num < 1 or step_num > len(self.steps):
            raise ValueError(f"Step {step_num} not found. Valid: 1-{len(self.steps)}")

        step = self.steps[step_num - 1]

        # Step header
        console.print()
        console.print(Panel(
            f"[bold]{step.title}[/bold]\n\n"
            f"{step.description}",
            title=f"Step {step.number}/{len(self.steps)}",
            border_style="green",
        ))

        # Command to run
        if step.command:
            console.print()
            console.print(f"[bold cyan]Command:[/] [green]{step.command}[/]")

        # Hint
        if step.hint:
            console.print()
            console.print(f"[dim]💡 Hint: {step.hint}[/]")

        # Follow-up command
        if step.follow_up:
            console.print()
            console.print(f"[dim]📎 Follow-up: {step.follow_up}[/]")

        return step

    def run(self, start_step: int = 1) -> bool:
        """Run the tutorial interactively."""
        self.show_intro()

        # Confirm start
        if start_step == 1:
            if not questionary.confirm(
                "Ready to start?",
                default=True,
            ).ask():
                console.print("[yellow]Tutorial cancelled.[/]")
                return False
        else:
            console.print(f"[cyan]Resuming from step {start_step}...[/]")

        # Run through steps
        current_step = start_step
        while current_step <= len(self.steps):
            step = self.show_step(current_step)

            # Interactive prompt
            if step.interactive and step.command:
                console.print()
                console.print("[bold]Try running the command above, then continue.[/]")

            # Navigation options
            console.print()
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "Continue to next step",
                    "Repeat this step",
                    "Skip to a specific step",
                    "Exit tutorial",
                ],
            ).ask()

            if action == "Continue to next step":
                current_step += 1
            elif action == "Repeat this step":
                pass  # Stay on current step
            elif action == "Skip to a specific step":
                try:
                    new_step = int(questionary.text(
                        f"Enter step number (1-{len(self.steps)}):",
                    ).ask())
                    if 1 <= new_step <= len(self.steps):
                        current_step = new_step
                    else:
                        console.print(f"[red]Invalid step. Must be 1-{len(self.steps)}[/]")
                except (ValueError, TypeError):
                    console.print("[red]Invalid input.[/]")
            elif action == "Exit tutorial":
                console.print(f"[yellow]Exiting. Resume later with: ait learn {self.level.value} --step {current_step}[/]")
                return False

        # Completion
        self.show_completion()
        return True

    def show_completion(self) -> None:
        """Display completion message."""
        console.print()
        console.print(Panel(
            f"[bold green]🎉 Congratulations![/]\n\n"
            f"You've completed the [bold]{self.level.display_name}[/] tutorial!\n\n"
            f"[dim]Steps completed:[/] {len(self.steps)}\n"
            f"[dim]Level:[/] {self.level.value}",
            title="Tutorial Complete",
            border_style="green",
        ))

        # Next level suggestion
        if self.level == TutorialLevel.GETTING_STARTED:
            console.print()
            console.print("[cyan]Next:[/] Try the Intermediate tutorial:")
            console.print("  [green]ait learn intermediate[/]")
        elif self.level == TutorialLevel.INTERMEDIATE:
            console.print()
            console.print("[cyan]Next:[/] Try the Advanced tutorial:")
            console.print("  [green]ait learn advanced[/]")


# ============================================
# Tutorial Content Factories
# ============================================

def create_getting_started_tutorial() -> Tutorial:
    """Create the Getting Started tutorial (7 steps)."""
    return Tutorial(
        level=TutorialLevel.GETTING_STARTED,
        title="Getting Started with aiterm",
        description="Learn the essential commands to optimize your terminal for AI-assisted development.",
        prerequisites=[
            "aiterm installed (run 'ait doctor' to verify)",
            "iTerm2, Ghostty, or another supported terminal",
        ],
        steps=[
            TutorialStep(
                number=1,
                title="What is aiterm?",
                description=(
                    "aiterm is a terminal optimizer for AI-assisted development. "
                    "It manages terminal profiles, context detection, and integrates "
                    "with Claude Code, Gemini CLI, and other AI tools."
                ),
                hint="aiterm works best with iTerm2 on macOS",
            ),
            TutorialStep(
                number=2,
                title="Check Your Installation",
                description="Verify that aiterm is correctly installed and all dependencies are available.",
                command="ait doctor",
                interactive=True,
                hint="All checks should pass. If not, follow the suggestions.",
                gif_path="docs/demos/tutorials/getting-started-01-doctor.gif",
            ),
            TutorialStep(
                number=3,
                title="View Configuration",
                description="See your current aiterm configuration and settings.",
                command="ait config show",
                interactive=True,
                hint="Configuration is stored in ~/.config/aiterm/",
            ),
            TutorialStep(
                number=4,
                title="Detect Project Context",
                description=(
                    "aiterm automatically detects your project type based on files "
                    "like DESCRIPTION (R), pyproject.toml (Python), or package.json (Node)."
                ),
                command="ait detect",
                interactive=True,
                hint="Try running this in different project directories",
                gif_path="docs/demos/tutorials/getting-started-02-detect.gif",
            ),
            TutorialStep(
                number=5,
                title="Switch Terminal Profile",
                description="Apply the detected context to your terminal, changing colors and status bar.",
                command="ait switch",
                interactive=True,
                hint="Your terminal should visually change based on context",
                gif_path="docs/demos/tutorials/getting-started-03-switch.gif",
            ),
            TutorialStep(
                number=6,
                title="Explore Commands",
                description="See all available aiterm commands and their descriptions.",
                command="ait --help",
                interactive=True,
                hint="Each command has its own --help for detailed usage",
            ),
            TutorialStep(
                number=7,
                title="Next Steps",
                description=(
                    "You've learned the basics! Here's what to explore next:\n\n"
                    "• Claude Code integration: ait claude --help\n"
                    "• Workflow automation: ait workflows --help\n"
                    "• Session management: ait sessions --help"
                ),
                hint="Try the Intermediate tutorial for deeper features",
            ),
        ],
    )


def create_intermediate_tutorial() -> Tutorial:
    """Create the Intermediate tutorial (11 steps)."""
    return Tutorial(
        level=TutorialLevel.INTERMEDIATE,
        title="Intermediate aiterm Features",
        description="Master Claude Code integration, workflows, sessions, and terminal management.",
        prerequisites=[
            "Completed Getting Started tutorial",
            "Claude Code CLI installed (optional but recommended)",
        ],
        steps=[
            TutorialStep(
                number=1,
                title="Claude Code Settings",
                description="View and manage your Claude Code configuration.",
                command="ait claude settings",
                interactive=True,
                hint="Settings are stored in ~/.claude/settings.json",
                gif_path="docs/demos/tutorials/intermediate-01-claude.gif",
            ),
            TutorialStep(
                number=2,
                title="Backup Your Settings",
                description="Create a backup of your Claude Code settings before making changes.",
                command="ait claude backup",
                interactive=True,
                hint="Backups are timestamped and stored safely",
            ),
            TutorialStep(
                number=3,
                title="Auto-Approval Presets",
                description="View available auto-approval presets for Claude Code commands.",
                command="ait claude approvals list",
                interactive=True,
                hint="Presets range from minimal to comprehensive",
            ),
            TutorialStep(
                number=4,
                title="Add Safe Approvals",
                description="Apply the 'safe' preset for common read-only operations.",
                command="ait claude approvals add safe",
                interactive=True,
                hint="The 'safe' preset includes git, npm, and common tools",
            ),
            TutorialStep(
                number=5,
                title="Workflow Basics",
                description="See built-in workflows for common development tasks.",
                command="ait workflows list",
                interactive=True,
                hint="Workflows automate multi-step processes",
                gif_path="docs/demos/tutorials/intermediate-02-workflows.gif",
            ),
            TutorialStep(
                number=6,
                title="Feature Branch Workflow",
                description="Use the feature workflow for structured development.",
                command="ait feature status",
                interactive=True,
                hint="Feature workflow tracks branch state and progress",
            ),
            TutorialStep(
                number=7,
                title="Session Management",
                description="View active Claude Code sessions across projects.",
                command="ait sessions live",
                interactive=True,
                hint="Sessions help coordinate parallel work",
                gif_path="docs/demos/tutorials/intermediate-03-sessions.gif",
            ),
            TutorialStep(
                number=8,
                title="Terminal Management Overview",
                description="See supported terminals and their features.",
                command="ait terminal list",
                interactive=True,
                hint="aiterm supports iTerm2, Ghostty, and more",
            ),
            TutorialStep(
                number=9,
                title="Detect Your Terminal",
                description="Identify which terminal you're currently using.",
                command="ait terminal detect",
                interactive=True,
                hint="Terminal detection happens automatically in most cases",
            ),
            TutorialStep(
                number=10,
                title="Ghostty Quick Themes",
                description="If using Ghostty, explore quick theme switching.",
                command="ait ghostty themes",
                interactive=True,
                hint="Skip if not using Ghostty terminal",
            ),
            TutorialStep(
                number=11,
                title="Status Bar Customization",
                description="Learn about status bar variables and customization.",
                command="ait status-bar show",
                interactive=True,
                hint="Status bars show context, time, and session info",
            ),
        ],
    )


def create_advanced_tutorial() -> Tutorial:
    """Create the Advanced tutorial (13 steps)."""
    return Tutorial(
        level=TutorialLevel.ADVANCED,
        title="Advanced aiterm Power User Techniques",
        description="Master release automation, craft integration, and advanced configurations.",
        prerequisites=[
            "Completed Intermediate tutorial",
            "Familiarity with git and release processes",
            "Craft plugin installed (optional)",
        ],
        steps=[
            TutorialStep(
                number=1,
                title="Release Automation Overview",
                description="aiterm v0.5.0+ includes 7 release commands for PyPI and Homebrew.",
                command="ait release --help",
                hint="7 commands: check, status, pypi, homebrew, tag, notes, full",
                gif_path="docs/demos/tutorials/advanced-01-release.gif",
            ),
            TutorialStep(
                number=2,
                title="Pre-Release Validation",
                description="Validate version consistency, tests, and changelog before releasing.",
                command="ait release check",
                interactive=True,
                hint="Run this before every release to catch issues early",
            ),
            TutorialStep(
                number=3,
                title="Release Status & Notes",
                description="See current version, pending commits, and generate release notes.",
                command="ait release status",
                interactive=True,
                follow_up="ait release notes",
            ),
            TutorialStep(
                number=4,
                title="Full Release Workflow",
                description="Understand the complete release workflow from check to publish.",
                command="ait release full --help",
                hint="Use --dry-run first: ait release full 0.6.0 --dry-run",
            ),
            TutorialStep(
                number=5,
                title="Custom Workflow Creation",
                description="Build your own automation workflows in YAML format.",
                command="ait workflows custom create my-workflow",
                interactive=True,
                hint="Workflows stored in ~/.config/aiterm/workflows/",
            ),
            TutorialStep(
                number=6,
                title="Workflow Chaining",
                description="Chain multiple workflows with the + separator.",
                command="ait workflows run lint+test+build --dry-run",
                interactive=True,
                hint="Stops on first failure, great for pre-commit checks",
            ),
            TutorialStep(
                number=7,
                title="Craft Integration Overview",
                description="Craft extends aiterm with 68 commands, 17 skills, 7 agents.",
                command="ait craft status",
                hint="Craft provides AI-powered development workflows",
                gif_path="docs/demos/tutorials/advanced-03-craft.gif",
            ),
            TutorialStep(
                number=8,
                title="Craft Git Worktrees",
                description="Work on multiple branches simultaneously without switching.",
                command="# /craft:git:worktree setup",
                hint="Create worktrees for feature + hotfix at same time",
                gif_path="docs/demos/tutorials/advanced-02-worktrees.gif",
            ),
            TutorialStep(
                number=9,
                title="MCP Server Management",
                description="View and manage MCP servers for Claude Code.",
                command="ait mcp list",
                interactive=True,
                follow_up="ait mcp status",
            ),
            TutorialStep(
                number=10,
                title="IDE Integrations",
                description="See supported IDEs and their integration status.",
                command="ait ide list",
                hint="Use ait ide configure <ide> to set up integration",
            ),
            TutorialStep(
                number=11,
                title="Advanced Debugging",
                description="Get detailed diagnostic information in JSON format.",
                command="ait info --json",
                hint="Use --json for programmatic parsing",
            ),
            TutorialStep(
                number=12,
                title="Custom Configurations",
                description="Edit config.toml directly for advanced customization.",
                command="ait config edit",
                interactive=True,
                hint="See docs/reference/configuration.md for all options",
            ),
            TutorialStep(
                number=13,
                title="Next Steps & Resources",
                description=(
                    "You're now a power user! Resources:\n\n"
                    "• GitHub: https://github.com/Data-Wise/aiterm\n"
                    "• Docs: https://data-wise.github.io/aiterm\n"
                    "• Craft: /craft:hub for all commands"
                ),
                hint="Check ait --help periodically - new features added regularly!",
            ),
        ],
    )


# ============================================
# Tutorial Registry & Helpers
# ============================================

def get_tutorial(level: TutorialLevel) -> Tutorial:
    """Get a tutorial by level."""
    factories = {
        TutorialLevel.GETTING_STARTED: create_getting_started_tutorial,
        TutorialLevel.INTERMEDIATE: create_intermediate_tutorial,
        TutorialLevel.ADVANCED: create_advanced_tutorial,
    }
    return factories[level]()


def list_tutorials() -> None:
    """Display all available tutorials."""
    console.print()
    console.print(Panel(
        "[bold]Interactive Tutorials[/]\n\n"
        "Learn aiterm through hands-on, step-by-step guides.",
        title="📚 ait learn",
        border_style="cyan",
    ))

    table = Table(box=box.ROUNDED)
    table.add_column("Level", style="cyan")
    table.add_column("Steps", justify="center")
    table.add_column("Duration", justify="center")
    table.add_column("Description")

    for level in TutorialLevel:
        table.add_row(
            level.value,
            str(level.step_count),
            level.duration,
            level.description,
        )

    console.print(table)
    console.print()
    console.print("[bold]Usage:[/]")
    console.print("  ait learn                            # List tutorials")
    console.print("  ait learn start getting-started      # Start tutorial")
    console.print("  ait learn start intermediate -s 5    # Resume from step")
    console.print("  ait learn info advanced              # Show tutorial details")
    console.print()


def parse_level(level_str: str) -> Optional[TutorialLevel]:
    """Parse a level string to TutorialLevel enum."""
    level_str = level_str.lower().strip()

    # Empty string is invalid
    if not level_str:
        return None

    # Direct match
    for level in TutorialLevel:
        if level.value == level_str:
            return level

    # Partial match (requires at least 3 chars for safety)
    if len(level_str) >= 3:
        for level in TutorialLevel:
            if level_str in level.value:
                return level

    return None
