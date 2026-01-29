from typing import Optional

import click
from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog, message_dialog
from prompt_toolkit.styles import Style
from rich import box
from rich.console import Console
from rich.table import Table

from . import config
from .randomizer import randomize_factions


console = Console()
dialog_style = Style.from_dict(
    {
        "dialog": "bg:#ffffff #000000",
        "dialog.body": "bg:#ffffff #000000",
        "dialog.body text-area": "bg:#ffffff #000000",
        "dialog shadow": "bg:#ffffff",
        "dialog.body shadow": "bg:#ffffff",
        "checkbox-selected": "reverse",
        "button.focused": "reverse",
    }
)


@click.group()
def main() -> None:
    """Smash Up deck helper."""


@main.command()
def configure() -> None:
    """Configure which expansions are available."""
    config.ensure_config()
    try:
        expansions = config.load_config()
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    values = [
        (expansion.name, f"{expansion.name} ({len(expansion.factions)} factions)")
        for expansion in expansions
    ]
    default_values = [expansion.name for expansion in expansions if expansion.enabled]
    selected = checkboxlist_dialog(
        title="Smash Up Configuration",
        text=(
            "Use Up/Down to move, Enter to toggle selection. "
            "Press Tab to reach Save/Cancel."
        ),
        ok_text="Save",
        cancel_text="Cancel",
        values=values,
        default_values=default_values,
        style=dialog_style,
    ).run()
    if selected is None:
        console.print("No changes made.")
        return

    selected_set = set(selected)
    for expansion in expansions:
        expansion.enabled = expansion.name in selected_set
    config.save_config(expansions)
    enabled_count = sum(1 for expansion in expansions if expansion.enabled)
    console.print(
        f"Enabled {enabled_count}/{len(expansions)} expansions. Saved to {config.CONFIG_FILE}"
    )


@main.command()
def randomize() -> None:
    """Randomly assign factions to players."""
    config.ensure_config()
    players = _prompt_positive_int("Number of players", "Enter number of players:")
    if players is None:
        return
    factions_per_player = _prompt_positive_int(
        "Factions per player",
        "Enter factions per player:",
    )
    if factions_per_player is None:
        return
    try:
        expansions = config.load_config()
        assignments = randomize_factions(expansions, players, factions_per_player)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    table = Table(title="Smash Up Factions", box=box.SIMPLE, show_lines=True)
    table.add_column("Player", style="bold")
    table.add_column("Factions")
    for index, factions in enumerate(assignments, start=1):
        table.add_row(f"Player {index}", ", ".join(factions))
    console.print(table)


def _prompt_positive_int(title: str, prompt: str) -> Optional[int]:
    while True:
        response = input_dialog(title=title, text=prompt, style=dialog_style).run()
        if response is None:
            return None
        text = response.strip()
        if text.isdigit() and int(text) > 0:
            return int(text)
        message_dialog(
            title="Invalid input",
            text="Please enter a positive whole number.",
            style=dialog_style,
        ).run()


if __name__ == "__main__":
    main()
