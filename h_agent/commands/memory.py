"""
h_agent/commands/memory.py - /memory Command

Manage persistent memory for user preferences, project info, and decisions.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class MemoryCommand(Command):
    name = "memory"
    description = "Manage persistent memory"
    aliases = ["mem"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute memory command with subcommands."""
        parts = args.strip().split(maxsplit=1)
        if not parts:
            return self._show_help()

        subcmd = parts[0].lower()
        subargs = parts[1] if len(parts) > 1 else ""

        if subcmd in ("list", "ls", "l"):
            return await self._list_memories()
        elif subcmd in ("add", "a", "set"):
            if not subargs:
                return CommandResult.err("Usage: /memory add <text>")
            return await self._add_memory(subargs)
        elif subcmd in ("search", "s", "find"):
            if not subargs:
                return CommandResult.err("Usage: /memory search <query>")
            return await self._search_memory(subargs)
        elif subcmd in ("clear", "c", "reset"):
            return await self._clear_memory()
        elif subcmd in ("stats", "st", "info"):
            return await self._stats_memory()
        elif subcmd in ("help", "h", "?"):
            return self._show_help()
        else:
            return CommandResult.err(f"Unknown subcommand: {subcmd}. Use /memory help for usage.")

    def _show_help(self) -> CommandResult:
        """Show help for memory command."""
        help_text = """Usage: /memory <subcommand>

Subcommands:
  /memory list              List all memories
  /memory add <text>        Add a new memory (user type)
  /memory search <query>    Search memories
  /memory stats             Show memory statistics
  /memory clear             Clear all memories

Examples:
  /memory add User prefers dark theme
  /memory search dark theme
  /memory list
"""
        return CommandResult.ok(help_text)

    async def _list_memories(self) -> CommandResult:
        """List all memories."""
        try:
            from h_agent.memory.long_term import LongTermMemory, MemoryType

            memory = LongTermMemory()
            lines = ["📚 Memories:\n"]

            for mem_type in [MemoryType.USER, MemoryType.PROJECT, MemoryType.DECISION, MemoryType.FACT, MemoryType.ERROR]:
                entries = memory._data.get(mem_type, [])
                if entries:
                    type_label = {
                        MemoryType.USER: "👤 User Preferences",
                        MemoryType.PROJECT: "📁 Project Info",
                        MemoryType.DECISION: "⚖️ Decisions",
                        MemoryType.FACT: "📝 Facts",
                        MemoryType.ERROR: "🐛 Errors & Solutions",
                    }.get(mem_type, mem_type)
                    lines.append(f"\n{type_label}:")
                    for entry in entries:
                        key = entry.get("key", "unknown")
                        value = entry.get("value", "")
                        created = entry.get("created_at", "")[:10]
                        lines.append(f"  [{created}] {key}: {value}")

            if len(lines) == 1:
                lines.append("  (No memories stored yet)")

            lines.append("\nUse /memory add <text> to add a memory.")

            return CommandResult.ok("\n".join(lines))
        except Exception as e:
            return CommandResult.err(f"Failed to list memories: {e}")

    async def _add_memory(self, text: str) -> CommandResult:
        """Add a new memory."""
        try:
            from h_agent.memory.long_term import remember, MemoryType

            # Parse the text to determine type and key
            # Simple format: "type: key = value" or just "text"
            parts = text.split("=", 1)
            if len(parts) == 2:
                key_part = parts[0].strip()
                value = parts[1].strip()
                # Determine type from prefix
                if ":" in key_part:
                    type_str, key = key_part.split(":", 1)
                    type_str = type_str.lower().strip()
                    if type_str == "user":
                        mem_type = MemoryType.USER
                    elif type_str == "project":
                        mem_type = MemoryType.PROJECT
                    elif type_str == "decision":
                        mem_type = MemoryType.DECISION
                    elif type_str == "fact":
                        mem_type = MemoryType.FACT
                    elif type_str == "error":
                        mem_type = MemoryType.ERROR
                    else:
                        mem_type = MemoryType.USER
                        key = key_part
                else:
                    mem_type = MemoryType.USER
                    key = key_part
            else:
                # Just a text, use timestamp as key
                from datetime import datetime
                key = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                value = text.strip()

            remember(mem_type, key, value)
            return CommandResult.ok(f"✅ Memory added: [{mem_type}] {key} = {value}")
        except Exception as e:
            return CommandResult.err(f"Failed to add memory: {e}")

    async def _search_memory(self, query: str) -> CommandResult:
        """Search memories."""
        try:
            from h_agent.memory.long_term import search_memory

            results = search_memory(query)

            if not results:
                return CommandResult.ok(f"No memories found matching: '{query}'")

            lines = [f"🔍 Search results for '{query}':\n"]
            for result in results:
                mem_type = result.get("type", "unknown")
                key = result.get("key", "unknown")
                value = result.get("value", "")
                lines.append(f"  [{mem_type}] {key}: {value}")

            return CommandResult.ok("\n".join(lines))
        except Exception as e:
            return CommandResult.err(f"Failed to search memories: {e}")

    async def _clear_memory(self) -> CommandResult:
        """Clear all memories (requires confirmation via context)."""
        # This should be enhanced with confirmation in real CLI usage
        try:
            from h_agent.memory.long_term import LongTermMemory, MemoryType

            memory = LongTermMemory()
            total = sum(len(entries) for entries in memory._data.values())

            if total == 0:
                return CommandResult.ok("No memories to clear.")

            # Actually clear the memories
            for mem_type in memory._data:
                memory._data[mem_type] = []
            memory._save()

            return CommandResult.ok(f"✅ Cleared {total} memories.")
        except Exception as e:
            return CommandResult.err(f"Failed to clear memories: {e}")

    async def _stats_memory(self) -> CommandResult:
        """Show memory statistics."""
        try:
            from h_agent.memory.long_term import LongTermMemory, MemoryType, LONG_TERM_FILE

            memory = LongTermMemory()

            lines = ["📊 Memory Statistics:\n"]

            total = 0
            for mem_type in [MemoryType.USER, MemoryType.PROJECT, MemoryType.DECISION, MemoryType.FACT, MemoryType.ERROR]:
                entries = memory._data.get(mem_type, [])
                count = len(entries)
                total += count
                type_label = {
                    MemoryType.USER: "👤 User",
                    MemoryType.PROJECT: "📁 Project",
                    MemoryType.DECISION: "⚖️ Decisions",
                    MemoryType.FACT: "📝 Facts",
                    MemoryType.ERROR: "🐛 Errors",
                }.get(mem_type, mem_type)
                lines.append(f"  {type_label}: {count}")

            lines.append(f"\n  Total: {total} entries")

            if LONG_TERM_FILE.exists():
                size = LONG_TERM_FILE.stat().st_size
                lines.append(f"  File size: {size} bytes")

            return CommandResult.ok("\n".join(lines))
        except Exception as e:
            return CommandResult.err(f"Failed to get stats: {e}")

    def get_help(self) -> str:
        return """Usage: /memory <subcommand>

Manage persistent memory for storing user preferences, project info, and decisions.

Subcommands:
  list              List all stored memories
  add <text>        Add a new memory
  search <query>    Search memories by keyword
  stats             Show memory statistics
  clear             Clear all memories (careful!)

Examples:
  /memory add User prefers Python over JavaScript
  /memory search preferences
  /memory list
"""
