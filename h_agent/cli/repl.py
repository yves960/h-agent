"""
h_agent/cli/repl.py - REPL Loop

Interactive Read-Eval-Print loop for h-agent.
Inspired by Claude Code's REPL implementation.
"""

from __future__ import annotations

import asyncio
import os
import sys
import signal
from typing import Optional, Callable, List

# Optional: questionary for fancy prompts
try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False

from h_agent.tools import get_registry


# ============================================================
# ANSI Colors
# ============================================================

class Colors:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


# ============================================================
# Slash Commands
# ============================================================

class SlashCommand:
    """A slash command in the REPL."""
    
    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable,
        aliases: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.aliases = aliases or []


# Built-in slash commands
SLASH_COMMANDS: List[SlashCommand] = []


def register_slash_command(cmd: SlashCommand):
    """Register a slash command."""
    SLASH_COMMANDS.append(cmd)


def get_slash_commands() -> List[SlashCommand]:
    """Get all registered slash commands."""
    return SLASH_COMMANDS


def _register_builtin_commands():
    """Register built-in slash commands."""
    global SLASH_COMMANDS
    
    # /clear - Clear conversation
    def cmd_clear(engine, context):
        context["messages"] = []
        return "Conversation cleared."
    
    SLASH_COMMANDS.append(SlashCommand(
        name="clear",
        description="Clear conversation history",
        handler=cmd_clear,
        aliases=["cls"],
    ))
    
    # /help - Show help
    def cmd_help(engine, context):
        lines = ["Available commands:"]
        lines.append("  /exit, /quit     Exit the REPL")
        lines.append("  /clear           Clear conversation")
        lines.append("  /tools           List available tools")
        lines.append("  /model           Show current model")
        lines.append("  /cost            Show token usage cost")
        lines.append("  /history         Show conversation history")
        if SLASH_COMMANDS:
            lines.append("")
            lines.append("Slash commands:")
            for cmd in SLASH_COMMANDS:
                alias_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                lines.append(f"  /{cmd.name}{alias_str}  {cmd.description}")
        return "\n".join(lines)
    
    SLASH_COMMANDS.append(SlashCommand(
        name="help",
        description="Show this help message",
        handler=cmd_help,
        aliases=["?"],
    ))
    
    # /tools - List tools
    def cmd_tools(engine, context):
        registry = get_registry()
        tools = registry.list_tools()
        if not tools:
            return "No tools available."
        lines = ["Available tools:"]
        for tool_name in sorted(tools):
            tool = registry.get(tool_name)
            if tool:
                desc = tool.description[:60] if tool.description else ""
                lines.append(f"  {tool_name:<20} {desc}")
        return "\n".join(lines)
    
    SLASH_COMMANDS.append(SlashCommand(
        name="tools",
        description="List available tools",
        handler=cmd_tools,
    ))
    
    # /model - Show model
    def cmd_model(engine, context):
        return f"Current model: {engine.model if engine else 'unknown'}"
    
    SLASH_COMMANDS.append(SlashCommand(
        name="model",
        description="Show current model",
        handler=cmd_model,
    ))
    
    # /cost - Show cost
    def cmd_cost(engine, context):
        if engine:
            usage = engine.get_usage()
            return (
                f"Token usage:\n"
                f"  Prompt: {usage.prompt_tokens:,} tokens\n"
                f"  Completion: {usage.completion_tokens:,} tokens\n"
                f"  Total: {usage.total_tokens:,} tokens\n"
                f"  Estimated cost: ${usage.cost_usd:.4f}"
            )
        return "No usage data available."
    
    SLASH_COMMANDS.append(SlashCommand(
        name="cost",
        description="Show token usage cost",
        handler=cmd_cost,
    ))
    
    # /history - Show history
    def cmd_history(engine, context):
        messages = context.get("messages", [])
        if not messages:
            return "No conversation history."
        lines = [f"Conversation ({len(messages)} messages):"]
        for i, msg in enumerate(messages[-10:], max(1, len(messages) - 9)):
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "[complex content]"
            if len(content) > 80:
                content = content[:77] + "..."
            lines.append(f"  [{i}] {role}: {content}")
        return "\n".join(lines)
    
    SLASH_COMMANDS.append(SlashCommand(
        name="history",
        description="Show conversation history",
        handler=cmd_history,
        aliases=["hist"],
    ))
    
    # /exit - Exit
    def cmd_exit(engine, context):
        context["running"] = False
        return "Goodbye!"
    
    SLASH_COMMANDS.append(SlashCommand(
        name="exit",
        description="Exit the REPL",
        handler=cmd_exit,
        aliases=["quit", "q"],
    ))


# ============================================================
# Input Helpers
# ============================================================

def get_input(prompt: str = ">> ") -> str:
    """Get input from user."""
    try:
        return input(f"{Colors.CYAN}{prompt}{Colors.RESET}")
    except (EOFError, KeyboardInterrupt):
        return ""


def get_multiline_input() -> str:
    """
    Get multi-line input.
    End with empty line or Ctrl+D.
    """
    lines = []
    print(f"{Colors.DIM}(Enter blank line or Ctrl+D to finish){Colors.RESET}")
    
    while True:
        try:
            line = input(f"{Colors.CYAN}.. {Colors.RESET}")
            if not line.strip():
                break
            lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    return "\n".join(lines)


def print_output(text: str, color: str = Colors.WHITE):
    """Print output with color."""
    print(f"{color}{text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}Error: {text}{Colors.RESET}", file=sys.stderr)


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}Warning: {text}{Colors.RESET}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


# ============================================================
# REPL
# ============================================================

class REPL:
    """
    Interactive REPL for h-agent.
    
    Features:
    - Multi-line input support
    - Slash command execution
    - Tool execution with progress
    - Conversation history management
    - Ctrl+C/Ctrl+D handling
    """

    def __init__(
        self,
        engine=None,
        system_prompt: Optional[str] = None,
        welcome_message: Optional[str] = None,
    ):
        """
        Initialize REPL.
        
        Args:
            engine: QueryEngine instance
            system_prompt: System prompt to use
            welcome_message: Custom welcome message
        """
        self.engine = engine
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.welcome_message = welcome_message or self._default_welcome()
        
        self.messages: List[dict] = []
        self.context = {
            "running": True,
            "messages": self.messages,
        }
        
        self._setup_signal_handlers()
        _register_builtin_commands()

    def _default_system_prompt(self) -> str:
        """Get default system prompt."""
        return (
            f"You are a helpful AI assistant. "
            f"Current directory: {os.getcwd()}"
        )

    def _default_welcome(self) -> str:
        """Get default welcome message."""
        return (
            f"{Colors.CYAN}h_agent{Colors.RESET} - AI Coding Agent\n"
            f"{Colors.DIM}Type '/help' for available commands{Colors.RESET}\n"
        )

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful exit."""
        def handle_sigint(signum, frame):
            print(f"\n{Colors.YELLOW}Interrupted. Use /exit to quit.{Colors.RESET}")
        
        def handle_sigtstp(signum, frame):
            print(f"\n{Colors.YELLOW}Suspended.{Colors.RESET}")
        
        try:
            signal.signal(signal.SIGINT, handle_sigint)
            signal.signal(signal.SIGTSTP, handle_sigtstp)
        except (ValueError, OSError):
            pass  # Not in main thread

    def _parse_input(self, raw_input: str) -> tuple[str, Optional[str]]:
        """
        Parse user input.
        
        Returns:
            (command_type, content)
            command_type: "slash", "message", or "empty"
            content: The actual content
        """
        raw = raw_input.strip()
        
        if not raw:
            return "empty", ""
        
        if raw.startswith("/"):
            # Slash command
            parts = raw[1:].split(maxsplit=1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            return "slash", f"{cmd} {args}".strip()
        
        return "message", raw

    def _execute_slash_command(self, cmd_str: str) -> Optional[str]:
        """
        Execute a slash command.
        
        Returns:
            Output string or None to continue
        """
        parts = cmd_str.split(maxsplit=1)
        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Find command
        cmd = None
        for c in SLASH_COMMANDS:
            if c.name == cmd_name or cmd_name in c.aliases:
                cmd = c
                break
        
        if not cmd:
            # Try partial match
            matches = [c for c in SLASH_COMMANDS if c.name.startswith(cmd_name)]
            if len(matches) == 1:
                cmd = matches[0]
            elif len(matches) > 1:
                return f"Ambiguous command: {cmd_name}. Matches: {', '.join(m.name for m in matches)}"
            else:
                return f"Unknown command: /{cmd_name}. Type /help for available commands."
        
        # Execute
        try:
            return cmd.handler(self.engine, self.context)
        except Exception as e:
            return f"Error executing command: {e}"

    async def _run_query(self, prompt: str):
        """Run a query through the engine."""
        if not self.engine:
            print_error("No engine configured")
            return
        
        # Add user message
        self.messages.append({"role": "user", "content": prompt})
        
        # Show thinking indicator
        print(f"{Colors.DIM}", end="", flush=True)
        
        try:
            # Run the tool loop
            final_content = await self.engine.run_tool_loop(
                messages=self.messages,
                system_prompt=self.system_prompt,
            )
            
            # Print response
            print(f"{Colors.RESET}", end="")
            if final_content:
                print(f"\n{final_content}\n")
            else:
                print()
        
        except Exception as e:
            print(f"{Colors.RESET}")
            print_error(f"Query failed: {e}")

    def run(self, initial_prompt: Optional[str] = None):
        """
        Run the REPL.
        
        Args:
            initial_prompt: Optional prompt to run immediately (for non-interactive mode)
        """
        print(self.welcome_message)
        
        # Run initial prompt if provided
        if initial_prompt:
            cmd_type, content = self._parse_input(initial_prompt)
            if cmd_type == "slash":
                output = self._execute_slash_command(content)
                if output:
                    print(output)
            else:
                asyncio.run(self._run_query(content))
            return
        
        # Main loop
        while self.context.get("running", True):
            try:
                raw = get_input()
                if not raw:
                    continue
                
                cmd_type, content = self._parse_input(raw)
                
                if cmd_type == "empty":
                    continue
                elif cmd_type == "slash":
                    output = self._execute_slash_command(content)
                    if output:
                        print(output)
                else:
                    # Check for multi-line (starts with ```)
                    if content.startswith("```"):
                        # Multi-line input mode
                        print(f"{Colors.DIM}(Multi-line mode: end with ``` on its own line){Colors.RESET}")
                        multiline_content = content[3:]
                        while True:
                            try:
                                line = input(f"{Colors.CYAN}... {Colors.RESET}")
                                if line.strip() == "```":
                                    break
                                multiline_content += "\n" + line
                            except EOFError:
                                break
                        content = multiline_content
                    
                    asyncio.run(self._run_query(content))
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Use /exit to quit.{Colors.RESET}")
                continue
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print_error(f"Error: {e}")
        
        # Print final cost
        if self.engine:
            usage = self.engine.get_usage()
            if usage.total_tokens > 0:
                print(f"\n{Colors.DIM}Session: {usage.total_tokens:,} tokens, ${usage.cost_usd:.4f}{Colors.RESET}")


# ============================================================
# Convenience Functions
# ============================================================

async def run_repl_async(
    prompt: Optional[str] = None,
    model: str = "gpt-4o",
    system_prompt: Optional[str] = None,
    tools: Optional[List[dict]] = None,
):
    """Run REPL asynchronously."""
    from h_agent.core.engine import QueryEngine
    from h_agent.tools import get_registry
    
    registry = get_registry()
    tool_schemas = registry.get_tool_schemas()
    
    engine = QueryEngine(
        model=model,
        tools=tool_schemas,
        system_prompt=system_prompt,
        tool_registry=registry,
    )
    
    repl = REPL(
        engine=engine,
        system_prompt=system_prompt,
    )
    
    repl.run(initial_prompt=prompt)


def run_repl(
    prompt: Optional[str] = None,
    model: str = "gpt-4o",
    system_prompt: Optional[str] = None,
):
    """Run REPL synchronously."""
    asyncio.run(run_repl_async(prompt, model, system_prompt))
