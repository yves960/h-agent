"""
tests/test_migrations.py - Tests for Migrations Module

Tests for the configuration migration system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from h_agent.migrations import (
    Migration,
    MigrationRunner,
    Migration_1_1_0,
    run_migrations,
)


class TestMigration:
    """Test Migration base class."""

    def test_migration_requires_version(self):
        """Test that migration requires version."""
        migration = Migration()
        migration.version = "1.0.0"
        migration.description = "Test"
        migration.migrate = lambda x: x

        assert migration.version == "1.0.0"
        assert migration.description == "Test"


class TestMigrationRunner:
    """Test MigrationRunner."""

    def test_version_comparison(self):
        """Test version comparison logic."""
        runner = MigrationRunner(Path(tempfile.mktemp()))

        assert runner._compare_versions("1.1.0", "1.0.0") == 1
        assert runner._compare_versions("1.0.0", "1.1.0") == -1
        assert runner._compare_versions("1.0.0", "1.0.0") == 0
        assert runner._compare_versions("2.0.0", "1.9.9") == 1
        assert runner._compare_versions("1.0.10", "1.0.9") == 1

    def test_version_comparison_padding(self):
        """Test version comparison with different length."""
        runner = MigrationRunner(Path(tempfile.mktemp()))

        assert runner._compare_versions("1.0", "1.0.0") == 0
        assert runner._compare_versions("1", "1.0.0") == 0
        assert runner._compare_versions("1.0.0.1", "1.0.0") == 1

    def test_register_migration(self):
        """Test registering migrations."""
        runner = MigrationRunner(Path(tempfile.mktemp()))

        class TestMigration1(Migration):
            version = "1.0.0"
            description = "Test 1"

            def migrate(self, config):
                return config

        class TestMigration2(Migration):
            version = "2.0.0"
            description = "Test 2"

            def migrate(self, config):
                return config

        runner.register(TestMigration2())
        runner.register(TestMigration1())

        # Should be sorted
        assert runner.migrations[0].version == "1.0.0"
        assert runner.migrations[1].version == "2.0.0"

    def test_register_migration_requires_version(self):
        """Test that registering without version raises."""
        runner = MigrationRunner(Path(tempfile.mktemp()))

        migration = Migration()
        migration.description = "Test"
        migration.migrate = lambda x: x

        with pytest.raises(ValueError, match="version"):
            runner.register(migration)

    def test_run_migrations_creates_initial_config(self):
        """Test that run creates initial config if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            runner = MigrationRunner(config_path)

            # Should not raise
            applied = runner.run()
            assert applied == []
            assert config_path.exists()

            with open(config_path) as f:
                config = json.load(f)
            assert config["version"] == "1.0.0"

    def test_run_migrations_dry_run(self):
        """Test dry run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text('{"version": "0.0.0"}')

            runner = MigrationRunner(config_path)
            runner.register(Migration_1_1_0())

            applied = runner.run(dry_run=True)

            # Config should not change
            with open(config_path) as f:
                config = json.load(f)
            assert config.get("version") == "0.0.0"
            assert len(applied) == 1

    def test_run_migrations_actual(self):
        """Test actual migration run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text('{"version": "0.0.0"}')

            runner = MigrationRunner(config_path)
            runner.register(Migration_1_1_0())

            applied = runner.run()

            assert "1.1.0" in applied
            with open(config_path) as f:
                config = json.load(f)
            assert config["version"] == "1.1.0"
            assert "buddy" in config

    def test_run_migrations_skips_applied(self):
        """Test that already applied migrations are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text('{"version": "1.1.0"}')

            runner = MigrationRunner(config_path)
            runner.register(Migration_1_1_0())

            applied = runner.run()

            assert len(applied) == 0
            with open(config_path) as f:
                config = json.load(f)
            assert config["version"] == "1.1.0"

    def test_get_current_version(self):
        """Test getting current version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"

            runner = MigrationRunner(config_path)
            assert runner.get_current_version() == "0.0.0"

            config_path.write_text('{"version": "1.2.3"}')
            assert runner.get_current_version() == "1.2.3"

    def test_get_migrations_status(self):
        """Test getting migration status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text('{"version": "1.0.0"}')

            runner = MigrationRunner(config_path)

            class Migration2(Migration):
                version = "2.0.0"
                description = "Test"

                def migrate(self, config):
                    return config

            m1 = Migration_1_1_0()
            m2 = Migration2()

            runner.register(m1)
            runner.register(m2)

            # Verify versions
            assert m1.version == "1.1.0"
            assert m2.version == "2.0.0"

            # Verify migrations are registered
            assert len(runner.migrations) == 2

            status = runner.get_migrations_status()

            # Check keys exist
            assert "1.1.0" in status, f"Expected 1.1.0 in status, got {status}"
            assert "2.0.0" in status, f"Expected 2.0.0 in status, got {status}"

            # Current version is 1.0.0, so:
            # - Migration 1.1.0 is NEWER than 1.0.0 -> not yet applied -> "pending"
            # - Migration 2.0.0 is NEWER than 1.0.0 -> not yet applied -> "pending"
            assert status["1.1.0"] == "pending"
            assert status["2.0.0"] == "pending"

            # Now test with config at version 1.2.0
            config_path.write_text('{"version": "1.2.0"}')
            status2 = runner.get_migrations_status()

            # Migration 1.1.0 is older than 1.2.0 -> already applied -> "applied"
            assert status2["1.1.0"] == "applied"
            # Migration 2.0.0 is newer than 1.2.0 -> not applied -> "pending"
            assert status2["2.0.0"] == "pending"


class TestMigration_1_1_0:
    """Test Migration_1_1_0."""

    def test_adds_buddy_config(self):
        """Test that buddy config is added."""
        migration = Migration_1_1_0()
        config = {}

        result = migration.migrate(config)

        assert "buddy" in result
        assert result["buddy"]["enabled"] is True
        assert result["buddy"]["muted"] is False

    def test_does_not_overwrite_existing(self):
        """Test that existing buddy config is preserved."""
        migration = Migration_1_1_0()
        config = {"buddy": {"enabled": False, "custom": True}}

        result = migration.migrate(config)

        assert result["buddy"]["enabled"] is False
        assert result["buddy"]["custom"] is True


class TestRunMigrationsFunction:
    """Test the convenience function."""

    def test_run_migrations_registers_builtins(self):
        """Test that built-in migrations are registered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text('{"version": "0.0.0"}')

            applied = run_migrations(config_path)

            assert "1.1.0" in applied
            assert "1.2.0" in applied
            assert "1.3.0" in applied
