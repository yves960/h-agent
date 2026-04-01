"""
h_agent/plugins/registry.py - Plugin Registry

Central registry for managing plugins.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .schema import Plugin
from .loader import PluginLoader


# Global registry instance
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> "PluginRegistry":
    """Get the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


class PluginRegistry:
    """
    Central plugin registry.

    Manages discovery, loading, and lifecycle of plugins.

    Example:
        registry = get_plugin_registry()
        registry.discover()

        for plugin in registry.list_plugins():
            print(f"{plugin.manifest.name}: {plugin.manifest.description}")
    """

    def __init__(self, plugins_dir=None):
        self.plugins: Dict[str, Plugin] = {}
        self.loader = PluginLoader(plugins_dir)

    def discover(self) -> int:
        """
        Discover and register all plugins.

        Returns:
            Number of plugins discovered
        """
        for plugin in self.loader.discover():
            self.plugins[plugin.manifest.name] = plugin
        return len(self.plugins)

    def get(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self) -> List[Plugin]:
        """List all registered plugins."""
        return sorted(self.plugins.values(), key=lambda p: p.manifest.name)

    def list_enabled(self) -> List[Plugin]:
        """List all enabled plugins."""
        return [p for p in self.list_plugins() if p.enabled]

    def enable(self, name: str) -> bool:
        """
        Enable a plugin by name.

        Returns:
            True if plugin was found and enabled
        """
        plugin = self.get(name)
        if plugin:
            if self.loader.activate(plugin):
                return True
        return False

    def disable(self, name: str) -> bool:
        """
        Disable a plugin by name.

        Returns:
            True if plugin was found and disabled
        """
        plugin = self.get(name)
        if plugin:
            self.loader.deactivate(plugin)
            plugin.enabled = False
            return True
        return False

    def reload(self, name: str) -> bool:
        """
        Reload a plugin (disable then enable).

        Returns:
            True if reload succeeded
        """
        plugin = self.get(name)
        if not plugin:
            return False
        self.loader.deactivate(plugin)
        return self.loader.activate(plugin)
