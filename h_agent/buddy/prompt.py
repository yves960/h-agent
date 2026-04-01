"""
h_agent/buddy/prompt.py - Companion Prompt Generation

Prompts for AI to generate companion names and personalities.
"""

from h_agent.buddy.types import Species


def companion_intro_text(name: str, species: str) -> str:
    """Text to inject into system prompt about the companion."""
    return f"""# Companion

A small {species} named {name} sits beside the user's input box and occasionally comments in a speech bubble. You're not {name} — it's a separate watcher.

When the user addresses {name} directly (by name), its bubble will answer. Your job in that moment is to stay out of the way: respond in ONE line or less, or just answer any part of the message meant for you. Don't explain that you're not {name} — they know. Don't narrate what {name} might say — the bubble handles that."""


def get_hatch_prompt(species: Species, inspiration_seed: int) -> str:
    """Prompt for the hatching event when user first gets a companion."""
    return f"""The user's companion is about to hatch! Generate a fun hatching moment.

Species: {species.value}

Create a brief, exciting hatching narrative (2-3 sentences) that:
- Describes the egg/item cracking
- Shows what emerges
- Ends with the companion looking at the user expectantly

Inspiration seed: {inspiration_seed}

Respond with only the hatching narrative."""


def get_name_prompt(species: Species, inspiration_seed: int) -> str:
    """Prompt for AI to generate companion name."""
    species_descriptions = {
        Species.DUCK: "a fluffy yellow duck with wobbly steps",
        Species.GOOSE: "a majestic goose with excellent posture",
        Species.BLOB: "a jiggly blob that changes shape",
        Species.CAT: "a curious cat with expressive eyes",
        Species.DRAGON: "a tiny dragon with big dreams",
        Species.OCTOPUS: "a purple octopus with tentacles",
        Species.OWL: "a wise owl with fluffy feathers",
        Species.PENGUIN: "a dapper penguin in formal wear",
        Species.TURTLE: "a patient turtle with a shell house",
        Species.SNAIL: "a speedy snail (for a snail)",
        Species.GHOST: "a friendly ghost who's not scary",
        Species.AXOLOTL: "a pink axolotl with feathery gills",
        Species.CAPYBARA: "a chill capybara who's friends with everyone",
        Species.CACTUS: "a spiky cactus with a soft heart",
        Species.ROBOT: "a small robot with curiosity circuits",
        Species.RABBIT: "a fluffy rabbit with big ears",
        Species.MUSHROOM: "a cute mushroom with spots",
        Species.CHONK: "a round, fluffy chonk of unknown origin",
    }
    
    desc = species_descriptions.get(species, f"a {species.value}")
    
    return f"""The user just hatched {desc} as their coding companion!

Generate a short, memorable name (1-3 words, easy to say):
- 2-4 syllables
- Cute but not childish
- Unique but pronounceable
- Fun to say aloud

Inspiration seed: {inspiration_seed}

Respond with ONLY the name, no explanation or punctuation."""


def get_personality_prompt(species: Species, stats: dict, inspiration_seed: int) -> str:
    """Prompt for AI to generate companion personality."""
    stats_str = ", ".join(f"{k}: {v}/100" for k, v in stats.items())
    
    return f"""Generate a personality for a {species.value} coding companion.

Stats ({stats_str}):
- DEBUGGING: How good at finding bugs (higher = more helpful)
- PATIENCE: How patient they are with mistakes (higher = calmer)
- CHAOS: How mischievous they are (higher = more chaotic)
- WISDOM: How insightful their advice (higher = wiser)
- SNARK: How sarcastic their comments (higher = snarkier)

Create a 1-2 sentence personality description that:
- Has a distinct voice
- References their stats in a fun way
- Would make a fun coding buddy

Inspiration seed: {inspiration_seed}

Respond with ONLY the personality description."""
