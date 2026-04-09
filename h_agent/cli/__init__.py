"""CLI module - Command line interface for h_agent."""

__all__ = ["main"]


def main():
    """Lazy wrapper to avoid importing the full CLI during package import."""
    from h_agent.cli.commands import main as commands_main

    return commands_main()
