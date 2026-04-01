"""
h_agent/permissions/context.py - Permission Context

Defines the permission context, mode, and rule structures.
"""

from __future__ import annotations

import os
import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any
from enum import Enum


class PermissionMode(str, Enum):
    """
    Permission mode for tool execution.
    
    Attributes:
        DEFAULT: Ask user for confirmation on each dangerous operation
        AUTO: Automatically allow safe operations, ask for dangerous ones
        BYPASS: Allow all operations without confirmation (DANGEROUS!)
        DENY: Deny all tool executions
    """
    DEFAULT = "default"    # 每次询问
    AUTO = "auto"          # 自动允许安全操作
    BYPASS = "bypass"      # 允许所有（危险！）
    DENY = "deny"          # 拒绝所有


@dataclass
class PermissionRule:
    """
    A single permission rule.
    
    Attributes:
        tool_name: Tool name pattern (supports * wildcards)
        patterns: List of glob patterns for arguments (e.g., ["*.py", "src/*"])
        action: "allow" or "deny"
        description: Optional human-readable description
    """
    tool_name: str
    patterns: List[str] = field(default_factory=list)
    action: Literal["allow", "deny"] = "allow"
    description: Optional[str] = None

    def matches_tool(self, tool_name: str) -> bool:
        """Check if tool name matches this rule."""
        return fnmatch.fnmatch(tool_name, self.tool_name)


@dataclass
class PermissionContext:
    """
    Permission context for tool execution.
    
    Attributes:
        mode: Permission mode (default, auto, bypass, deny)
        always_allow: List of rules that always allow
        always_deny: List of rules that always deny
        working_dirs: List of allowed working directories
       危险操作黑名单: Patterns for dangerous operations (e.g., "rm -rf", "DROP TABLE")
    
    Example:
        ctx = PermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=[
                PermissionRule(tool_name="read", patterns=["*.py"]),
                PermissionRule(tool_name="bash", patterns=["ls", "pwd", "git status"]),
            ],
            always_deny=[
                PermissionRule(tool_name="bash", patterns=["rm -rf*", "DROP DATABASE*"]),
            ],
            working_dirs=["/home/user/project", "~/code"],
        )
    """
    mode: PermissionMode = PermissionMode.DEFAULT
    always_allow: List[PermissionRule] = field(default_factory=list)
    always_deny: List[PermissionRule] = field(default_factory=list)
    working_dirs: List[str] = field(default_factory=list)
    dangerous_blacklist: List[str] = field(default_factory=list)

    def should_auto_approve(self, tool_name: str, args: dict) -> bool:
        """
        Check if tool should be auto-approved.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            True if should auto-approve
        """
        # Check bypass mode
        if self.mode == PermissionMode.BYPASS:
            return True
        
        # Check deny mode
        if self.mode == PermissionMode.DENY:
            return False
        
        # Check always_allow rules
        for rule in self.always_allow:
            if rule.matches_tool(tool_name):
                if not rule.patterns:
                    # No patterns means match all
                    return True
                # Check argument patterns
                args_str = str(args)
                for pattern in rule.patterns:
                    if self._match_any_pattern(args_str, pattern):
                        return True
        
        return False

    def should_auto_deny(self, tool_name: str, args: dict) -> bool:
        """
        Check if tool should be auto-denied.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            True if should auto-deny
        """
        # Check deny mode
        if self.mode == PermissionMode.DENY:
            return True
        
        # Check bypass mode (never auto-deny)
        if self.mode == PermissionMode.BYPASS:
            return False
        
        # Check always_deny rules
        for rule in self.always_deny:
            if rule.matches_tool(tool_name):
                if not rule.patterns:
                    # No patterns means match all
                    return True
                # Check argument patterns
                args_str = str(args)
                for pattern in rule.patterns:
                    if self._match_any_pattern(args_str, pattern):
                        return True
        
        return False

    def is_path_safe(self, path: str) -> bool:
        """
        Check if a file path is within allowed working directories.
        
        Args:
            path: File path to check
            
        Returns:
            True if path is safe (within allowed dirs)
        """
        if not self.working_dirs:
            return True  # No restrictions
        
        # Resolve path
        abs_path = os.path.abspath(os.path.expanduser(path))
        
        for allowed_dir in self.working_dirs:
            abs_allowed = os.path.abspath(os.path.expanduser(allowed_dir))
            if abs_path.startswith(abs_allowed):
                return True
        
        return False

    def _match_any_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches any pattern variant."""
        # Direct glob match (exact match with wildcards)
        if fnmatch.fnmatch(text, pattern):
            return True
        
        # Simple substring match (pattern is contained in text)
        if pattern in text:
            return True
        
        # Check if pattern is contained in text (case-insensitive)
        if pattern.lower() in text.lower():
            return True
        
        # Check for wildcard patterns
        if pattern.startswith("*") and pattern.endswith("*"):
            # Middle wildcard: *foo*
            inner = pattern[1:-1]
            if inner in text:
                return True
        elif pattern.startswith("*"):
            # Ends with wildcard: *foo
            suffix = pattern[1:]
            if text.endswith(suffix) or suffix in text:
                return True
        elif pattern.endswith("*"):
            # Starts with wildcard: foo*
            prefix = pattern[:-1]
            if text.startswith(prefix) or prefix in text:
                return True
        
        # Also check command-like patterns (space-insensitive)
        if " " in pattern:
            pattern_no_wildcard = pattern.replace("*", "").strip()
            if pattern_no_wildcard in text.replace("  ", " ").strip():
                return True
        
        return False

    def add_always_allow(self, tool_name: str, *patterns: str) -> None:
        """
        Add an always-allow rule.
        
        Args:
            tool_name: Tool name (supports *)
            *patterns: Argument patterns to match
        """
        self.always_allow.append(
            PermissionRule(tool_name=tool_name, patterns=list(patterns))
        )

    def add_always_deny(self, tool_name: str, *patterns: str) -> None:
        """
        Add an always-deny rule.
        
        Args:
            tool_name: Tool name (supports *)
            *patterns: Argument patterns to match
        """
        self.always_deny.append(
            PermissionRule(tool_name=tool_name, patterns=list(patterns))
        )


# ============================================================
# Default Context Factory
# ============================================================

def create_default_context(
    mode: PermissionMode = PermissionMode.DEFAULT,
    working_dirs: Optional[List[str]] = None,
) -> PermissionContext:
    """
    Create a default permission context with safe defaults.
    
    Args:
        mode: Permission mode
        working_dirs: Allowed working directories
        
    Returns:
        Configured PermissionContext
    """
    ctx = PermissionContext(mode=mode, working_dirs=working_dirs or [])
    
    # Default safe patterns for common tools
    if mode in (PermissionMode.DEFAULT, PermissionMode.AUTO):
        # Allow safe read operations
        ctx.add_always_allow("read", "*.py", "*.txt", "*.md", "*.json", "*.yaml", "*.yml")
        ctx.add_always_allow("read", "*.js", "*.ts", "*.html", "*.css")
        ctx.add_always_allow("read", "*.sh", "*.bash", "*.zsh")
        
        # Allow safe git commands
        ctx.add_always_allow("git", "status", "diff", "log", "branch", "remote -v")
        
        # Allow safe bash commands
        ctx.add_always_allow("bash", "ls", "pwd", "cd", "echo", "cat")
        
        # Deny dangerous operations
        ctx.add_always_deny("bash", "rm -rf*", "dd", "mkfs", "fdisk")
        ctx.add_always_deny("bash", "DROP DATABASE*", "DELETE FROM* WHERE*")
        ctx.add_always_deny("write", "*.sh", "*.bash")  # Writing shell scripts needs review
    
    return ctx
