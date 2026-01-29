from dataclasses import dataclass
from typing import List


@dataclass
class Expansion:
    name: str
    factions: List[str]
    enabled: bool = True
