"""
h_agent/migrations/__init__.py - Migrations Module

Database/schema migration system for h-agent configuration.
Provides version tracking and automatic migration for config changes.

Usage:
    from h_agent.migrations import MigrationRunner, Migration

    runner = MigrationRunner()
    runner.register(MyMigration())
    runner.run()
"""

from h_agent.migrations.core import (
    Migration,
    MigrationRunner,
    Migration_1_1_0,
    run_migrations,
)

__all__ = [
    "Migration",
    "MigrationRunner",
    "Migration_1_1_0",
    "run_migrations",
]
