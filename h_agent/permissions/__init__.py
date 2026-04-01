"""
h_agent/permissions - Permission System

Provides fine-grained permission control for tool execution.
Inspired by Claude Code's permission system.

Modules:
    context: PermissionContext, PermissionMode, PermissionRule
    checker: PermissionChecker, PermissionResult, PermissionDecision
    rules: Rule matching utilities

Usage:
    from h_agent.permissions import PermissionContext, PermissionChecker
    
    ctx = PermissionContext(mode=PermissionMode.AUTO)
    checker = PermissionChecker(ctx)
    result = checker.check("bash", {"command": "ls"})
"""

from h_agent.permissions.context import (
    PermissionContext,
    PermissionMode,
    PermissionRule,
)
from h_agent.permissions.checker import (
    PermissionChecker,
    PermissionDecision,
    PermissionResult,
)
from h_agent.permissions.rules import match_pattern, is_safe_path

__all__ = [
    "PermissionContext",
    "PermissionMode",
    "PermissionRule",
    "PermissionChecker",
    "PermissionDecision",
    "PermissionResult",
    "match_pattern",
    "is_safe_path",
]
