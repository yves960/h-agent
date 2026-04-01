"""
h_agent/buddy/display.py - Terminal Display for Companions

Renders companions and their info for terminal output.
"""

from typing import Optional

from h_agent.buddy.types import Companion, Rarity, RARITY_STARS
from h_agent.buddy.sprites import render_sprite, sprite_frame_count


# ANSI Colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Rarity colors
    COMMON = "\033[90m"      # Bright black/gray
    UNCOMMON = "\033[32m"     # Green
    RARE = "\033[34m"         # Blue
    EPIC = "\033[35m"         # Magenta
    LEGENDARY = "\033[33m"    # Yellow/Gold
    
    # Special
    SHINY = "\033[93m"        # Bright yellow
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"


RARITY_COLORS = {
    Rarity.COMMON: Colors.COMMON,
    Rarity.UNCOMMON: Colors.UNCOMMON,
    Rarity.RARE: Colors.RARE,
    Rarity.EPIC: Colors.EPIC,
    Rarity.LEGENDARY: Colors.LEGENDARY,
}


def get_rarity_color(rarity: Rarity) -> str:
    """Get ANSI color code for a rarity."""
    return RARITY_COLORS.get(rarity, Colors.RESET)


def format_stats(stats: dict) -> str:
    """Format companion stats for display."""
    lines = []
    for name, value in stats.items():
        bar = "█" * (value // 10) + "░" * (10 - value // 10)
        lines.append(f"  {name}: [{bar}] {value}")
    return "\n".join(lines)


def format_companion_card(companion: Companion, frame: int = 0) -> str:
    """
    Format a complete companion card for display.
    
    Args:
        companion: The companion to display
        frame: Animation frame (0, 1, 2) for fidget animation
    
    Returns:
        Formatted string with sprite, name, rarity, stats
    """
    color = get_rarity_color(companion.rarity)
    stars = RARITY_STARS[companion.rarity]
    
    # Render sprite
    sprite_lines = render_sprite(companion, frame)
    
    # Build card
    lines = []
    
    # Header with name and rarity
    shiny_prefix = "✨ " if companion.shiny else ""
    lines.append(f"{color}{Colors.BOLD}{shiny_prefix}{companion.name}{Colors.RESET} {color}{stars}{Colors.RESET}")
    lines.append(f"{color}{companion.rarity.value.upper()}{Colors.RESET}")
    
    # Sprite
    for line in sprite_lines:
        lines.append(f"{color}{line}{Colors.RESET}")
    
    # Stats
    lines.append("")
    lines.append(f"{Colors.DIM}Stats:{Colors.RESET}")
    lines.append(format_stats(companion.stats))
    
    # Personality (if set)
    if companion.personality and companion.personality != "???":
        lines.append("")
        lines.append(f"{Colors.DIM}Personality:{Colors.RESET} {companion.personality}")
    
    return "\n".join(lines)


def format_companion_mini(companion: Companion, frame: int = 0) -> str:
    """
    Compact companion display for inline display (e.g., next to prompt).
    
    Args:
        companion: The companion to display
        frame: Animation frame for fidget animation
    
    Returns:
        Single-line or compact multi-line representation
    """
    color = get_rarity_color(companion.rarity)
    sprite_lines = render_sprite(companion, frame)
    
    # Just show sprite with name below
    lines = []
    for line in sprite_lines:
        lines.append(f"{color}{line}{Colors.RESET}")
    
    shiny_prefix = "✨ " if companion.shiny else ""
    lines.append(f"{color}{shiny_prefix}{companion.name}{Colors.RESET}")
    
    return "\n".join(lines)


def format_companion_bubble(companion: Companion, message: str) -> str:
    """
    Format a speech bubble from the companion.
    
    Args:
        companion: The speaking companion
        message: What the companion says
    
    Returns:
        Formatted speech bubble
    """
    color = Colors.CYAN
    
    # Simple bubble
    bubble = [
        f"{color} {companion.name}:{Colors.RESET}",
        f"{color}┌{'─' * (len(message) + 2)}┐{Colors.RESET}",
        f"{color}│ {message} │{Colors.RESET}",
        f"{color}└{'─' * (len(message) + 2)}┘{Colors.RESET}",
    ]
    
    return "\n".join(bubble)


def get_prompt_suffix(companion: Companion, frame: int = 0) -> str:
    """
    Get the companion suffix for display next to user input.
    
    Args:
        companion: The companion to display
        frame: Animation frame
    
    Returns:
        Compact string to append to prompt
    """
    color = get_rarity_color(companion.rarity)
    sprite = render_sprite(companion, frame)
    
    # Return first few lines of sprite, right-aligned
    suffix = ""
    for line in sprite[:3]:  # Just first 3 lines for compactness
        suffix += f"{color}{line}{Colors.RESET}\n"
    
    return suffix


def animate_companion(companion: Companion, frames: int = 3, delay: float = 0.3) -> list[str]:
    """
    Generate animation frames for a companion.
    
    Args:
        companion: The companion to animate
        frames: Number of frames to generate
        delay: Delay between frames (for potential animation)
    
    Returns:
        List of frame strings
    """
    frame_count = sprite_frame_count(companion.species)
    result = []
    
    for i in range(frames):
        frame = i % frame_count
        result.append(format_companion_card(companion, frame))
    
    return result
