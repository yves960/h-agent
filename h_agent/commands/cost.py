"""
h_agent/commands/cost.py - /cost Command

Show token usage and cost estimation.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class CostCommand(Command):
    name = "cost"
    description = "Show token usage and cost estimation"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        if not context.engine:
            return CommandResult.err("No engine configured.")

        usage = context.engine.get_usage()
        
        lines = [
            "Token usage:",
            f"  Prompt tokens:     {usage.prompt_tokens:,}",
            f"  Completion tokens: {usage.completion_tokens:,}",
            f"  Total tokens:       {usage.total_tokens:,}",
            f"  Estimated cost:    ${usage.cost_usd:.4f}",
        ]
        
        # Show pricing info
        pricing = context.engine.pricing
        model = context.engine.model
        if model in pricing:
            tier = pricing[model]
            lines.append("")
            lines.append(f"Pricing ({model}):")
            lines.append(f"  Input:  ${tier['input']:.2f} / 1M tokens")
            lines.append(f"  Output: ${tier['output']:.2f} / 1M tokens")
        
        return CommandResult.ok("\n".join(lines))

    def get_help(self) -> str:
        return (
            f"/{self.name} - {self.description}\n"
            f"  Usage: /{self.name}\n"
            f"  Shows token counts and estimated cost"
        )
