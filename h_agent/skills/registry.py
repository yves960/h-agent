"""
h_agent/skills/registry.py - Skill Registry

Central registry for managing and executing skills.
"""

from typing import Dict, List, Optional
from pathlib import Path
from .base import Skill, SkillContext, SkillResult


class SkillRegistry:
    """Skill registry for registration, lookup, and execution."""

    def __init__(self):
        self.skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self.skills[skill.name] = skill

    def unregister(self, name: str) -> bool:
        """Unregister a skill."""
        if name in self.skills:
            del self.skills[name]
            return True
        return False

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        """List all registered skills."""
        return list(self.skills.values())

    async def execute(self, name: str, context: SkillContext, **kwargs) -> SkillResult:
        """Execute a skill by name."""
        skill = self.get(name)
        if not skill:
            return SkillResult(
                success=False,
                error=f"Skill not found: {name}"
            )

        # Validate parameters
        error = skill.validate_inputs(kwargs)
        if error:
            return SkillResult(success=False, error=error)

        # Execute
        try:
            return await skill.execute(context, **kwargs)
        except Exception as e:
            return SkillResult(success=False, error=str(e))


# Global registry instance
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry."""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
