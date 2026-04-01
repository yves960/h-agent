"""
h_agent/buddy - Buddy System

A companion system for h-agent, inspired by Claude Code's buddy implementation.
Provides pet companions with unique species, rarities, and personalities.
"""

from h_agent.buddy.types import (
    Rarity,
    Species,
    Eye,
    Hat,
    StatName,
    CompanionBones,
    CompanionSoul,
    Companion,
    SPECIES_LIST,
    EYES_LIST,
    HATS_LIST,
    STAT_NAMES_LIST,
    RARITIES_LIST,
    RARITY_WEIGHTS,
    RARITY_FLOOR,
    RARITY_STARS,
)

from h_agent.buddy.companion import (
    roll,
    roll_with_seed,
    generate_companion,
    get_default_user_id,
    get_name_prompt,
    get_personality_prompt,
)

from h_agent.buddy.sprites import (
    render_sprite,
    sprite_frame_count,
    render_face,
)

from h_agent.buddy.display import (
    format_companion_card,
    format_companion_mini,
    format_companion_bubble,
    get_prompt_suffix,
    animate_companion,
    Colors,
)

__all__ = [
    # Types
    "Rarity",
    "Species",
    "Eye",
    "Hat",
    "StatName",
    "CompanionBones",
    "CompanionSoul",
    "Companion",
    "SPECIES_LIST",
    "EYES_LIST",
    "HATS_LIST",
    "STAT_NAMES_LIST",
    "RARITIES_LIST",
    "RARITY_WEIGHTS",
    "RARITY_FLOOR",
    "RARITY_STARS",
    # Companion generation
    "roll",
    "roll_with_seed",
    "generate_companion",
    "get_default_user_id",
    "get_name_prompt",
    "get_personality_prompt",
    # Sprites
    "render_sprite",
    "sprite_frame_count",
    "render_face",
    # Display
    "format_companion_card",
    "format_companion_mini",
    "format_companion_bubble",
    "get_prompt_suffix",
    "animate_companion",
    "Colors",
]
