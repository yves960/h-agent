"""
h_agent/plugins/schema.py - Plugin Schema

Plugin manifest and data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class PluginManifest:
    """
    Plugin manifest - metadata describing a plugin.

    Loaded from plugin.json in each plugin directory.
    """
    name: str
    version: str
    description: str
    author: str
    main: str = "index.py"
    tools: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plugin:
    """
    Plugin instance.

    Flat interface matching legacy test expectations.
    Also provides .manifest for the new architecture.

    Attributes:
        name: Plugin name
        version: Version string
        description: Description
        author: Author name
        manifest: Full plugin manifest (new architecture)
        path: Path to plugin directory
        enabled: Whether plugin is active
        instance: Loaded Python module (after activation)
    """
    # Flat fields (legacy interface / test compatibility)
    name: str = ""
    version: str = ""
    description: str = ""
    author: str = ""
    # New architecture fields
    manifest: Optional[PluginManifest] = None
    path: str = ""
    enabled: bool = True
    instance: Optional[Any] = None

    def __post_init__(self):
        # If manifest is provided but flat fields are empty, extract from manifest
        if self.manifest and not self.name:
            self.name = self.manifest.name
            self.version = self.manifest.version
            self.description = self.manifest.description
            self.author = self.manifest.author

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
            "path": self.path,
        }

    def __repr__(self):
        return f"Plugin({self.name} {self.version})"
