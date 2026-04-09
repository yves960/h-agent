"""Module entry point that delegates to the full CLI implementation."""

from h_agent.cli.commands import main


if __name__ == "__main__":
    raise SystemExit(main())
