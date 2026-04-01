"""
h_agent/migrations/core.py - Migration Core

Core migration system for h-agent configuration migrations.
"""

from pathlib import Path
from typing import List, Callable, Dict, Any, Optional
import json
import shutil

# Type alias for migration function
MigrationFunc = Callable[[Dict[str, Any]], Dict[str, Any]]


class Migration:
    """
    Base class for migrations.

    Subclass this and implement the `migrate` method.

    Attributes:
        version: Target version string (e.g., "1.1.0")
        description: Human-readable description
    """

    version: str = ""
    description: str = ""

    def migrate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply migration to config.

        Args:
            config: Current configuration dict

        Returns:
            Updated configuration dict
        """
        raise NotImplementedError("Migration.migrate() must be implemented")


class MigrationRunner:
    """
    Runs migrations for configuration files.

    Supports:
    - Registering multiple migrations
    - Version comparison
    - Sequential migration execution
    - Backup before migration
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize migration runner.

        Args:
            config_path: Path to config file. If None, uses default.
        """
        if config_path:
            self.config_path = config_path
        else:
            from h_agent.core.config import AGENT_CONFIG_FILE
            self.config_path = AGENT_CONFIG_FILE

        self.migrations: List[Migration] = []
        self._backup_dir = self.config_path.parent / "backups"

    def register(self, migration: Migration) -> None:
        """
        Register a migration.

        Args:
            migration: Migration instance to register
        """
        if not migration.version:
            raise ValueError("Migration must have a version")

        self.migrations.append(migration)
        # Sort by version
        self.migrations.sort(key=lambda m: [int(x) for x in m.version.split(".")])

    def run(self, dry_run: bool = False) -> List[str]:
        """
        Run all needed migrations.

        Args:
            dry_run: If True, don't actually modify files

        Returns:
            List of migration versions that were applied
        """
        if not self.config_path.exists():
            # Create initial config
            self._create_initial_config(dry_run)
            return []

        # Load current config
        with open(self.config_path) as f:
            config = json.load(f)

        current_version = config.get("version", "0.0.0")
        applied = []

        for migration in self.migrations:
            if self._compare_versions(migration.version, current_version) > 0:
                print(f"Applying migration {migration.version}: {migration.description}")

                if not dry_run:
                    # Create backup
                    self._backup_config()

                    # Apply migration
                    config = migration.migrate(config)
                    config["version"] = migration.version

                    # Save
                    with open(self.config_path, "w") as f:
                        json.dump(config, f, indent=2)

                applied.append(migration.version)
                current_version = migration.version

        return applied

    def _create_initial_config(self, dry_run: bool = False) -> None:
        """Create initial config file with version."""
        config = {
            "version": "1.0.0",
            "model_id": "gpt-4o",
            "api_base_url": "https://api.openai.com/v1",
        }

        if not dry_run:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)

    def _backup_config(self) -> None:
        """Create a backup of the current config."""
        if not self.config_path.exists():
            return

        self._backup_dir.mkdir(parents=True, exist_ok=True)

        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / f"config_{timestamp}.json"

        shutil.copy2(self.config_path, backup_path)
        print(f"Backup created: {backup_path}")

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Args:
            v1: First version
            v2: Second version

        Returns:
            1 if v1 > v2, -1 if v1 < v2, 0 if equal
        """
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        # Pad with zeros
        while len(parts1) < len(parts2):
            parts1.append(0)
        while len(parts2) < len(parts1):
            parts2.append(0)

        for p1, p2 in zip(parts1, parts2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1

        return 0

    def get_current_version(self) -> str:
        """Get current config version."""
        if not self.config_path.exists():
            return "0.0.0"

        try:
            with open(self.config_path) as f:
                config = json.load(f)
            return config.get("version", "0.0.0")
        except Exception:
            return "0.0.0"

    def get_migrations_status(self) -> Dict[str, str]:
        """Get status of all migrations."""
        current = self.get_current_version()
        status = {}

        for migration in self.migrations:
            if self._compare_versions(migration.version, current) <= 0:
                status[migration.version] = "applied"
            else:
                status[migration.version] = "pending"

        return status


# ============================================================
# Built-in Migrations
# ============================================================

class Migration_1_1_0(Migration):
    """
    Migration to version 1.1.0.

    Adds buddy configuration for agent collaboration.
    """

    version = "1.1.0"
    description = "Add buddy configuration"

    def migrate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add buddy config if not present."""
        if "buddy" not in config:
            config["buddy"] = {
                "enabled": True,
                "muted": False,
                "model": config.get("model_id", "gpt-4o"),
            }
        return config


class Migration_1_2_0(Migration):
    """
    Migration to version 1.2.0.

    Adds keybindings configuration.
    """

    version = "1.2.0"
    description = "Add keybindings configuration"

    def migrate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add keybindings config."""
        if "keybindings" not in config:
            config["keybindings"] = {
                "enabled": True,
                "vi_mode": False,
            }
        return config


class Migration_1_3_0(Migration):
    """
    Migration to version 1.3.0.

    Adds advanced context settings.
    """

    version = "1.3.0"
    description = "Add advanced context settings"

    def migrate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add context config."""
        if "context" not in config:
            config["context"] = {
                "safe_limit": 180000,
                "max_tool_output": 50000,
            }
        return config


# ============================================================
# Convenience Functions
# ============================================================

def run_migrations(config_path: Optional[Path] = None) -> List[str]:
    """
    Run all migrations with default setup.

    Args:
        config_path: Optional path to config file

    Returns:
        List of applied migration versions
    """
    runner = MigrationRunner(config_path)

    # Register built-in migrations
    runner.register(Migration_1_1_0())
    runner.register(Migration_1_2_0())
    runner.register(Migration_1_3_0())

    return runner.run()
