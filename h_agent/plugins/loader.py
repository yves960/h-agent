"""
h_agent/plugins/loader.py - Plugin Loader

Discovers and loads plugins from the filesystem.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import List, Optional

from .schema import Plugin, PluginManifest


class PluginLoader:
    """
    Plugin discovery and loading.

    Scans plugin directories for valid plugins and loads them.

    Attributes:
        plugins_dir: Base directory for plugins (default: ~/.h-agent/plugins)
    """

    def __init__(self, plugins_dir: Path | None = None):
        self.plugins_dir = plugins_dir or Path.home() / ".h-agent" / "plugins"

    def discover(self) -> List[Plugin]:
        """
        Discover all plugins in the plugins directory.

        Returns:
            List of discovered plugins (not yet activated)
        """
        plugins = []

        if not self.plugins_dir.exists():
            return plugins

        for entry in self.plugins_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                plugin = self.load(entry)
                if plugin:
                    plugins.append(plugin)

        return plugins

    def load(self, plugin_dir: Path) -> Optional[Plugin]:
        """
        Load a single plugin from a directory.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Plugin instance or None if not a valid plugin
        """
        manifest_path = plugin_dir / "plugin.json"
        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path) as f:
                data = json.load(f)
        except Exception:
            return None

        # Validate required fields
        required = ["name", "version", "description", "author"]
        for field in required:
            if field not in data:
                return None

        manifest = PluginManifest(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            main=data.get("main", "index.py"),
            tools=data.get("tools", []),
            commands=data.get("commands", []),
            permissions=data.get("permissions", []),
            config=data.get("config", {}),
        )

        return Plugin(
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            manifest=manifest,
            path=str(plugin_dir),
        )

    def activate(self, plugin: Plugin) -> bool:
        """
        Activate a plugin by importing its main module.

        Args:
            plugin: Plugin to activate

        Returns:
            True if activation succeeded
        """
        main_path = Path(plugin.path) / plugin.manifest.main
        if not main_path.exists():
            return False

        try:
            module_name = f"h_agent_plugin_{plugin.manifest.name}"

            # Remove existing if reloading
            if module_name in sys.modules:
                del sys.modules[module_name]

            spec = importlib.util.spec_from_file_location(module_name, main_path)
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            plugin.instance = module
            plugin.enabled = True
            return True

        except Exception:
            return False

    def deactivate(self, plugin: Plugin):
        """
        Deactivate a plugin (remove its module).

        Args:
            plugin: Plugin to deactivate
        """
        module_name = f"h_agent_plugin_{plugin.manifest.name}"
        if module_name in sys.modules:
            del sys.modules[module_name]
        plugin.instance = None
        plugin.enabled = False
