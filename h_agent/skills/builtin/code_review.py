"""
h_agent/skills/builtin/code_review.py - Code Review Skill
"""

from h_agent.skills.base import Skill, SkillContext, SkillResult


class CodeReviewSkill(Skill):
    """Code review skill."""

    name = "code_review"
    description = "Review code for issues and improvements"
    parameters = {
        "path": {
            "type": "string",
            "description": "File or directory to review",
            "required": True
        },
        "focus": {
            "type": "string",
            "description": "Focus area: security, performance, style, all",
            "required": False
        }
    }

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        path = kwargs["path"]
        focus = kwargs.get("focus", "all")

        # Read code
        code = ""
        try:
            from pathlib import Path
            p = Path(path)
            if p.is_file():
                code = p.read_text()
            elif p.is_dir():
                code_parts = []
                for f in p.rglob("*.py"):
                    code_parts.append(f"# {f}\n{f.read_text()}")
                code = "\n\n".join(code_parts)
        except Exception as e:
            return SkillResult(success=False, output="", error=str(e))

        prompt = f"""Review the code below.
Path: {path}
Focus: {focus}

```{code}
```

Provide:
1. Summary
2. Issues found (if any)
3. Suggestions for improvement
"""

        # Call LLM if available
        output = prompt
        if context.run_tool:
            try:
                result = context.run_tool("llm", {"prompt": prompt})
                if isinstance(result, str):
                    output = result
                elif hasattr(result, "output"):
                    output = result.output
            except Exception:
                pass

        return SkillResult(success=True, output=output)
