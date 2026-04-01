"""
h_agent/buddy/types.py - Buddy System Types

Defines species, rarity, eyes, hats, and companion data structures.
"""

from dataclasses import dataclass
from enum import Enum


class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class Species(str, Enum):
    DUCK = "duck"
    GOOSE = "goose"
    BLOB = "blob"
    CAT = "cat"
    DRAGON = "dragon"
    OCTOPUS = "octopus"
    OWL = "owl"
    PENGUIN = "penguin"
    TURTLE = "turtle"
    SNAIL = "snail"
    GHOST = "ghost"
    AXOLOTL = "axolotl"
    CAPYBARA = "capybara"
    CACTUS = "cactus"
    ROBOT = "robot"
    RABBIT = "rabbit"
    MUSHROOM = "mushroom"
    CHONK = "chonk"


class Eye(str, Enum):
    DOT = "·"
    STAR = "✦"
    CROSS = "×"
    CIRCLE = "◉"
    AT = "@"
    DEGREE = "°"


class Hat(str, Enum):
    NONE = "none"
    CROWN = "crown"
    TOPHAT = "tophat"
    PROPELLER = "propeller"
    HALO = "halo"
    WIZARD = "wizard"
    BEANIE = "beanie"
    TINYDUCK = "tinyduck"


class StatName(str, Enum):
    DEBUGGING = "DEBUGGING"
    PATIENCE = "PATIENCE"
    CHAOS = "CHAOS"
    WISDOM = "WISDOM"
    SNARK = "SNARK"


# Collections for random selection
SPECIES_LIST = list(Species)
EYES_LIST = list(Eye)
HATS_LIST = list(Hat)
STAT_NAMES_LIST = list(StatName)
RARITIES_LIST = list(Rarity)

RARITY_WEIGHTS = {
    Rarity.COMMON: 60,
    Rarity.UNCOMMON: 25,
    Rarity.RARE: 10,
    Rarity.EPIC: 4,
    Rarity.LEGENDARY: 1,
}

RARITY_FLOOR = {
    Rarity.COMMON: 5,
    Rarity.UNCOMMON: 15,
    Rarity.RARE: 25,
    Rarity.EPIC: 35,
    Rarity.LEGENDARY: 50,
}

RARITY_STARS = {
    Rarity.COMMON: "★",
    Rarity.UNCOMMON: "★★",
    Rarity.RARE: "★★★",
    Rarity.EPIC: "★★★★",
    Rarity.LEGENDARY: "★★★★★",
}


@dataclass
class CompanionBones:
    """Deterministic parts derived from hash(userId)"""
    rarity: Rarity
    species: Species
    eye: Eye
    hat: Hat
    shiny: bool
    stats: dict  # StatName -> int


@dataclass
class CompanionSoul:
    """AI-generated parts stored after first hatch"""
    name: str
    personality: str


@dataclass
class Companion(CompanionBones, CompanionSoul):
    """Complete companion with bones + soul"""
    hatched_at: float
