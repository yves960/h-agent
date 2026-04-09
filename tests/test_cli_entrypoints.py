"""Smoke tests for the public CLI entrypoints."""

import os
import subprocess
import sys


def _cli_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("OPENAI_API_KEY", "test-key")
    env.setdefault("OPENAI_BASE_URL", "https://example.invalid/v1")
    env.setdefault("MODEL_ID", "test-model")
    return env


def test_module_entrypoint_matches_full_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "h_agent", "--help"],
        capture_output=True,
        text=True,
        env=_cli_env(),
        timeout=10,
    )

    assert result.returncode == 0
    assert "session" in result.stdout
    assert "chat" in result.stdout
    assert "run" in result.stdout
    assert "RuntimeWarning" not in result.stderr


def test_commands_module_help_has_no_runpy_warning():
    result = subprocess.run(
        [sys.executable, "-m", "h_agent.cli.commands", "--help"],
        capture_output=True,
        text=True,
        env=_cli_env(),
        timeout=10,
    )

    assert result.returncode == 0
    assert "session" in result.stdout
    assert "RuntimeWarning" not in result.stderr


def test_module_entrypoint_version():
    result = subprocess.run(
        [sys.executable, "-m", "h_agent", "--version"],
        capture_output=True,
        text=True,
        env=_cli_env(),
        timeout=10,
    )

    assert result.returncode == 0
    assert result.stdout.strip().startswith("h-agent ")


def test_module_entrypoint_doctor():
    result = subprocess.run(
        [sys.executable, "-m", "h_agent", "doctor"],
        capture_output=True,
        text=True,
        env=_cli_env(),
        timeout=10,
    )

    assert result.returncode == 0
    assert "Doctor" in result.stdout or "Diagnostics" in result.stdout
