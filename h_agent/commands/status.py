"""
h_agent/commands/status.py - /status Command

Show session status and statistics with enhanced features.
"""

import os
import sys
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from h_agent.commands.base import Command, CommandContext, CommandResult


class StatusCommand(Command):
    name = "status"
    description = "Show session status and statistics"
    aliases = ["st", "stat"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        lines = [
            "=" * 60,
            "h-agent Status",
            "=" * 60,
            "",
        ]

        # Session info
        lines.append("📊 Session Information:")
        lines.append(f"  Messages: {len(context.messages)}")
        lines.append(f"  Running: {'Yes' if context.running else 'No'}")

        # Time info
        try:
            start_time = context.get("start_time")
            if start_time:
                elapsed = datetime.now() - start_time
                lines.append(f"  Session time: {elapsed}")
        except Exception:
            pass

        # Engine info
        if context.engine:
            engine = context.engine
            lines.append("")
            lines.append("🔧 Engine:")
            lines.append(f"  Model: {engine.model}")

            usage = engine.get_usage()
            lines.append(f"  Total tokens: {usage.total_tokens:,}")
            lines.append(f"  Cost: ${usage.cost_usd:.4f}")

        # Tool stats
        try:
            from h_agent.tools import get_registry
            registry = get_registry()
            tools = registry.list_tools()
            lines.append("")
            lines.append(f"🛠️  Tools: {len(tools)} registered")

            # Group tools by category
            categories = {}
            for tool in tools:
                cat = tool.get("category", "general")
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1

            for cat, count in categories.items():
                lines.append(f"    {cat}: {count}")
        except Exception as e:
            lines.append(f"  Tools: Error loading ({e})")

        # Command stats
        try:
            from h_agent.commands import get_registry as get_cmd_registry
            cmd_registry = get_cmd_registry()
            lines.append("")
            lines.append(f"📝 Commands: {len(cmd_registry.list_commands())} registered")
        except Exception:
            pass

        # Memory stats
        try:
            from h_agent.memory.long_term import LongTermMemory, MemoryType
            memory = LongTermMemory()
            total = sum(len(entries) for entries in memory._data.values())
            lines.append("")
            lines.append(f"🧠 Memory: {total} entries stored")

            # Show breakdown
            for mem_type in [MemoryType.USER, MemoryType.PROJECT, MemoryType.DECISION]:
                entries = memory._data.get(mem_type, [])
                if entries:
                    lines.append(f"    {mem_type}: {len(entries)}")
        except Exception:
            pass

        # System stats
        lines.append("")
        lines.append("💻 System:")

        # Memory usage
        try:
            if HAS_PSUTIL:
                process = psutil.Process(os.getpid())
                mem_info = process.memory_info()
                mem_mb = mem_info.rss / 1024 / 1024
                lines.append(f"  Memory: {mem_mb:.1f} MB")
            else:
                lines.append("  Memory: (psutil not installed)")
        except Exception:
            pass

        # Python version
        lines.append(f"  Python: {sys.version.split()[0]}")

        # Platform
        try:
            import platform
            lines.append(f"  Platform: {platform.system()}")
        except Exception:
            pass

        # Active tasks
        lines.append("")
        lines.append("📋 Active Tasks:")
        try:
            from h_agent.tasks import get_active_tasks
            tasks = get_active_tasks()
            if tasks:
                for task in tasks[:5]:  # Show max 5
                    lines.append(f"  • {task}")
            else:
                lines.append("  (none)")
        except Exception:
            lines.append("  (unavailable)")

        # Config profile
        lines.append("")
        lines.append("⚙️  Config:")
        try:
            from h_agent.core.config import get_current_profile
            profile = get_current_profile()
            lines.append(f"  Profile: {profile}")
        except Exception:
            pass

        try:
            from h_agent.core.config import MODEL_ID
            lines.append(f"  Model: {MODEL_ID}")
        except Exception:
            pass

        lines.append("")
        lines.append("=" * 60)

        return CommandResult(
            success=True,
            output="\n".join(lines)
        )

    def get_help(self) -> str:
        return f"""/{self.name} - {self.description}

Shows comprehensive status information including:
  - Session statistics (messages, tokens, cost)
  - Engine configuration
  - Registered tools and commands
  - Memory usage
  - System information
  - Active tasks

Usage:
  /{self.name}

This command provides a quick overview of the current session
and system state. Use /usage for detailed token/cost breakdown.
"""
