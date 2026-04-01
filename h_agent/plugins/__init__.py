"""
h_agent/plugins/__init__.py - Plugin System

Extensible plugin architecture for h-agent.
"""

from .schema import Plugin, PluginManifest
from .loader import PluginLoader
from .registry import PluginRegistry, get_plugin_registry

# For backwards compatibility, also expose convenience functions
from .registry import get_plugin_registry as _registry


def load_plugin(name: str):
    """Discover and load a single plugin by name."""
    r = _registry()
    if not r.plugins:
        r.discover()
    plugin = r.get(name)
    if plugin and not plugin.enabled:
        r.enable(name)
    return plugin


def _discover_plugins():
    """Discover all plugins (lazy init)."""
    return list(_registry().discover() or [])


def load_all_plugins():
    """Load all discovered plugins."""
    return {p.manifest.name: p for p in _registry().discover() or _registry().list_plugins()}


def get_plugin(name: str):
    """Get a plugin by name."""
    r = _registry()
    if not r.plugins:
        r.discover()
    return r.get(name)


def list_plugins():
    """List all plugins."""
    r = _registry()
    if not r.plugins:
        r.discover()
    return r.list_plugins()


def enable_plugin(name: str) -> bool:
    """Enable a plugin by name."""
    return _registry().enable(name)


def disable_plugin(name: str) -> bool:
    """Disable a plugin by name."""
    return _registry().disable(name)


def get_enabled_tools():
    """Get list of tools from all enabled plugins."""
    r = _registry()
    if not r.plugins:
        r.discover()
    tools = []
    for p in r.list_enabled():
        tools.extend(p.manifest.tools or [])
    return tools


def get_enabled_handlers():
    """Get dict of handlers from all enabled plugins."""
    r = _registry()
    if not r.plugins:
        r.discover()
    handlers = {}
    for p in r.list_enabled():
        if p.instance and hasattr(p.instance, "handlers"):
            handlers.update(getattr(p.instance, "handlers", {}))
    return handlers


__all__ = [
    "Plugin",
    "PluginManifest",
    "PluginLoader",
    "PluginRegistry",
    "get_plugin_registry",
    # Legacy convenience functions
    "load_plugin",
    "load_all_plugins",
    "get_plugin",
    "list_plugins",
    "enable_plugin",
    "disable_plugin",
    "get_enabled_tools",
    "get_enabled_handlers",
    "_discover_plugins",
]
