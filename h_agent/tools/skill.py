"""
h_agent/tools/skill.py - Skill Tool

Tool for executing skills through the registry.
"""

from pathlib import Path
from h_agent.tools.base import Tool, ToolResult
from h_agent.skills import get_skill_registry, SkillContext


class SkillTool(Tool):
    """Execute a registered skill."""

    name = "skill"
    description = "Execute a skill by name"
    concurrency_safe = True

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Skill name"},
                "arguments": {"type": "object", "description": "Skill arguments"}
            },
            "required": ["name"]
        }

    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        registry = get_skill_registry()
        skill_name = args["name"]
        skill_args = args.get("arguments", {})

        context = SkillContext(
            working_dir=Path.cwd(),
            messages=[]
        )

        result = await registry.execute(skill_name, context, **skill_args)

        return ToolResult(
            success=result.success,
            output=result.output,
            error=result.error
        )
