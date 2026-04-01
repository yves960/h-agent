"""
h_agent/__main__.py - Entry Point

Main entry point for running h_agent as a module: python -m h_agent

Supports:
  - Interactive REPL mode
  - Single prompt execution
  - CLI argument parsing
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_environment():
    """Set up environment variables and load dotenv."""
    from dotenv import load_dotenv
    load_dotenv(override=True)


def get_default_model() -> str:
    """Get default model from config/env."""
    return os.getenv("MODEL_ID", "gpt-4o")


def get_system_prompt() -> str:
    """Get default system prompt."""
    cwd = os.getcwd()
    return (
        f"You are a helpful AI coding assistant.\n"
        f"Current working directory: {cwd}\n"
        f"Be concise and practical. Write working code over perfect code."
    )


async def run_repl(
    prompt: str = None,
    model: str = None,
    system_prompt: str = None,
    verbose: bool = False,
):
    """Run the interactive REPL."""
    from h_agent.cli.repl import REPL
    from h_agent.core.engine import QueryEngine
    from h_agent.tools import get_registry

    model = model or get_default_model()
    system_prompt = system_prompt or get_system_prompt()

    # Initialize tool registry
    registry = get_registry()
    tool_schemas = registry.get_tool_schemas()

    if verbose:
        print(f"Model: {model}")
        print(f"Tools: {', '.join(registry.list_tools())}")

    # Create engine
    engine = QueryEngine(
        model=model,
        tools=tool_schemas,
        system_prompt=system_prompt,
        tool_registry=registry,
    )

    # Create and run REPL
    repl = REPL(
        engine=engine,
        system_prompt=system_prompt,
    )

    repl.run(initial_prompt=prompt)


async def run_single(
    prompt: str,
    model: str = None,
    system_prompt: str = None,
    verbose: bool = False,
):
    """Run a single prompt and exit."""
    from h_agent.core.engine import QueryEngine
    from h_agent.tools import get_registry

    model = model or get_default_model()
    system_prompt = system_prompt or get_system_prompt()

    # Initialize tool registry
    registry = get_registry()
    tool_schemas = registry.get_tool_schemas()

    if verbose:
        print(f"Model: {model}", file=sys.stderr)

    # Create engine
    engine = QueryEngine(
        model=model,
        tools=tool_schemas,
        system_prompt=system_prompt,
        tool_registry=registry,
    )

    messages = []

    if verbose:
        print(f"System: {system_prompt[:100]}...", file=sys.stderr)

    # Run query
    result = await engine.run_tool_loop(
        messages=messages,
        system_prompt=system_prompt,
    )

    print(result)

    if verbose:
        usage = engine.get_usage()
        print(f"\n[Usage: {usage.total_tokens} tokens, ${usage.cost_usd:.4f}]", file=sys.stderr)


def main():
    """Main entry point with argument parsing."""
    setup_environment()

    parser = argparse.ArgumentParser(
        description="h-agent: AI coding agent with session management",
        prog="h-agent",
    )

    # Global options
    parser.add_argument(
        "--model", "-m",
        default=get_default_model(),
        help="Model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--system-prompt", "-s",
        help="System prompt",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    # Positional: prompt or command
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Prompt to execute (runs in single-shot mode)",
    )

    args = parser.parse_args()

    # Version check
    if args.version:
        try:
            from h_agent import __version__
            print(f"h-agent {__version__}")
        except ImportError:
            print("h-agent (version unknown)")
        return 0

    # Combine prompt arguments
    prompt_text = " ".join(args.prompt) if args.prompt else None

    # Choose mode
    if prompt_text:
        # Single-shot mode
        asyncio.run(run_single(
            prompt=prompt_text,
            model=args.model,
            system_prompt=args.system_prompt,
            verbose=args.verbose,
        ))
    else:
        # Interactive REPL mode
        asyncio.run(run_repl(
            model=args.model,
            system_prompt=args.system_prompt,
            verbose=args.verbose,
        ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
