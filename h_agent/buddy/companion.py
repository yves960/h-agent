"""
h_agent/buddy/companion.py - Companion Generation

Deterministic companion generation from user ID.
Based on Claude Code's companion.ts implementation.
"""

import hashlib
import random
import time
from typing import Optional, Tuple

from h_agent.buddy.types import (
    CompanionBones,
    CompanionSoul,
    Companion,
    Rarity,
    Species,
    Eye,
    Hat,
    StatName,
    SPECIES_LIST,
    EYES_LIST,
    HATS_LIST,
    STAT_NAMES_LIST,
    RARITIES_LIST,
    RARITY_WEIGHTS,
    RARITY_FLOOR,
)


SALT = "friend-2026-401"


def hash_string(s: str) -> int:
    """Hash a string to a 32-bit integer."""
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def mulberry32(seed: int):
    """Mulberry32 - seeded PRNG for deterministic random selection."""
    def generator():
        nonlocal seed
        seed = (seed + 0x6d2b79f5) & 0xFFFFFFFF
        t = (seed ^ (seed >> 15)) * (1 | seed)
        t = (t ^ (t >> 7)) * (1 | t)
        t = (t ^ (t >> 14))
        return (t & 0xFFFFFFFF) / 4294967296
    return generator


def pick(rng, arr):
    """Pick a random element from a list using the seeded RNG."""
    return arr[int(rng() * len(arr))]


def roll_rarity(rng) -> Rarity:
    """Roll for rarity using weighted probabilities."""
    total = sum(RARITY_WEIGHTS.values())
    roll = rng() * total
    for rarity in RARITIES_LIST:
        roll -= RARITY_WEIGHTS[rarity]
        if roll < 0:
            return rarity
    return Rarity.COMMON


def roll_stats(rng, rarity: Rarity) -> dict:
    """Generate stats with one peak, one dump, rest scattered."""
    floor = RARITY_FLOOR[rarity]
    
    # Pick peak and dump stats
    peak = pick(rng, STAT_NAMES_LIST)
    dump = pick(rng, STAT_NAMES_LIST)
    while dump == peak:
        dump = pick(rng, STAT_NAMES_LIST)
    
    stats = {}
    for name in STAT_NAMES_LIST:
        if name == peak:
            stats[name.value] = min(100, floor + 50 + int(rng() * 30))
        elif name == dump:
            stats[name.value] = max(1, floor - 10 + int(rng() * 15))
        else:
            stats[name.value] = floor + int(rng() * 40)
    
    return stats


def roll_bones(rng) -> CompanionBones:
    """Roll deterministic companion bones (rarity, species, eye, hat, shiny, stats)."""
    rarity = roll_rarity(rng)
    
    bones = CompanionBones(
        rarity=rarity,
        species=pick(rng, SPECIES_LIST),
        eye=pick(rng, EYES_LIST),
        hat=Hat.NONE if rarity == Rarity.COMMON else pick(rng, HATS_LIST),
        shiny=rng() < 0.01,  # 1% chance
        stats=roll_stats(rng, rarity),
    )
    
    return bones


# Cache for deterministic results
_roll_cache: Optional[Tuple[str, CompanionBones, int]] = None


def roll(user_id: str) -> Tuple[CompanionBones, int]:
    """
    Roll companion bones for a user ID.
    Results are cached for performance.
    
    Returns:
        Tuple of (CompanionBones, inspiration_seed)
    """
    global _roll_cache
    
    key = user_id + SALT
    
    if _roll_cache is not None and _roll_cache[0] == key:
        return _roll_cache[1], _roll_cache[2]
    
    seed = hash_string(key)
    rng = mulberry32(seed)
    bones = roll_bones(rng)
    inspiration_seed = int(rng() * 1e9)
    
    _roll_cache = (key, bones, inspiration_seed)
    return bones, inspiration_seed


def roll_with_seed(seed_str: str) -> Tuple[CompanionBones, int]:
    """Roll companion with a specific seed string (for testing)."""
    seed = hash_string(seed_str)
    rng = mulberry32(seed)
    bones = roll_bones(rng)
    inspiration_seed = int(rng() * 1e9)
    return bones, inspiration_seed


def generate_companion(user_id: str, soul: Optional[CompanionSoul] = None) -> Companion:
    """
    Generate a complete companion from user ID and optional soul.
    
    Args:
        user_id: Unique user identifier
        soul: Optional CompanionSoul (name, personality) from stored config
    
    Returns:
        Full Companion with bones + soul
    """
    bones, _ = roll(user_id)
    
    if soul is None:
        soul = CompanionSoul(
            name="???",  # Placeholder until AI generates
            personality="???",
        )
    
    return Companion(
        rarity=bones.rarity,
        species=bones.species,
        eye=bones.eye,
        hat=bones.hat,
        shiny=bones.shiny,
        stats=bones.stats,
        name=soul.name,
        personality=soul.personality,
        hatched_at=time.time(),
    )


def get_default_user_id() -> str:
    """Get default user ID for standalone use."""
    return "default-user"


# Name generation prompts (for AI to use)
def get_name_prompt(species: Species, inspiration_seed: int) -> str:
    """Generate prompt for AI to create companion name."""
    return f"""Generate a cute, memorable name for a {species.value} companion.
The name should be:
- 2-4 syllables
- Easy to say
- Match the companion's species traits
- Unique but not weird

Inspiration seed: {inspiration_seed}

Respond with only the name, nothing else."""


def get_personality_prompt(species: Species, stats: dict, inspiration_seed: int) -> str:
    """Generate prompt for AI to create companion personality."""
    stats_str = ", ".join(f"{k}: {v}" for k, v in stats.items())
    
    return f"""Generate a personality description for a {species.value} companion.
Stats: {stats_str}

The personality should:
- Be 1-2 sentences
- Reference the stats in a fun way
- Have a distinct voice (snarky, wise, chaotic, patient, etc.)
- Be endearing but not generic

Inspiration seed: {inspiration_seed}

Respond with only the personality description, nothing else."""
