"""
h_agent/commands/usage.py - /usage Command

Show detailed usage statistics including token usage, costs, and session info.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class UsageCommand(Command):
    name = "usage"
    description = "Show usage statistics and cost breakdown"
    aliases = ["stats", "usage"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute usage command."""
        lines = ["📊 Usage Statistics:\n"]

        # Session info
        lines.append(f"Messages in session: {len(context.messages)}")

        # Engine stats
        if context.engine:
            engine = context.engine
            lines.append(f"\n🔧 Engine Info:")
            lines.append(f"  Model: {engine.model}")

            usage = engine.get_usage()
            lines.append(f"\n💰 Token Usage:")
            lines.append(f"  Prompt tokens:     {usage.prompt_tokens:,}")
            lines.append(f"  Completion tokens: {usage.completion_tokens:,}")
            lines.append(f"  Total tokens:      {usage.total_tokens:,}")
            lines.append(f"  Estimated cost:    ${usage.cost_usd:.4f}")

            # Pricing info
            pricing = engine.pricing
            model = engine.model
            if model in pricing:
                tier = pricing[model]
                lines.append(f"\n💵 Pricing ({model}):")
                lines.append(f"  Input:  ${tier['input']:.2f} / 1M tokens")
                lines.append(f"  Output: ${tier['output']:.2f} / 1M tokens")

        # Tool stats
        try:
            from h_agent.tools import get_registry
            registry = get_registry()
            tools = registry.list_tools()
            lines.append(f"\n🛠️ Tools: {len(tools)} registered")
        except Exception:
            pass

        # Command stats
        try:
            from h_agent.commands import get_registry as get_cmd_registry
            cmd_registry = get_cmd_registry()
            lines.append(f"📝 Commands: {len(cmd_registry.list_commands())} registered")
        except Exception:
            pass

        # Memory stats
        try:
            from h_agent.memory.long_term import LongTermMemory, MemoryType
            memory = LongTermMemory()
            total_memories = sum(len(entries) for entries in memory._data.values())
            lines.append(f"🧠 Memories: {total_memories} stored")
        except Exception:
            pass

        # Show per-model usage if we have historical data
        lines.append("\n📈 Model Usage Summary:")
        lines.append(f"  Current: {context.engine.model if context.engine else 'N/A'}")

        # Estimate monthly usage based on session
        if context.engine:
            session_tokens = context.engine.get_usage().total_tokens
            lines.append(f"  Session tokens: ~{session_tokens:,}")
            session_cost = context.engine.get_usage().cost_usd
            lines.append(f"  Session cost: ~${session_cost:.4f}")

        return CommandResult.ok("\n".join(lines))

    def get_help(self) -> str:
        return f"""/{self.name} - {self.description}

Shows detailed usage statistics including:
  - Token usage (prompt, completion, total)
  - Cost estimation
  - Model pricing
  - Session statistics
  - Memory count
  - Tools and commands registered

Usage:
  /{self.name}

This command provides a comprehensive overview of your current session's
resource usage and estimated costs.
"""
