"""
h_agent/keybindings/config.py - Keybinding Configuration

Defines key binding structures and a global registry for key bindings.
Inspired by vim keybinding patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any

# ============================================================
# Default Key Bindings
# ============================================================

DEFAULT_BINDINGS = {
    "Ctrl+C": "interrupt",
    "Ctrl+D": "exit",
    "Ctrl+L": "clear",
    "Ctrl+R": "retry",
    "Ctrl+Z": "suspend",
    "Tab": "autocomplete",
    "Shift+Tab": "autocomplete_reverse",
    "Up": "history_prev",
    "Down": "history_next",
    "Ctrl+U": "clear_line",
    "Ctrl+K": "clear_after_cursor",
    "Ctrl+A": "move_line_start",
    "Ctrl+E": "move_line_end",
    "Ctrl+W": "delete_word",
    "Alt+B": "move_word_back",
    "Alt+F": "move_word_forward",
    "Ctrl+C+Ctrl+C": "force_interrupt",
}


# ============================================================
# Key Binding Data Class
# ============================================================

@dataclass
class KeyBinding:
    """
    Represents a single key binding.

    Attributes:
        key: The key combination (e.g., "Ctrl+C", "Up", "F1")
        action: The action name to trigger
        description: Human-readable description of the action
        handler: Optional callable handler for the action
        category: Category for grouping (e.g., "navigation", "editing", "execution")
    """
    key: str
    action: str
    description: str = ""
    handler: Optional[Callable] = None
    category: str = "general"

    def __post_init__(self):
        """Normalize key format."""
        self.key = self.key.replace("ctrl+", "Ctrl+").replace("Control+", "Ctrl+")
        # Capitalize letter after Ctrl+/Control+
        if self.key.lower().startswith("ctrl+"):
            self.key = "Ctrl+" + self.key[5:].capitalize()
        elif self.key.lower().startswith("control+"):
            self.key = "Ctrl+" + self.key[8:].capitalize()


# ============================================================
# Key Bindings Registry
# ============================================================

class KeyBindings:
    """
    Global key bindings registry.

    Supports:
    - Registering/unregistering key bindings
    - Looking up bindings by key
    - Listing all bindings
    - Grouping by category
    - Custom handlers for actions
    """

    def __init__(self):
        self._bindings: Dict[str, KeyBinding] = {}
        self._handlers: Dict[str, Callable] = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load default key bindings."""
        for key, action in DEFAULT_BINDINGS.items():
            desc = self._get_default_description(action)
            self.register(key, action, desc)

    def _get_default_description(self, action: str) -> str:
        """Get default description for an action."""
        descriptions = {
            "interrupt": "Interrupt current operation",
            "exit": "Exit the REPL",
            "clear": "Clear the screen",
            "retry": "Retry last command",
            "suspend": "Suspend to background",
            "autocomplete": "Autocomplete current input",
            "autocomplete_reverse": "Autocomplete (reverse direction)",
            "history_prev": "Previous command in history",
            "history_next": "Next command in history",
            "clear_line": "Clear current line",
            "clear_after_cursor": "Clear from cursor to end",
            "move_line_start": "Move to start of line",
            "move_line_end": "Move to end of line",
            "delete_word": "Delete previous word",
            "move_word_back": "Move word backward",
            "move_word_forward": "Move word forward",
            "force_interrupt": "Force interrupt (double Ctrl+C)",
        }
        return descriptions.get(action, f"Execute {action}")

    def register(
        self,
        key: str,
        action: str,
        description: str = "",
        handler: Optional[Callable] = None,
        category: str = "general",
    ) -> None:
        """
        Register a key binding.

        Args:
            key: Key combination (e.g., "Ctrl+C", "F1")
            action: Action name to trigger
            description: Human-readable description
            handler: Optional handler function
            category: Category for grouping
        """
        binding = KeyBinding(
            key=key,
            action=action,
            description=description or self._get_default_description(action),
            handler=handler,
            category=category,
        )
        self._bindings[key] = binding

        if handler:
            self._handlers[action] = handler

    def unregister(self, key: str) -> bool:
        """
        Unregister a key binding.

        Args:
            key: Key combination to remove

        Returns:
            True if unregistered, False if not found
        """
        if key in self._bindings:
            del self._bindings[key]
            return True
        return False

    def get(self, key: str) -> Optional[KeyBinding]:
        """
        Get a binding by key.

        Args:
            key: Key combination

        Returns:
            KeyBinding or None if not found
        """
        return self._bindings.get(key)

    def get_by_action(self, action: str) -> List[KeyBinding]:
        """
        Get all bindings for an action.

        Args:
            action: Action name

        Returns:
            List of matching KeyBindings
        """
        return [b for b in self._bindings.values() if b.action == action]

    def list_all(self) -> List[KeyBinding]:
        """List all registered bindings."""
        return list(self._bindings.values())

    def list_by_category(self, category: str) -> List[KeyBinding]:
        """List bindings in a specific category."""
        return [b for b in self._bindings.values() if b.category == category]

    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(set(b.category for b in self._bindings.values()))

    def execute(self, key: str, *args, **kwargs) -> Any:
        """
        Execute the handler for a key binding.

        Args:
            key: Key combination pressed
            *args, **kwargs: Additional context passed to handler

        Returns:
            Result from handler, or None if no handler/not found
        """
        binding = self.get(key)
        if not binding:
            return None

        context = args[0] if args else kwargs.get('context')

        # Try handler on binding first
        if binding.handler:
            return binding.handler(context)

        # Then try global handler for action
        if binding.action in self._handlers:
            return self._handlers[binding.action](context)

        return None

    def set_handler(self, action: str, handler: Callable) -> None:
        """
        Set a global handler for an action.

        Args:
            action: Action name
            handler: Handler function
        """
        self._handlers[action] = handler

    def clear_handlers(self) -> None:
        """Clear all global handlers."""
        self._handlers.clear()

    def reset_to_defaults(self) -> None:
        """Reset all bindings to defaults."""
        self._bindings.clear()
        self._handlers.clear()
        self._load_defaults()


# ============================================================
# Global Registry Instance
# ============================================================

_global_bindings: Optional[KeyBindings] = None


def get_bindings() -> KeyBindings:
    """Get the global KeyBindings instance."""
    global _global_bindings
    if _global_bindings is None:
        _global_bindings = KeyBindings()
    return _global_bindings


def register_binding(
    key: str,
    action: str,
    description: str = "",
    handler: Optional[Callable] = None,
    category: str = "general",
) -> None:
    """Register a binding with the global registry."""
    get_bindings().register(key, action, description, handler, category)


def get_binding(key: str) -> Optional[KeyBinding]:
    """Get a binding from the global registry."""
    return get_bindings().get(key)


def list_bindings() -> List[KeyBinding]:
    """List all bindings from the global registry."""
    return get_bindings().list_all()
