"""
h_agent/keybindings/__init__.py - Keybindings Module

Provides keybinding configuration and management for the REPL.
Supports registering custom key bindings and mapping keys to actions.
"""

from h_agent.keybindings.config import (
    KeyBinding,
    KeyBindings,
    DEFAULT_BINDINGS,
    register_binding,
    get_binding,
    list_bindings,
    get_bindings,
)

__all__ = [
    "KeyBinding",
    "KeyBindings",
    "DEFAULT_BINDINGS",
    "register_binding",
    "get_binding",
    "list_bindings",
    "get_bindings",
]
