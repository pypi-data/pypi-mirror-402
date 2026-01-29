"""Interactive configuration menu for statusLine.

This module provides an interactive menu for browsing and editing
statusLine configuration settings.
"""

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from aiterm.statusline.config import StatusLineConfig


class InteractiveConfigMenu:
    """Interactive configuration menu."""

    def __init__(self, config: 'StatusLineConfig'):
        """Initialize interactive menu.

        Args:
            config: StatusLineConfig instance
        """
        self.config = config
        self.console = Console()

    def run(self, category: Optional[str] = None) -> None:
        """Run interactive menu.

        Args:
            category: If provided, show only settings from this category
        """
        while True:
            settings = self.config.list_settings(category=category)

            # Display settings table
            table = self._create_table(settings, category)
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

    def _create_table(self, settings: list[dict], category: Optional[str] = None) -> Table:
        """Create settings table.

        Args:
            settings: List of setting dicts
            category: Category name for title (if filtered)

        Returns:
            Rich Table object
        """
        title = "StatusLine Configuration"
        if category:
            title += f" ({category})"

        table = Table(title=title, show_header=True)

        table.add_column("#", style="dim", width=3)
        table.add_column("Setting", style="cyan")
        table.add_column("Current Value", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Description")

        for idx, setting in enumerate(settings, 1):
            # Format value for display
            value_str = str(setting['value'])
            if isinstance(setting['value'], bool):
                value_str = "✓" if setting['value'] else "✗"

            table.add_row(
                str(idx),
                setting['key'],
                value_str,
                setting['type'],
                setting['description']
            )

        return table

    def _edit_setting(self, setting: dict) -> None:
        """Edit a single setting.

        Args:
            setting: Setting dict with key, value, type, etc.
        """
        key = setting['key']
        current = setting['value']
        schema_def = self.config.get_schema()[key]

        self.console.print(f"\n[bold]Editing:[/] {key}")
        self.console.print(f"[dim]Description: {setting['description']}[/]")
        self.console.print(f"[dim]Current value: {current}[/]")

        # Get new value based on type
        if setting['type'] == 'bool':
            new_value = Confirm.ask("Enable?", default=current)
        elif 'choices' in schema_def:
            choices_str = ", ".join(str(c) for c in schema_def['choices'])
            self.console.print(f"[dim]Choices: {choices_str}[/]")
            new_value = Prompt.ask(
                "New value",
                choices=[str(c) for c in schema_def['choices']],
                default=str(current)
            )
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
        else:
            self.console.print("[dim]No change[/]")
