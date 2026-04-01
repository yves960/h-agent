"""
tests/test_keybindings.py - Tests for Keybindings Module

Tests for the keybinding configuration and registry system.
"""

import pytest
from h_agent.keybindings import (
    KeyBinding,
    KeyBindings,
    DEFAULT_BINDINGS,
    register_binding,
    get_binding,
    list_bindings,
)


class TestKeyBinding:
    """Test KeyBinding dataclass."""

    def test_key_binding_creation(self):
        """Test creating a key binding."""
        binding = KeyBinding(key="Ctrl+C", action="interrupt", description="Interrupt")
        assert binding.key == "Ctrl+C"
        assert binding.action == "interrupt"
        assert binding.description == "Interrupt"

    def test_key_binding_normalization(self):
        """Test key normalization (ctrl+ -> Ctrl+)."""
        binding = KeyBinding(key="ctrl+c", action="test")
        assert "Ctrl+" in binding.key
        assert binding.key.lower().replace("ctrl+", "").replace("control+", "") == "c"


class TestKeyBindings:
    """Test KeyBindings registry."""

    def test_default_bindings_loaded(self):
        """Test that default bindings are loaded."""
        kb = KeyBindings()
        assert len(kb.list_all()) > 0
        assert "Ctrl+C" in [b.key for b in kb.list_all()]

    def test_register_binding(self):
        """Test registering a new binding."""
        kb = KeyBindings()
        kb.register("F1", "help", "Show help")
        binding = kb.get("F1")
        assert binding is not None
        assert binding.action == "help"
        assert binding.description == "Show help"

    def test_unregister_binding(self):
        """Test unregistering a binding."""
        kb = KeyBindings()
        kb.register("F2", "test", "Test action")
        assert kb.get("F2") is not None

        result = kb.unregister("F2")
        assert result is True
        assert kb.get("F2") is None

    def test_unregister_nonexistent(self):
        """Test unregistering a non-existent binding."""
        kb = KeyBindings()
        result = kb.unregister("DOES_NOT_EXIST")
        assert result is False

    def test_get_by_action(self):
        """Test getting bindings by action."""
        kb = KeyBindings()
        bindings = kb.get_by_action("exit")
        assert len(bindings) > 0
        assert all(b.action == "exit" for b in bindings)

    def test_list_by_category(self):
        """Test listing bindings by category."""
        kb = KeyBindings()
        kb.register("Ctrl+X", "cut", "Cut text", category="editing")
        editing_bindings = kb.list_by_category("editing")
        assert len(editing_bindings) > 0
        assert any(b.key == "Ctrl+X" for b in editing_bindings)

    def test_list_categories(self):
        """Test listing all categories."""
        kb = KeyBindings()
        kb.register("Ctrl+X", "cut", "Cut text", category="editing")
        categories = kb.list_categories()
        assert "editing" in categories

    def test_set_handler(self):
        """Test setting a handler for an action."""
        kb = KeyBindings()
        called = []

        def handler(ctx):
            called.append(ctx)

        # Register a new binding with a unique action
        kb.register("Ctrl+Alt+T", "custom_action", "Custom action")

        # Set handler for the custom action
        kb.set_handler("custom_action", handler)

        # Execute the binding - should call the handler
        kb.execute("Ctrl+Alt+T", "test_context")

        assert len(called) == 1
        assert called[0] == "test_context"

    def test_execute_with_binding_handler(self):
        """Test executing a binding with its own handler."""
        kb = KeyBindings()
        called = []

        def handler(ctx):
            called.append(ctx)

        kb.register("Ctrl+G", "test", handler=handler)
        kb.execute("Ctrl+G", "test_context")

        assert len(called) == 1

    def test_execute_nonexistent(self):
        """Test executing a non-existent binding."""
        kb = KeyBindings()
        result = kb.execute("DOES_NOT_EXIST")
        assert result is None

    def test_clear_handlers(self):
        """Test clearing all handlers."""
        kb = KeyBindings()

        def handler(ctx):
            pass

        kb.set_handler("test", handler)
        kb.clear_handlers()
        # Should not raise
        kb.execute("Ctrl+X", "context")

    def test_reset_to_defaults(self):
        """Test resetting to default bindings."""
        kb = KeyBindings()
        original_count = len(kb.list_all())

        kb.register("F99", "test", "Test")
        kb.reset_to_defaults()

        # Should be back to original count
        assert len(kb.list_all()) == original_count
        assert kb.get("F99") is None

    def test_default_bindings_content(self):
        """Test default bindings have expected actions."""
        expected_actions = ["interrupt", "exit", "clear", "retry"]
        for action in expected_actions:
            bindings = KeyBindings().get_by_action(action)
            assert len(bindings) > 0, f"Missing default binding for {action}"


class TestGlobalRegistry:
    """Test global registry functions."""

    def test_register_binding_global(self):
        """Test registering via global function."""
        from h_agent.keybindings import get_bindings, get_binding

        # Clear existing
        bindings = get_bindings()
        original = bindings.get("Ctrl+Shift+T")
        if original:
            bindings.unregister("Ctrl+Shift+T")

        register_binding("Ctrl+Shift+T", "test", "Test binding")
        binding = get_binding("Ctrl+Shift+T")
        assert binding is not None
        assert binding.action == "test"

    def test_get_binding_global(self):
        """Test getting binding via global function."""
        binding = get_binding("Ctrl+C")
        assert binding is not None
        assert binding.action == "interrupt"

    def test_list_bindings_global(self):
        """Test listing bindings via global function."""
        bindings = list_bindings()
        assert len(bindings) > 0
        assert any(b.key == "Ctrl+C" for b in bindings)
