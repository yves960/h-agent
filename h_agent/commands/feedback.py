"""
h_agent/commands/feedback.py - /feedback Command

Open GitHub issues page for feedback and bug reports.
"""

import subprocess
import sys
import webbrowser

from h_agent.commands.base import Command, CommandContext, CommandResult


class FeedbackCommand(Command):
    name = "feedback"
    description = "Send feedback, report bugs, or request features via GitHub"
    aliases = ["issue", "bug", "suggest"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute feedback command."""
        github_url = self._get_github_url()
        issues_url = f"{github_url}/issues/new"

        lines = ["🐛💡 Feedback & Support\n"]
        lines.append(f"GitHub: {github_url}")
        lines.append(f"Issues: {issues_url}\n")

        if args.strip():
            # User provided feedback text
            feedback_text = args.strip()
            lines.append("📝 Your feedback:")
            lines.append(f'   "{feedback_text}"\n')
            lines.append("Please open the issues page to submit your feedback.")

        lines.append("\n📋 Before reporting a bug, please:")
        lines.append("   1. Check existing issues")
        lines.append("   2. Run /doctor to verify your setup")
        lines.append("   3. Include relevant error messages")
        lines.append("\n🔧 Common issues:")
        lines.append("   - Run /doctor for diagnostics")
        lines.append("   - Run /clear to reset conversation")
        lines.append("   - Check /config for correct settings")

        # Try to open browser
        try:
            lines.append(f"\n🌐 Opening GitHub issues page...")
            webbrowser.open(issues_url)
        except Exception:
            lines.append(f"\n💡 Manually visit: {issues_url}")

        return CommandResult.ok("\n".join(lines))

    def _get_github_url(self) -> str:
        """Get the GitHub repository URL."""
        try:
            # Try to detect from git remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Convert git URL to web URL
                if url.startswith("git@github.com:"):
                    url = url.replace("git@github.com:", "https://github.com/")
                if url.endswith(".git"):
                    url = url[:-4]
                if "github.com" in url:
                    return url
        except Exception:
            pass

        # Fallback
        return "https://github.com/user/h-agent"

    def get_help(self) -> str:
        return f"""/{self.name} - {self.description}

Opens the GitHub issues page where you can:
  - Report bugs
  - Request new features
  - Ask questions
  - Submit feedback

Usage:
  /{self.name} [optional feedback text]

Examples:
  /{self.name}
  /{self.name} It would be great to have...
  /{self.name} Found a bug when using...

For quick bug reports, just run:
  /{self.name}

For immediate issues:
  - Check /doctor for diagnostics
  - Check /help for command reference
"""
