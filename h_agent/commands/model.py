"""
h_agent/commands/model.py - /model Command

Show or switch the current model.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class ModelCommand(Command):
    name = "model"
    description = "Show or change the current model"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        if not context.engine:
            return CommandResult.err("No engine configured.")

        if args:
            # Change model
            new_model = args.strip()
            old_model = context.engine.model
            context.engine.model = new_model
            return CommandResult.ok(
                f"Model changed from {old_model} to {new_model}"
            )
        
        # Show current model
        model = context.engine.model
        return CommandResult.ok(f"Current model: {model}")

    def get_help(self) -> str:
        return (
            f"/{self.name} - {self.description}\n"
            f"  Usage: /{self.name} [model]\n"
            f"  Show current model or switch to a new one"
        )
