import random
from typing import List, Sequence

from .classes import Expansion


def collect_factions(expansions: Sequence[Expansion]) -> List[str]:
    available: List[str] = []
    seen = set()
    for expansion in expansions:
        if not expansion.enabled:
            continue
        for faction in expansion.factions:
            if faction in seen:
                continue
            seen.add(faction)
            available.append(faction)
    if not available:
        raise ValueError("No factions available. Enable at least one expansion.")
    return available


def randomize_factions(
    expansions: Sequence[Expansion],
    players: int,
    factions_per_player: int,
) -> List[List[str]]:
    if players <= 0:
        raise ValueError("Players must be at least 1.")
    if factions_per_player <= 0:
        raise ValueError("Factions per player must be at least 1.")
    available = collect_factions(expansions)
    total_needed = players * factions_per_player
    if total_needed > len(available):
        raise ValueError(
            f"Need {total_needed} factions but only {len(available)} are available."
        )
    rng = random.SystemRandom()
    selected = rng.sample(available, total_needed)
    assignments = []
    for i in range(players):
        start = i * factions_per_player
        assignments.append(selected[start : start + factions_per_player])
    return assignments
