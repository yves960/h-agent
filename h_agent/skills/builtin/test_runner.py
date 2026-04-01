"""
h_agent/skills/builtin/test_runner.py - Test Runner Skill
"""

import subprocess
from pathlib import Path
from h_agent.skills.base import Skill, SkillContext, SkillResult


class TestRunnerSkill(Skill):
    """Test runner skill."""

    name = "test_runner"
    description = "Run tests and analyze results"
    parameters = {
        "command": {
            "type": "string",
            "description": "Test command to run",
            "required": True
        },
        "fail_fast": {
            "type": "boolean",
            "description": "Stop on first failure",
            "required": False
        }
    }

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        command = kwargs["command"]
        fail_fast = kwargs.get("fail_fast", False)

        # Build command
        cmd = command
        if fail_fast:
            cmd = f"{command} -x"

        # Run tests
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(context.working_dir)
        )

        output = result.stdout + result.stderr

        return SkillResult(
            success=result.returncode == 0,
            output=output,
            artifacts={"return_code": result.returncode}
        )
