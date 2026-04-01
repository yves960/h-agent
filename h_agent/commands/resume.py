"""h_agent/commands/resume.py - Resume Command

Resumes a previous session from saved transcript.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.session import SessionStorage, SessionResumer


class ResumeCommand(Command):
    """Resume a previous session."""
    
    name = "resume"
    description = "恢复上一次会话"
    aliases = ["r"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute the resume command.
        
        Args:
            args: Session ID to resume, or empty for latest session
            context: Command execution context
            
        Returns:
            CommandResult with success/failure and output message
        """
        resumer = SessionResumer()
        
        # Find session to resume
        session_id = args.strip() if args else None
        transcript = resumer.find_session(session_id)
        
        if not transcript:
            if session_id:
                return CommandResult(
                    success=False,
                    output=f"Session not found: {session_id}"
                )
            else:
                return CommandResult(
                    success=False,
                    output="No previous session found to resume"
                )
        
        # Restore context
        ctx = resumer.restore_context(transcript)
        
        # Update context
        context.messages.clear()
        context.messages.extend(ctx["messages"])
        
        # Update engine token counter if available
        if context.engine:
            context.engine.total_usage.total_tokens = ctx["total_tokens"]
        
        return CommandResult(
            success=True,
            output=f"Resumed session {transcript.session_id} ({len(transcript.messages)} messages, {transcript.total_tokens} tokens)"
        )
