"""
tests/test_screens.py - Tests for Screens Module

Tests for the full-screen UI components.
"""

import pytest
from h_agent.screens import run_doctor_check
from h_agent.screens.doctor import DoctorScreen, CheckResult


class TestCheckResult:
    """Test CheckResult dataclass."""

    def test_check_result_creation(self):
        """Test creating a check result."""
        result = CheckResult(
            name="Test",
            status="pass",
            message="Test passed",
            details="Additional info"
        )
        assert result.name == "Test"
        assert result.status == "pass"
        assert result.message == "Test passed"
        assert result.details == "Additional info"


class TestDoctorScreen:
    """Test DoctorScreen class."""

    def test_doctor_screen_creation(self):
        """Test creating a doctor screen."""
        screen = DoctorScreen()
        assert screen.results == []

    def test_run_checks_returns_results(self):
        """Test that run_checks returns results."""
        screen = DoctorScreen()
        results = screen.run_checks()
        assert len(results) > 0

    def test_check_python(self):
        """Test Python check."""
        screen = DoctorScreen()
        screen._check_python()

        assert len(screen.results) == 1
        result = screen.results[0]
        assert result.name == "Python"
        assert result.status in ("pass", "warn")
        assert "Python" in result.message

    def test_check_dependencies(self):
        """Test dependencies check."""
        screen = DoctorScreen()
        screen._check_dependencies()

        # Should check for openai, tiktoken, yaml, rich
        dep_names = [r.name for r in screen.results]
        assert "openai" in dep_names
        assert "tiktoken" in dep_names
        assert "yaml" in dep_names
        assert "rich" in dep_names

    def test_check_api(self):
        """Test API check."""
        screen = DoctorScreen()
        screen._check_api()

        # Should have API Client and Model checks
        assert len(screen.results) >= 2

    def test_check_config(self):
        """Test config check."""
        screen = DoctorScreen()
        screen._check_config()

        # Should have some config checks
        assert len(screen.results) >= 1
        names = [r.name for r in screen.results]
        # May be "Config", "Config Dir", "Config File" depending on implementation
        assert any("Config" in name for name in names)

    def test_check_tools(self):
        """Test tools check."""
        screen = DoctorScreen()
        screen._check_tools()

        assert len(screen.results) == 1
        result = screen.results[0]
        assert result.name == "Tools"
        # Status can be pass, fail, or warn
        assert result.status in ("pass", "fail", "warn")
        # Message should contain some info about tools
        assert len(result.message) > 0

    def test_check_commands(self):
        """Test commands check."""
        screen = DoctorScreen()
        screen._check_commands()

        assert len(screen.results) == 1
        result = screen.results[0]
        assert result.name == "Commands"
        assert result.status in ("pass", "fail")
        assert "commands" in result.message.lower()

    def test_check_memory(self):
        """Test memory check."""
        screen = DoctorScreen()
        screen._check_memory()

        assert len(screen.results) == 1
        result = screen.results[0]
        assert result.name == "Memory"
        assert result.status in ("pass", "fail", "warn")

    def test_check_platform(self):
        """Test platform check."""
        screen = DoctorScreen()
        screen._check_platform()

        assert len(screen.results) == 1
        result = screen.results[0]
        assert result.name == "Platform"
        assert result.status in ("pass", "warn")

    def test_render_returns_string(self):
        """Test that render returns a string."""
        screen = DoctorScreen()
        screen.run_checks()

        output = screen.render()
        assert isinstance(output, str)
        assert "h-agent Doctor" in output
        assert "Summary:" in output

    def test_render_includes_all_results(self):
        """Test that render includes all check results."""
        screen = DoctorScreen()
        screen.run_checks()

        output = screen.render()

        for result in screen.results:
            assert result.name in output or result.message in output

    def test_render_shows_recommendations_on_failure(self):
        """Test that render shows recommendations when checks fail."""
        screen = DoctorScreen()
        screen._add_result("Test", "fail", "Test failed")

        output = screen.render()
        assert "Recommendations" in output

    def test_add_result(self):
        """Test adding a result manually."""
        screen = DoctorScreen()
        screen._add_result("Custom", "pass", "Custom check passed")

        assert len(screen.results) == 1
        assert screen.results[0].name == "Custom"

    def test_summary_counts(self):
        """Test summary counts are correct."""
        screen = DoctorScreen()
        screen._add_result("Test1", "pass", "Pass")
        screen._add_result("Test2", "pass", "Pass")
        screen._add_result("Test3", "warn", "Warn")
        screen._add_result("Test4", "fail", "Fail")

        output = screen.render()
        assert "2 ✅" in output
        assert "1 ⚠️" in output
        assert "1 ❌" in output


class TestRunDoctorCheck:
    """Test the convenience function."""

    def test_run_doctor_check_returns_list(self):
        """Test that run_doctor_check returns a list."""
        results = run_doctor_check()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_run_doctor_check_returns_check_results(self):
        """Test that results are CheckResult objects."""
        results = run_doctor_check()
        for result in results:
            assert isinstance(result, CheckResult)
            assert result.name
            assert result.status in ("pass", "fail", "warn", "skip")
            assert result.message
