"""
h_agent/skills/base.py - Skill Base Classes

Defines the Skill abstract base class and related data classes
for the h-agent skill system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from abc import ABC, abstractmethod
from pathlib import Path


@dataclass
class SkillResult:
    """Result of a skill execution."""
    success: bool
    output: str
    error: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillContext:
    """Execution context passed to skills."""
    working_dir: Path
    messages: List[dict]
    variables: Dict[str, Any] = field(default_factory=dict)

    # Callbacks
    ask_user: Optional[Callable] = None
    run_tool: Optional[Callable] = None


class Skill(ABC):
    """Abstract base class for all skills."""

    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""

    # Input parameter definitions
    parameters: Dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute the skill."""
        pass

    def validate_inputs(self, kwargs: dict) -> Optional[str]:
        """Validate input parameters."""
        for param_name, param_def in self.parameters.items():
            if param_def.get("required", False) and param_name not in kwargs:
                return f"Missing required parameter: {param_name}"
        return None
