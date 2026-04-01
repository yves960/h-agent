"""
h_agent/commands/history.py - /history Command

Show conversation history.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class HistoryCommand(Command):
    name = "history"
    description = "Show conversation history"
    aliases = ["hist"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        messages = context.messages

        if not messages:
            return CommandResult.ok("No conversation history.")

        # Parse limit from args
        limit = 10
        if args:
            try:
                limit = int(args.strip())
                if limit < 1:
                    limit = 10
            except ValueError:
                pass

        # Show last N messages
        total = len(messages)
        start = max(0, total - limit)
        shown = messages[start:]

        lines = [f"Conversation ({total} messages, showing last {len(shown)}):"]
        
        for i, msg in enumerate(shown, start + 1):
            role = msg.get("role", "?")
            content = msg.get("content", "")
            
            # Handle tool calls
            if "tool_calls" in msg:
                tool_names = [
                    tc.get("function", {}).get("name", "?")
                    for tc in msg["tool_calls"]
                ]
                content = f"[tool calls: {', '.join(tool_names)}]"
            elif isinstance(content, list):
                content = "[complex content]"
            elif not content:
                content = "[empty]"
            
            # Truncate long content
            if len(content) > 80:
                content = content[:77] + "..."
            
            lines.append(f"  [{i}] {role}: {content}")

        return CommandResult.ok("\n".join(lines))

    def get_help(self) -> str:
        return (
            f"/{self.name} - {self.description}\n"
            f"  Usage: /{self.name} [limit]\n"
            f"  Show conversation history (default: last 10 messages)"
        )
