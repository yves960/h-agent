"""
h_agent/screens/doctor.py - Doctor Screen

Full-screen diagnostic UI for h-agent environment check.
Shows comprehensive health status of the installation.
"""

import sys
import platform
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Rich imports for fancy terminal UI
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""
    name: str
    status: str  # "pass", "fail", "warn", "skip"
    message: str
    details: str = ""


class DoctorScreen:
    """
    Full-screen doctor UI for h-agent diagnostics.

    Features:
    - Environment checks (Python, dependencies, API)
    - Configuration validation
    - Tool and command registry checks
    - Memory and storage checks
    """

    def __init__(self):
        self.console = Console() if HAS_RICH else None
        self.results: List[CheckResult] = []

    def _add_result(self, name: str, status: str, message: str, details: str = ""):
        """Add a check result."""
        self.results.append(CheckResult(name, status, message, details))

    def run_checks(self) -> List[CheckResult]:
        """Run all diagnostic checks."""
        self.results = []

        # 1. Python Environment
        self._check_python()

        # 2. Core Dependencies
        self._check_dependencies()

        # 3. API Configuration
        self._check_api()

        # 4. Configuration Files
        self._check_config()

        # 5. Tool Registry
        self._check_tools()

        # 6. Command Registry
        self._check_commands()

        # 7. Memory System
        self._check_memory()

        # 8. Platform Info
        self._check_platform()

        return self.results

    def _check_python(self):
        """Check Python environment."""
        version = sys.version
        version_info = sys.version_info

        if version_info.major >= 3 and version_info.minor >= 10:
            status = "pass"
            msg = f"Python {version_info.major}.{version_info.minor}.{version_info.micro}"
        else:
            status = "warn"
            msg = f"Python {version_info.major}.{version_info.minor} (recommended: 3.10+)"

        self._add_result("Python", status, msg, f"Full: {version}")

    def _check_dependencies(self):
        """Check core dependencies."""
        deps = [
            ("openai", "OpenAI API client"),
            ("tiktoken", "Token counting"),
            ("yaml", "PyYAML for config"),
            ("rich", "Terminal UI"),
        ]

        for dep_name, dep_desc in deps:
            try:
                mod = __import__(dep_name)
                version = getattr(mod, "__version__", "installed")
                self._add_result(dep_name, "pass", f"{dep_desc}: {version}")
            except ImportError:
                self._add_result(dep_name, "fail", f"{dep_desc}: Not installed")

    def _check_api(self):
        """Check API configuration."""
        try:
            from h_agent.core.client import get_client
            client = get_client()
            self._add_result("API Client", "pass", "Client configured")
        except Exception as e:
            self._add_result("API Client", "fail", f"Configuration error: {str(e)[:50]}")

        try:
            from h_agent.core.config import MODEL_ID
            self._add_result("Model", "pass", f"Configured: {MODEL_ID}")
        except Exception as e:
            self._add_result("Model", "warn", f"Using default: {str(e)[:30]}")

    def _check_config(self):
        """Check configuration files."""
        try:
            from h_agent.core.config import AGENT_CONFIG_DIR, AGENT_CONFIG_FILE
            import os

            if AGENT_CONFIG_DIR.exists():
                self._add_result("Config Dir", "pass", f"Exists: {AGENT_CONFIG_DIR}")
            else:
                self._add_result("Config Dir", "warn", "Does not exist (will be created)")

            if AGENT_CONFIG_FILE.exists():
                self._add_result("Config File", "pass", f"Found: {AGENT_CONFIG_FILE.name}")
            else:
                self._add_result("Config File", "warn", "Not found (using defaults)")
        except Exception as e:
            self._add_result("Config", "fail", f"Error: {str(e)[:50]}")

    def _check_tools(self):
        """Check tool registry."""
        try:
            from h_agent.tools import get_registry
            registry = get_registry()
            tools = registry.list_tools()
            self._add_result(
                "Tools",
                "pass",
                f"{len(tools)} tools registered",
                ", ".join(t.get("name", "unknown") for t in tools[:5]) + "..."
                if len(tools) > 5 else ", ".join(t.get("name", "unknown") for t in tools)
            )
        except Exception as e:
            self._add_result("Tools", "fail", f"Error: {str(e)[:50]}")

    def _check_commands(self):
        """Check command registry."""
        try:
            from h_agent.commands import get_registry
            registry = get_registry()
            commands = registry.list_commands()
            self._add_result(
                "Commands",
                "pass",
                f"{len(commands)} commands registered",
                ", ".join(c.name for c in commands[:5]) + "..."
                if len(commands) > 5 else ", ".join(c.name for c in commands)
            )
        except Exception as e:
            self._add_result("Commands", "fail", f"Error: {str(e)[:50]}")

    def _check_memory(self):
        """Check memory system."""
        try:
            from h_agent.memory.long_term import LongTermMemory, MemoryType, LONG_TERM_FILE
            memory = LongTermMemory()
            total = sum(len(entries) for entries in memory._data.values())

            if LONG_TERM_FILE.exists():
                size = LONG_TERM_FILE.stat().st_size
                self._add_result(
                    "Memory",
                    "pass",
                    f"{total} memories stored ({size} bytes)",
                )
            else:
                self._add_result(
                    "Memory",
                    "pass",
                    f"{total} memories (file will be created)",
                )
        except Exception as e:
            self._add_result("Memory", "fail", f"Error: {str(e)[:50]}")

    def _check_platform(self):
        """Check platform information."""
        system = platform.system()
        release = platform.release()
        machine = platform.machine()

        status = "pass" if system in ("Darwin", "Linux", "Windows") else "warn"
        self._add_result(
            "Platform",
            status,
            f"{system} {release}",
            f"Machine: {machine}",
        )

    def render(self) -> str:
        """Render the doctor screen as a string."""
        if not self.results:
            self.run_checks()

        lines = ["=" * 60]
        lines.append("🏥 h-agent Doctor - Environment Diagnostics")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        warned = sum(1 for r in self.results if r.status == "warn")

        lines.append(f"Summary: {passed} ✅  {warned} ⚠️  {failed} ❌")
        lines.append("")

        # Grouped results
        current_category = ""
        for result in self.results:
            if result.name != current_category:
                current_category = result.name
                lines.append(f"\n📌 {result.name}")

            status_icon = {
                "pass": "✅",
                "fail": "❌",
                "warn": "⚠️",
                "skip": "⏭️",
            }.get(result.status, "?")

            lines.append(f"   {status_icon} {result.message}")
            if result.details:
                lines.append(f"      └─ {result.details}")

        lines.append("")
        lines.append("=" * 60)

        # Recommendations
        if failed > 0:
            lines.append("\n💡 Recommendations:")
            for r in self.results:
                if r.status == "fail":
                    lines.append(f"   - Fix: {r.name}")
            lines.append("\n   Run: pip install -e ~/Projects/self/h-agent")

        lines.append("\nPress any key to exit...")

        return "\n".join(lines)

    def render_rich(self) -> None:
        """Render using rich library if available."""
        if not self.console:
            print(self.render())
            return

        self.console.clear()

        # Title
        self.console.print(Panel.fit(
            "🏥 h-agent Doctor",
            subtitle="Environment Diagnostics",
            style="bold blue"
        ))

        # Run checks if not done
        if not self.results:
            self.run_checks()

        # Summary
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        warned = sum(1 for r in self.results if r.status == "warn")

        # Create table
        table = Table(title="Diagnostic Results", show_header=True, header_style="bold")
        table.add_column("Status", width=8)
        table.add_column("Component", width=15)
        table.add_column("Message", width=40)
        table.add_column("Details", width=30)

        for result in self.results:
            status_icon = {
                "pass": "✅",
                "fail": "❌",
                "warn": "⚠️",
                "skip": "⏭️",
            }.get(result.status, "?")

            table.add_row(
                status_icon,
                result.name,
                result.message,
                result.details[:50] if result.details else "-"
            )

        self.console.print(table)

        # Summary panel
        summary_text = Text()
        summary_text.append(f"  Passed: {passed} ✅", style="green")
        summary_text.append(f"   Warnings: {warned} ⚠️", style="yellow")
        summary_text.append(f"   Failed: {failed} ❌", style="red")

        self.console.print(Panel(summary_text, title="Summary"))

        # Recommendations
        if failed > 0:
            recs = [r.name for r in self.results if r.status == "fail"]
            self.console.print(f"\n[yellow]💡 Fix failed checks:[/yellow] {', '.join(recs)}")


async def run_doctor_screen():
    """Run the full-screen doctor UI."""
    screen = DoctorScreen()
    screen.run_checks()

    if HAS_RICH:
        screen.render_rich()
    else:
        print(screen.render())

    # Wait for keypress (if possible)
    try:
        import tty
        import termios
        import os

        def get_char():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

        print("\nWaiting for keypress...")
        get_char()
    except Exception:
        pass


def run_doctor_check() -> List[CheckResult]:
    """
    Run doctor checks programmatically.

    Returns:
        List of CheckResult objects
    """
    screen = DoctorScreen()
    return screen.run_checks()
