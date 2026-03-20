#!/usr/bin/env python3
"""
h_agent/cli/commands.py - Command Line Interface

Main entry point for h_agent CLI.
"""

import os
import sys
from pathlib import Path

# Add parent to path for imports when running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

load_dotenv(override=True)

# Import from core
from h_agent.core.tools import agent_loop, TOOLS, TOOL_HANDLERS, execute_tool_call
from h_agent.core.config import MODEL, OPENAI_BASE_URL


def get_system_prompt() -> str:
    """Get the system prompt for the agent."""
    return f"""You are a coding agent at {os.getcwd()}.

Use the available tools to solve tasks efficiently.

Available tools:
- bash: Run shell commands
- read: Read file contents
- write: Write content to files
- edit: Make precise edits to files
- glob: Find files by pattern

Act efficiently. Don't over-explain."""


def interactive_mode():
    """Run interactive REPL mode."""
    print(f"\033[36mh_agent - OpenAI Agent Harness\033[0m")
    print(f"Model: {MODEL}")
    print(f"API: {OPENAI_BASE_URL}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Tools: {', '.join(TOOL_HANDLERS.keys())}")
    print()
    print("Type 'q', 'exit', or press Enter to quit")
    print("=" * 50)
    print()
    
    history = []
    
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if query.strip().lower() in ("q", "exit", ""):
            print("Goodbye!")
            break
        
        # Add user message
        history.append({"role": "user", "content": query})
        
        # Run agent loop
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            )
            
            while True:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": get_system_prompt()}] + history,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=8000,
                )
                
                message = response.choices[0].message
                history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                })
                
                if not message.tool_calls:
                    break
                
                # Execute tool calls
                import json
                for tool_call in message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    key_arg = args.get('command') or args.get('path') or args.get('pattern', '')
                    print(f"\033[33m$ {tool_call.function.name}({key_arg[:40]})\033[0m")
                    
                    result = execute_tool_call(tool_call)
                    print(result[:200] + ("..." if len(result) > 200 else ""))
                    
                    history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            
            # Print final response
            if history[-1].get("content"):
                print(f"\n{history[-1]['content']}\n")
                
        except Exception as e:
            print(f"\033[31mError: {e}\033[0m")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Single command mode
        query = " ".join(sys.argv[1:])
        print(f"Running: {query}")
        # TODO: Implement single command mode
        print("Single command mode not yet implemented. Use interactive mode.")
        sys.exit(1)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()