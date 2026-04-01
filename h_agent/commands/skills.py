"""
h_agent/commands/skills.py - /skills command
"""

from h_agent.commands.base import Command, CommandResult, CommandContext
from h_agent.skills import get_skill_registry


class SkillsCommand(Command):
    name = "skills"
    description = "Manage skills"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        registry = get_skill_registry()

        if not args or args == "list":
            skills = registry.list_skills()
            lines = ["Available skills:"]
            for skill in skills:
                lines.append(f"  {skill.name}: {skill.description}")

            if not skills:
                lines.append("  (none)")

            return CommandResult(success=True, output="\n".join(lines))

        elif args.startswith("info "):
            skill_name = args[5:].strip()
            skill = registry.get(skill_name)
            if not skill:
                return CommandResult(success=False, output=f"Skill not found: {skill_name}")

            lines = [
                f"Name: {skill.name}",
                f"Description: {skill.description}",
                f"Version: {skill.version}",
                f"Parameters:",
            ]
            for param, defn in skill.parameters.items():
                required = " (required)" if defn.get("required") else ""
                lines.append(f"  {param}: {defn.get('description', '')}{required}")

            return CommandResult(success=True, output="\n".join(lines))

        return CommandResult(success=False, output=f"Unknown skills command: {args}")
