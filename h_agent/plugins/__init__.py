"""
h_agent/plugins - Plugin System

Dynamic plugin loading for h-agent extensibility.
Plugins are Python modules in the plugins directory or installed packages.
"""

import os
import sys
import importlib
import importlib.util
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

PLUGIN_DIR = Path(__file__).parent
PLUGINS_CONFIG_FILE = PLUGIN_DIR.parent.parent / ".h-agent" / "plugins.json"
PLUGIN_INDEX_URL = "https://raw.githubusercontent.com/ekko-ai/h-agent-plugins/main/index.json"


@dataclass
class Plugin:
    """Represents a loaded plugin."""
    name: str
    version: str
    description: str
    author: str
    tools: List[Dict] = field(default_factory=list)
    handlers: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    path: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
            "tool_count": len(self.tools),
        }


_loaded_plugins: Dict[str, Plugin] = {}
_plugin_state: Dict[str, bool] = {}


def _get_plugin_state() -> Dict[str, bool]:
    """Load plugin enabled/disabled state from config."""
    if PLUGINS_CONFIG_FILE.exists():
        try:
            with open(PLUGINS_CONFIG_FILE) as f:
                data = json.load(f)
            return data.get("plugins", {})
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_plugin_state(state: Dict[str, bool]) -> None:
    """Save plugin state to config."""
    PLUGINS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLUGINS_CONFIG_FILE, "w") as f:
        json.dump({"plugins": state}, f, indent=2)


def _discover_plugins() -> List[Path]:
    """Discover plugin modules in the plugins directory."""
    plugins = []
    if not PLUGIN_DIR.exists():
        return plugins
    for item in PLUGIN_DIR.iterdir():
        if item.is_file() and item.suffix == ".py" and item.stem not in ("__init__", "__main__"):
            plugins.append(item)
        elif item.is_dir() and (item / "__init__.py").exists():
            plugins.append(item)
    return plugins


def load_plugin(path: Path) -> Optional[Plugin]:
    """Load a plugin from a path (file or directory)."""
    try:
        if path.is_file():
            name = path.stem
            spec = importlib.util.spec_from_file_location(name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
        elif path.is_dir():
            name = path.name
            spec = importlib.util.spec_from_file_location(name, path / "__init__.py")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
        else:
            return None

        module = sys.modules.get(name)
        if not module:
            return None

        # Check for required plugin attributes
        plugin_name = getattr(module, "PLUGIN_NAME", name)
        plugin_version = getattr(module, "PLUGIN_VERSION", "0.0.0")
        plugin_desc = getattr(module, "PLUGIN_DESCRIPTION", "")
        plugin_author = getattr(module, "PLUGIN_AUTHOR", "unknown")

        tools = getattr(module, "PLUGIN_TOOLS", [])
        handlers = getattr(module, "PLUGIN_HANDLERS", {})

        plugin = Plugin(
            name=plugin_name,
            version=plugin_version,
            description=plugin_desc,
            author=plugin_author,
            tools=tools,
            handlers=handlers,
            path=path,
        )

        # Restore enabled state
        state = _get_plugin_state()
        plugin.enabled = state.get(plugin.name, True)

        _loaded_plugins[plugin.name] = plugin
        return plugin

    except Exception as e:
        print(f"[plugin] Failed to load {path}: {e}", file=sys.stderr)
        return None


def load_all_plugins() -> Dict[str, Plugin]:
    """Discover and load all available plugins."""
    state = _get_plugin_state()
    for name, enabled in state.items():
        if name not in _loaded_plugins and enabled:
            # Try to load as installed package
            try:
                mod = importlib.import_module(f"h_agent_plugins_{name}")
                # ... (would need proper plugin package structure)
            except ImportError:
                pass

    # Load local plugins
    for path in _discover_plugins():
        name = path.stem if path.is_file() else path.name
        if name == "__init__":
            continue
        if name not in _loaded_plugins:
            load_plugin(path)

    return _loaded_plugins


def get_plugin(name: str) -> Optional[Plugin]:
    """Get a loaded plugin by name."""
    return _loaded_plugins.get(name)


def list_plugins() -> List[Plugin]:
    """List all loaded plugins."""
    return list(_loaded_plugins.values())


def enable_plugin(name: str) -> bool:
    """Enable a plugin."""
    if name in _loaded_plugins:
        _loaded_plugins[name].enabled = True
        state = _get_plugin_state()
        state[name] = True
        _save_plugin_state(state)
        return True
    return False


def disable_plugin(name: str) -> bool:
    """Disable a plugin."""
    if name in _loaded_plugins:
        _loaded_plugins[name].enabled = False
        state = _get_plugin_state()
        state[name] = True
        _save_plugin_state(state)
        return True
    return False


def get_enabled_tools() -> List[Dict]:
    """Get all tools from enabled plugins."""
    tools = []
    for plugin in _loaded_plugins.values():
        if plugin.enabled:
            tools.extend(plugin.tools)
    return tools


def get_enabled_handlers() -> Dict[str, Any]:
    """Get all handlers from enabled plugins."""
    handlers = {}
    for plugin in _loaded_plugins.values():
        if plugin.enabled:
            handlers.update(plugin.handlers)
    return handlers
