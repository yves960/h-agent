"""
h_agent/skills/loader.py - Skill Loader

Loads skills from Python files and YAML definitions.
"""

import yaml
import importlib.util
import sys
from pathlib import Path
from typing import List
from .base import Skill, SkillResult
from .registry import get_skill_registry


def load_skill_from_file(path: Path) -> Skill:
    """Load a skill from a Python file."""
    spec = importlib.util.spec_from_file_location("skill_module", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load spec from {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["skill_module"] = module
    spec.loader.exec_module(module)

    # Find Skill subclass
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, Skill) and attr is not Skill:
            return attr()

    raise ValueError(f"No Skill class found in {path}")


def load_skill_from_yaml(path: Path) -> Skill:
    """Load a skill from a YAML file (declarative)."""
    with open(path) as f:
        data = yaml.safe_load(f)

    class YAMLSkill(Skill):
        name = data["name"]
        description = data.get("description", "")
        parameters = data.get("parameters", {})
        steps = data.get("steps", [])

        async def execute(self, ctx, **kwargs):
            output_parts = []
            for step in self.steps:
                if step["type"] == "prompt":
                    prompt = step["template"].format(**kwargs)
                    output_parts.append(prompt)
                elif step["type"] == "tool":
                    # Tool invocation placeholder
                    pass
            return SkillResult(
                success=True,
                output="\n".join(output_parts)
            )

    return YAMLSkill()


def load_skills_from_dir(dir_path: Path) -> List[Skill]:
    """Load all skills from a directory."""
    skills = []

    for path in dir_path.glob("**/*.py"):
        try:
            skill = load_skill_from_file(path)
            skills.append(skill)
        except Exception as e:
            print(f"Failed to load skill from {path}: {e}")

    for path in dir_path.glob("**/*.skill.yaml"):
        try:
            skill = load_skill_from_yaml(path)
            skills.append(skill)
        except Exception as e:
            print(f"Failed to load skill from {path}: {e}")

    return skills


def register_builtin_skills() -> None:
    """Register built-in skills."""
    from .builtin import code_review, test_runner

    registry = get_skill_registry()
    registry.register(code_review.CodeReviewSkill())
    registry.register(test_runner.TestRunnerSkill())
