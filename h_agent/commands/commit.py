"""
h_agent/commands/commit.py - /commit Command

Generate a commit message and commit changes.
"""

import subprocess

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.core.client import get_client


class CommitCommand(Command):
    name = "commit"
    description = "Generate a commit message and commit changes"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        # 1. Get git diff
        result = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True, text=True
        )
        diff = result.stdout

        if not diff:
            # If no staged changes, try staging all
            subprocess.run(["git", "add", "-A"])
            result = subprocess.run(
                ["git", "diff", "--staged"],
                capture_output=True, text=True
            )
            diff = result.stdout

        if not diff:
            return CommandResult(
                success=False, 
                output="No changes to commit"
            )

        # 2. Generate commit message using LLM
        prompt = f"""Generate a concise commit message for these changes:

{diff[:3000]}

Respond with only the commit message, no explanation. Use imperative mood, max 72 characters."""

        try:
            client = get_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates concise git commit messages."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=100,
                temperature=0.3,
            )
            commit_msg = response.choices[0].message.content.strip()
        except Exception as e:
            return CommandResult(
                success=False,
                output=f"Failed to generate commit message: {e}"
            )

        # 3. Execute commit
        try:
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                return CommandResult(
                    success=False,
                    output=f"Git commit failed: {result.stderr}"
                )
        except Exception as e:
            return CommandResult(
                success=False,
                output=f"Git commit error: {e}"
            )

        return CommandResult(
            success=True,
            output=f"Committed: {commit_msg}"
        )
