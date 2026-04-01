"""
h_agent/commands/config.py - /config Command

Show or modify configuration.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class ConfigCommand(Command):
    name = "config"
    description = "Show or modify configuration"

    # Known config keys and their descriptions
    CONFIG_KEYS = {
        "model": "Model ID",
        "max_tokens": "Max tokens in response",
        "temperature": "Temperature for generation",
        "timeout": "Request timeout (seconds)",
        "max_turns": "Max tool call iterations",
    }

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        if not context.engine:
            return CommandResult.err("No engine configured.")

        parts = args.strip().split(maxsplit=1)
        key = parts[0] if parts else ""
        value = parts[1] if len(parts) > 1 else None

        if not args:
            # Show all config
            return self._show_all_config(context.engine)

        if not key:
            return CommandResult.err("Usage: /config [key] [value]")

        # Check if it's a valid key
        if key not in self.CONFIG_KEYS:
            valid_keys = ", ".join(self.CONFIG_KEYS.keys())
            return CommandResult.err(
                f"Unknown config key: {key}. Valid keys: {valid_keys}"
            )

        if value is None:
            # Show specific key
            return self._show_key(context.engine, key)

        # Set value
        return self._set_key(context.engine, key, value)

    def _show_all_config(self, engine) -> CommandResult:
        lines = ["Configuration:"]
        lines.append(f"  model:       {engine.model}")
        lines.append(f"  max_tokens:  {engine.max_tokens}")
        lines.append(f"  temperature: {engine.temperature}")
        lines.append(f"  timeout:     {engine.timeout}")
        lines.append(f"  max_turns:   {engine.max_turns}")
        lines.append("")
        lines.append("Use /config <key> to see details, /config <key> <value> to set.")
        return CommandResult.ok("\n".join(lines))

    def _show_key(self, engine, key: str) -> CommandResult:
        value = getattr(engine, key, None)
        desc = self.CONFIG_KEYS.get(key, key)
        return CommandResult.ok(f"{desc}: {value}")

    def _set_key(self, engine, key: str, value: str) -> CommandResult:
        old_value = getattr(engine, key, None)

        # Type conversion
        if key in ("max_tokens", "timeout", "max_turns"):
            try:
                value = int(value)
            except ValueError:
                return CommandResult.err(f"Invalid integer: {value}")
        elif key == "temperature":
            try:
                value = float(value)
                if not 0 <= value <= 2:
                    return CommandResult.err("Temperature must be between 0 and 2")
            except ValueError:
                return CommandResult.err(f"Invalid float: {value}")

        setattr(engine, key, value)
        return CommandResult.ok(f"{key}: {old_value} -> {value}")

    def get_help(self) -> str:
        keys = ", ".join(f"'{k}'" for k in self.CONFIG_KEYS.keys())
        return (
            f"/{self.name} - {self.description}\n"
            f"  Usage: /{self.name} [{keys}]\n"
            f"  Show or modify configuration"
        )
