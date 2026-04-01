"""
h_agent/commands/upgrade.py - /upgrade Command

Check for updates and provide upgrade instructions.
"""

import subprocess
import sys

from h_agent.commands.base import Command, CommandContext, CommandResult


class UpgradeCommand(Command):
    name = "upgrade"
    description = "Check for updates and upgrade h-agent"
    aliases = ["update"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute upgrade command."""
        lines = ["🔄 h-agent Upgrade Check\n"]

        # Check current version
        try:
            from h_agent import __version__
            lines.append(f"Current version: {__version__}")
        except ImportError:
            lines.append("Version: Unknown (installed via editable mode?)")

        # Check pip version
        lines.append(f"\n📦 Package Manager Check:")
        lines.append(f"  Python: {sys.version.split()[0]}")
        lines.append(f"  pip: {self._get_pip_version()}")

        # Check for updates
        lines.append("\n🔍 Checking for updates...")

        update_info = self._check_for_updates()

        if update_info["has_update"]:
            lines.append(f"\n✨ New version available: {update_info['latest']}")
            lines.append(f"   Current: {update_info['current']}")
            lines.append("\n📋 To upgrade, run:")
            lines.append("   pip install --upgrade h-agent")
            if "github" in update_info.get("url", ""):
                lines.append("\n   Or for development version:")
                lines.append("   pip install --upgrade git+https://github.com/user/h-agent.git")
        else:
            lines.append("\n✅ You have the latest version!")
            lines.append(f"   {update_info['current']}")

        lines.append("\n---")
        lines.append("💡 To manually check PyPI for updates:")
        lines.append("   pip index versions h-agent")
        lines.append("\n💡 To upgrade:")
        lines.append("   pip install --upgrade h-agent")

        return CommandResult.ok("\n".join(lines))

    def _get_pip_version(self) -> str:
        """Get pip version."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split()[1] if result.stdout else "unknown"
        except Exception:
            pass
        return "unknown"

    def _check_for_updates(self) -> dict:
        """Check if there's a newer version on PyPI."""
        try:
            # Try to get latest version from PyPI
            result = subprocess.run(
                [sys.executable, "-m", "pip", "index", "versions", "h-agent"],
                capture_output=True,
                text=True,
                timeout=10
            )

            latest = "unknown"
            if result.returncode == 0:
                # Parse output like "Available versions: 1.0.0, 1.0.1, ..."
                output = result.stdout
                if "Available versions:" in output:
                    versions_str = output.split("Available versions:")[1].strip()
                    versions = [v.strip() for v in versions_str.split(",")]
                    if versions:
                        latest = versions[-1].strip("() ")

            # Get current version
            current = "unknown"
            try:
                from h_agent import __version__
                current = __version__
            except ImportError:
                current = "editable"

            has_update = False
            if latest != "unknown" and current != "editable":
                try:
                    # Simple version comparison
                    from packaging.version import parse
                    has_update = parse(latest) > parse(current)
                except Exception:
                    pass

            return {
                "has_update": has_update,
                "current": current,
                "latest": latest,
                "url": "https://pypi.org/project/h-agent/",
            }
        except Exception as e:
            return {
                "has_update": False,
                "current": "unknown",
                "latest": "unknown",
                "error": str(e),
            }

    def get_help(self) -> str:
        return f"""/{self.name} - {self.description}

Checks for available updates and shows upgrade instructions.

Usage:
  /{self.name}

The command will:
1. Show your current version
2. Check PyPI for the latest version
3. Provide upgrade commands if an update is available

Note: If you installed via git clone, use:
  git pull && pip install -e .
"""

    def _get_github_url(self) -> str:
        """Get GitHub URL for the project."""
        try:
            from h_agent import __file__
            import os
            git_dir = os.path.dirname(__file__)
            while git_dir and git_dir != "/":
                if os.path.exists(os.path.join(git_dir, ".git")):
                    # Found git repo, try to get remote
                    try:
                        result = subprocess.run(
                            ["git", "remote", "get-url", "origin"],
                            cwd=git_dir,
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            url = result.stdout.strip()
                            if url.endswith(".git"):
                                url = url[:-4]
                            if "github.com" in url:
                                return url
                    except Exception:
                        pass
                git_dir = os.path.dirname(git_dir)
        except Exception:
            pass
        return "https://github.com/user/h-agent"
