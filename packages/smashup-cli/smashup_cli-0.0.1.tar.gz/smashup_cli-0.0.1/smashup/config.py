from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .classes import Expansion

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


CONFIG_DIR = Path.home() / ".smashup"
CONFIG_FILE = CONFIG_DIR / "factions.toml"
CONFIG_VERSION = 2


DEFAULT_EXPANSIONS: List[Expansion] = [
    Expansion(
        name="10th Anniversary",
        factions=[
            "Mermaids",
            "Sheep",
            "Skeletons",
            "World Champs",
        ],
    ),
    Expansion(
        name="All Stars Event Kit",
        factions=[
            "Smash Up All Stars",
        ],
    ),
    Expansion(
        name="Awesome Level 9000",
        factions=[
            "Bear Cavalry",
            "Ghosts",
            "Killer Plants",
            "Steampunks",
        ],
    ),
    Expansion(
        name="Big in Japan",
        factions=[
            "Itty Critters",
            "Kaiju",
            "Magical Girls",
            "Mega Troopers",
        ],
    ),
    Expansion(
        name="Cease and Desist",
        factions=[
            "Astroknights",
            "Changerbots",
            "Ignobles",
            "Star Roamers",
        ],
    ),
    Expansion(
        name="Core Set",
        factions=[
            "Aliens",
            "Dinosaurs",
            "Ninjas",
            "Pirates",
            "Robots",
            "Tricksters",
            "Wizards",
            "Zombies",
        ],
    ),
    Expansion(
        name="Excellent Movies, Dudes!",
        factions=[
            "Action Heroes",
            "Backtimers",
            "Extramorphs",
            "Wraithrustlers",
        ],
    ),
    Expansion(
        name="Half the Battle",
        factions=[
            "Adolescent Epic Geckos",
            "G.I. Gerald",
            "Pearl and the Images",
            "Rulers of the Cosmos",
        ],
    ),
    Expansion(
        name="It's Your Fault!",
        factions=[
            "Dragons",
            "Mythic Greeks",
            "Sharks",
            "Superheroes",
            "Tornados",
        ],
    ),
    Expansion(
        name="Monster Smash",
        factions=[
            "Giant Ants",
            "Mad Scientists",
            "Vampires",
            "Werewolves",
        ],
    ),
    Expansion(
        name="Oops, You Did It Again",
        factions=[
            "Ancient Egyptians",
            "Cowboys",
            "Samurai",
            "Vikings",
        ],
    ),
    Expansion(
        name="Pretty Pretty Smash Up",
        factions=[
            "Fairies",
            "Kitty Cats",
            "Mythic Horses",
            "Princesses",
        ],
    ),
    Expansion(
        name="Science Fiction Double Feature",
        factions=[
            "Cyborg Apes",
            "Shapeshifters",
            "Super Spies",
            "Time Travelers",
        ],
    ),
    Expansion(
        name="Smash Up All Stars (pack)",
        factions=[
            "Smash Up All Stars",
        ],
    ),
    Expansion(
        name="Smash Up Goblins",
        factions=[
            "Goblins",
        ],
    ),
    Expansion(
        name="Smash Up Knights of the Round Table",
        factions=[
            "Knights of the Round Table",
        ],
    ),
    Expansion(
        name="Smash Up Penguins",
        factions=[
            "Penguins",
        ],
    ),
    Expansion(
        name="Smash Up Sheep Promo",
        factions=[
            "Sheep",
        ],
    ),
    Expansion(
        name="Smash Up Teens",
        factions=[
            "Teens",
        ],
    ),
    Expansion(
        name="Smash Up: Disney Edition",
        factions=[
            "Aladdin",
            "Beauty and the Beast",
            "Big Hero 6",
            "Frozen",
            "Mulan",
            "The Lion King",
            "The Nightmare Before Christmas",
            "Wreck-It Ralph",
        ],
    ),
    Expansion(
        name="Smash Up: Marvel",
        factions=[
            "Avengers",
            "Hydra",
            "Kree",
            "Masters of Evil",
            "S.H.I.E.L.D.",
            "Sinister Six",
            "Spider-Verse",
            "Ultimates",
        ],
    ),
    Expansion(
        name="Smash Up: Munchkin",
        factions=[
            "Clerics",
            "Dwarves",
            "Elves",
            "Halflings",
            "Mages",
            "Orcs",
            "Thieves",
            "Warriors",
        ],
    ),
    Expansion(
        name="That '70s Expansion",
        factions=[
            "Disco Dancers",
            "Kung Fu Fighters",
            "Truckers",
            "Vigilantes",
        ],
    ),
    Expansion(
        name="The Big Geeky Box",
        factions=[
            "Geeks",
        ],
    ),
    Expansion(
        name="The Bigger Geekier Box",
        factions=[
            "Geeks",
            "Smash Up All Stars",
        ],
    ),
    Expansion(
        name="The Obligatory Cthulhu Set",
        factions=[
            "Elder Things",
            "Innsmouth",
            "Minions of Cthulhu",
            "Miskatonic University",
        ],
    ),
    Expansion(
        name="What Were We Thinking?",
        factions=[
            "Explorers",
            "Grannies",
            "Rock Stars",
            "Teddy Bears",
        ],
    ),
    Expansion(
        name="World Tour Event Kit",
        factions=[
            "Penguins",
        ],
    ),
    Expansion(
        name="World Tour: Culture Shock",
        factions=[
            "Anansi Tales",
            "Ancient Incas",
            "Grimms' Fairy Tales",
            "Polynesian Voyagers",
            "Russian Fairy Tales",
        ],
    ),
    Expansion(
        name="World Tour: International Incident",
        factions=[
            "Luchadors",
            "Mounties",
            "Musketeers",
            "Sumo Wrestlers",
        ],
    ),
]


def ensure_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_EXPANSIONS)
        return
    try:
        data = _read_config_data()
    except OSError:
        return
    version = data.get("version", 0)
    if isinstance(version, int) and version < CONFIG_VERSION:
        try:
            existing = _parse_expansions(data)
        except ValueError:
            return
        merged = _merge_expansions(existing, DEFAULT_EXPANSIONS)
        save_config(merged)


def load_config() -> List[Expansion]:
    data = _read_config_data()
    return _parse_expansions(data)


def save_config(expansions: Iterable[Expansion]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = _serialize_config(expansions)
    CONFIG_FILE.write_text(content, encoding="utf-8")


def _read_config_data() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing config file at {CONFIG_FILE}")
    with CONFIG_FILE.open("rb") as handle:
        return tomllib.load(handle)


def _parse_expansions(data: dict) -> List[Expansion]:
    expansions = data.get("expansions", [])
    if not isinstance(expansions, list) or not expansions:
        raise ValueError("Config file has no expansions defined.")
    parsed: List[Expansion] = []
    for entry in expansions:
        if not isinstance(entry, dict):
            raise ValueError("Expansion entries must be objects.")
        name = str(entry.get("name", "")).strip()
        factions = entry.get("factions", [])
        enabled = entry.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"Expansion '{name}' has invalid enabled flag.")
        if not name:
            raise ValueError("Expansion name cannot be empty.")
        if not isinstance(factions, list) or not factions:
            raise ValueError(f"Expansion '{name}' has no factions defined.")
        faction_names = [str(f).strip() for f in factions if str(f).strip()]
        if not faction_names:
            raise ValueError(f"Expansion '{name}' has no valid factions.")
        parsed.append(Expansion(name=name, factions=faction_names, enabled=enabled))
    return parsed


def _merge_expansions(
    existing: Iterable[Expansion], defaults: Iterable[Expansion]
) -> List[Expansion]:
    existing_by_name = {expansion.name: expansion for expansion in existing}
    merged: List[Expansion] = []
    for default in defaults:
        if default.name in existing_by_name:
            current = existing_by_name.pop(default.name)
            merged.append(
                Expansion(
                    name=default.name,
                    factions=default.factions,
                    enabled=current.enabled,
                )
            )
        else:
            merged.append(default)
    merged.extend(existing_by_name.values())
    return merged


def _serialize_config(expansions: Iterable[Expansion]) -> str:
    lines = [
        "# Smash Up factions and expansions.",
        "# Set enabled = true/false to include an expansion in randomize.",
        f"version = {CONFIG_VERSION}",
    ]
    for expansion in expansions:
        lines.append("")
        lines.append("[[expansions]]")
        lines.append(f"name = {_toml_string(expansion.name)}")
        lines.append(f"enabled = {str(bool(expansion.enabled)).lower()}")
        factions = ", ".join(_toml_string(faction) for faction in expansion.factions)
        lines.append(f"factions = [{factions}]")
    lines.append("")
    return "\n".join(lines)


def _toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
