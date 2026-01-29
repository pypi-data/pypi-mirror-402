import pytest

from smashup.classes import Expansion
from smashup.randomizer import collect_factions, randomize_factions


def test_collect_factions_skips_disabled_and_dedupes() -> None:
    expansions = [
        Expansion(name="Alpha", factions=["Aliens", "Dinosaurs"]),
        Expansion(name="Beta", factions=["Aliens", "Zombies"]),
        Expansion(name="Gamma", factions=["Robots"], enabled=False),
    ]

    result = collect_factions(expansions)

    assert result == ["Aliens", "Dinosaurs", "Zombies"]


def test_randomize_factions_assigns_unique() -> None:
    expansions = [
        Expansion(
            name="Core",
            factions=["A", "B", "C", "D", "E", "F"],
        )
    ]

    assignments = randomize_factions(expansions, players=2, factions_per_player=2)
    flat = [faction for group in assignments for faction in group]

    assert len(assignments) == 2
    assert len(assignments[0]) == 2
    assert len(assignments[1]) == 2
    assert len(flat) == 4
    assert len(set(flat)) == 4


def test_randomize_factions_requires_enough_factions() -> None:
    expansions = [
        Expansion(
            name="Core",
            factions=["A", "B", "C"],
        )
    ]

    with pytest.raises(ValueError):
        randomize_factions(expansions, players=2, factions_per_player=2)


def test_randomize_factions_validates_inputs() -> None:
    expansions = [
        Expansion(
            name="Core",
            factions=["A", "B", "C", "D"],
        )
    ]

    with pytest.raises(ValueError):
        randomize_factions(expansions, players=0, factions_per_player=1)

    with pytest.raises(ValueError):
        randomize_factions(expansions, players=1, factions_per_player=0)
