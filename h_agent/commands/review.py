"""
h_agent/commands/review.py - /review Command

Review code changes with LLM assistance.
"""

import subprocess

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.core.client import get_client


class ReviewCommand(Command):
    name = "review"
    description = "Review code changes"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        # Get diff
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True, text=True
        )
        diff = result.stdout

        if not diff:
            return CommandResult(
                success=False,
                output="No changes to review"
            )

        # Use LLM to review
        prompt = f"""Review these code changes and provide:
1. Summary of changes (brief)
2. Potential issues or bugs
3. Suggestions for improvement

Be concise and focus on the most important feedback.

Diff:
{diff[:5000]}"""

        try:
            client = get_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful code reviewer. Provide constructive, actionable feedback."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.5,
            )
            review_result = response.choices[0].message.content.strip()
        except Exception as e:
            return CommandResult(
                success=False,
                output=f"Review failed: {e}"
            )

        return CommandResult(
            success=True,
            output=review_result
        )
