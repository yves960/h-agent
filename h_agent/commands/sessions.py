"""h_agent/commands/sessions.py - Sessions Command

Lists all saved sessions.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.session import SessionStorage


class SessionsCommand(Command):
    """List all saved sessions."""
    
    name = "sessions"
    description = "列出所有保存的会话"
    aliases = ["ls"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute the sessions command.
        
        Args:
            args: Optional filter (not used currently)
            context: Command execution context
            
        Returns:
            CommandResult with list of sessions
        """
        storage = SessionStorage()
        sessions = storage.list_sessions()
        
        if not sessions:
            return CommandResult(
                success=True,
                output="No saved sessions found"
            )
        
        # Format output
        lines = ["Saved Sessions:"]
        for i, sess in enumerate(sessions[:20], 1):  # Limit to 20
            created = sess["created"][:19] if len(sess["created"]) > 19 else sess["created"]
            lines.append(
                f"  {i}. {sess['id']} ({sess['model']}) - "
                f"{created} - {sess['messages']} msgs, {sess['tokens']} tokens"
            )
        
        if len(sessions) > 20:
            lines.append(f"  ... and {len(sessions) - 20} more")
        
        return CommandResult(
            success=True,
            output="\n".join(lines)
        )
