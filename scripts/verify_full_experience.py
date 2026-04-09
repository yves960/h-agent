#!/usr/bin/env python3
"""Offline-safe full experience verification for h-agent."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(ROOT / ".venv" / "bin" / "python")


TOP_LEVEL_COMMANDS = [
    "start",
    "status",
    "stop",
    "autostart",
    "team",
    "agent",
    "logs",
    "session",
    "rag",
    "run",
    "chat",
    "config",
    "memory",
    "plugin",
    "skill",
    "template",
    "model",
    "init",
    "doctor",
    "web",
    "cron",
    "heartbeat",
]

NESTED_HELP_COMMANDS = [
    ["autostart", "status"],
    ["team", "list"],
    ["team", "status"],
    ["agent", "list"],
    ["session", "list"],
    ["session", "create"],
    ["session", "history"],
    ["session", "delete"],
    ["session", "search"],
    ["session", "rename"],
    ["session", "tag"],
    ["session", "group"],
    ["session", "cleanup"],
    ["rag", "index"],
    ["rag", "search"],
    ["rag", "stats"],
    ["memory", "list"],
    ["memory", "add"],
    ["memory", "get"],
    ["memory", "delete"],
    ["memory", "search"],
    ["memory", "dump"],
    ["plugin", "list"],
    ["plugin", "info"],
    ["plugin", "enable"],
    ["plugin", "disable"],
    ["plugin", "install"],
    ["plugin", "uninstall"],
    ["skill", "list"],
    ["skill", "info"],
    ["skill", "enable"],
    ["skill", "disable"],
    ["skill", "install"],
    ["skill", "uninstall"],
    ["skill", "run"],
    ["template", "list"],
    ["template", "show"],
    ["template", "apply"],
    ["template", "create"],
    ["template", "delete"],
    ["model", "list"],
    ["model", "switch"],
    ["model", "info"],
    ["model", "add"],
    ["cron", "list"],
    ["cron", "add"],
    ["cron", "remove"],
    ["cron", "enable"],
    ["cron", "disable"],
    ["cron", "exec"],
    ["cron", "log"],
    ["heartbeat", "start"],
    ["heartbeat", "stop"],
    ["heartbeat", "status"],
    ["heartbeat", "run"],
]


@dataclass
class StepResult:
    name: str
    passed: bool
    details: str


class Verifier:
    def __init__(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="h-agent-full-"))
        self.home = self.tmpdir / "home"
        self.state = self.tmpdir / "state"
        self.workspace = self.tmpdir / "workspace"
        self.home.mkdir(parents=True, exist_ok=True)
        self.state.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.results: list[StepResult] = []

    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["H_AGENT_HOME"] = str(self.state)
        env["OPENAI_API_KEY"] = "test-key"
        env["OPENAI_BASE_URL"] = "https://example.invalid/v1"
        env["MODEL_ID"] = "test-model"
        return env

    def run(
        self,
        name: str,
        args: list[str],
        *,
        cwd: Path | None = None,
        expect: int | tuple[int, ...] = 0,
        must_contain: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        cmd = [PYTHON, "-m", "h_agent", *args]
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or ROOT),
            env=self.env(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        expected = {expect} if isinstance(expect, int) else set(expect)
        combined = (proc.stdout or "") + (proc.stderr or "")
        passed = proc.returncode in expected
        if must_contain:
            passed = passed and all(token in combined for token in must_contain)
        details = combined.strip()[:1200]
        self.results.append(StepResult(name=name, passed=passed, details=details))
        if not passed:
            raise AssertionError(f"{name} failed\nCommand: {' '.join(cmd)}\n{details}")
        return proc

    def run_help_matrix(self) -> None:
        self.run("root help", ["--help"], must_contain=["session", "doctor", "heartbeat"])
        for command in TOP_LEVEL_COMMANDS:
            self.run(f"help:{command}", [command, "--help"], must_contain=["usage:"])
        for command in NESTED_HELP_COMMANDS:
            self.run(f"help:{' '.join(command)}", [*command, "--help"], must_contain=["usage:"])

    def run_bootstrap(self) -> None:
        self.run("doctor", ["doctor"], must_contain=["Doctor", "Diagnostics"])
        self.run("config show", ["config", "--show"], must_contain=["MODEL_ID"])
        self.run("status", ["status"], must_contain=["Daemon"])
        self.run("autostart status", ["autostart", "status"])
        self.run("logs tail", ["logs", "--tail", "5"], expect=(0, 1))

    def run_session_flow(self) -> None:
        created = self.run("session create", ["session", "create", "--name", "smoke"], must_contain=["Created:"])
        match = re.search(r"(sess-[a-f0-9]+)", created.stdout)
        assert match, created.stdout
        session_id = match.group(1)

        self.run("session list", ["session", "list"], must_contain=[session_id, "smoke"])
        self.run("session rename", ["session", "rename", session_id, "smoke-renamed"], must_contain=["Renamed"])
        self.run("session tag add", ["session", "tag", "add", session_id, "demo"], must_contain=["Added"])
        self.run("session tag get", ["session", "tag", "get", session_id], must_contain=["demo"])
        self.run("session group set", ["session", "group", "set", session_id, "acceptance"], must_contain=["group"])
        self.run("session group list", ["session", "group", "list"], must_contain=["acceptance"])
        self.run("session group sessions", ["session", "group", "sessions", "acceptance"], must_contain=[session_id])
        self.run("session search", ["session", "search", "smoke"], must_contain=[session_id])
        self.run("session history", ["session", "history", session_id], expect=0)
        self.run("session delete", ["session", "delete", session_id], must_contain=["Deleted"])
        self.run("session cleanup", ["session", "cleanup"], expect=0)

    def run_memory_flow(self) -> None:
        self.run("memory add", ["memory", "add", "fact", "smoke-key", "smoke-value", "--tags", "demo"], must_contain=["Stored"])
        self.run("memory get", ["memory", "get", "smoke-key"], must_contain=["smoke-value"])
        self.run("memory search", ["memory", "search", "smoke-key"], must_contain=["smoke-key"])
        self.run("memory list", ["memory", "list"], must_contain=["smoke-key"])
        self.run("memory dump", ["memory", "dump"], must_contain=["smoke-key"])
        self.run("memory delete", ["memory", "delete", "fact", "smoke-key"], must_contain=["Deleted"])

    def run_catalog_flow(self) -> None:
        self.run("plugin list", ["plugin", "list"], expect=0)
        self.run("skill list", ["skill", "list", "--all"], must_contain=["Skills"])
        self.run("skill info office", ["skill", "info", "office"], expect=0)
        self.run("template list", ["template", "list"], expect=0)
        self.run("model list", ["model", "list"], expect=0)
        self.run("rag stats", ["rag", "stats", "--directory", str(self.workspace)], must_contain=["Codebase Index Statistics"])

    def run_template_flow(self) -> None:
        name = "smoke-template"
        self.run("template create", ["template", "create", name], must_contain=["Created template"])
        self.run("template show", ["template", "show", name], must_contain=[f"Template: {name}"])
        self.run("template delete", ["template", "delete", name], must_contain=["Deleted template"])

    def run_agent_team_flow(self) -> None:
        self.run("agent list", ["agent", "list"], expect=0)
        self.run(
            "agent init",
            ["agent", "init", "smoke-agent", "--role", "coder", "--description", "smoke agent"],
            must_contain=["Created agent profile"],
        )
        self.run("agent show", ["agent", "show", "smoke-agent"], must_contain=["Agent: smoke-agent"])
        self.run("agent sessions", ["agent", "sessions", "smoke-agent"], expect=0)
        self.run("team list", ["team", "list"], expect=0)
        self.run("team status", ["team", "status"], must_contain=["Team:"])

    def run_rag_flow(self) -> None:
        project = self.workspace / "mini-project"
        project.mkdir(parents=True, exist_ok=True)
        (project / "sample.py").write_text(
            "def smoke_function():\n    return 'ok'\n",
            encoding="utf-8",
        )
        self.run("rag index", ["rag", "index", "--directory", str(project)], must_contain=["Indexing complete"])
        self.run("rag search", ["rag", "search", "smoke_function", "--directory", str(project)], must_contain=["smoke_function"])
        self.run("rag stats indexed", ["rag", "stats", "--directory", str(project)], must_contain=["Total files"])

    def run_scheduler_flow(self) -> None:
        self.run("cron list", ["cron", "list"], expect=0)
        added = self.run(
            "cron add",
            ["cron", "add", "*/5 * * * *", "echo smoke", "--name", "smoke-job"],
            must_contain=["Added cron job"],
        )
        match = re.search(r"ID: ([a-zA-Z0-9_-]+)", added.stdout)
        assert match, added.stdout
        job_id = match.group(1)
        self.run("cron disable", ["cron", "disable", job_id], must_contain=["Disabled"])
        self.run("cron enable", ["cron", "enable", job_id], must_contain=["Enabled"])
        self.run("cron log", ["cron", "log", "--job", job_id], expect=0)
        self.run("cron remove", ["cron", "remove", job_id], must_contain=["Removed"])
        self.run("heartbeat status", ["heartbeat", "status"], must_contain=["Heartbeat:"])
        self.run("heartbeat run", ["heartbeat", "run"], expect=0)

    def run_failure_path(self) -> None:
        self.run(
            "run failure path",
            ["run", "hello"],
            expect=1,
            must_contain=["Connection error", "OPENAI_BASE_URL"],
        )

    def summary(self) -> int:
        width = max(len(r.name) for r in self.results) if self.results else 10
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            print(f"[{status}] {result.name.ljust(width)}")
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print()
        print(f"Summary: {passed}/{total} checks passed")
        if passed != total:
            failed = next(r for r in self.results if not r.passed)
            print()
            print("First failure details:")
            print(failed.details)
            return 1
        return 0


def main() -> int:
    if not Path(PYTHON).exists():
        print(f"Expected virtualenv python at {PYTHON}", file=sys.stderr)
        return 1

    verifier = Verifier()
    try:
        verifier.run_help_matrix()
        verifier.run_bootstrap()
        verifier.run_session_flow()
        verifier.run_memory_flow()
        verifier.run_catalog_flow()
        verifier.run_template_flow()
        verifier.run_agent_team_flow()
        verifier.run_rag_flow()
        verifier.run_scheduler_flow()
        verifier.run_failure_path()
        return verifier.summary()
    finally:
        shutil.rmtree(verifier.tmpdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
