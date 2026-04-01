"""
h_agent/permissions/checker.py - Permission Checker

Implements permission checking logic for tool execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from h_agent.permissions.context import PermissionContext, PermissionMode
from h_agent.permissions.rules import (
    match_any_pattern,
    extract_paths_from_args,
    is_safe_path,
    detect_dangerous_operation,
    assess_risk_level,
    RiskLevel,
)


class PermissionDecision:
    """Permission decision outcomes."""
    ALLOW = "allow"      # Allow without asking
    DENY = "deny"       # Deny without asking
    ASK = "ask"         # Ask user for confirmation


@dataclass
class PermissionResult:
    """
    Result of a permission check.
    
    Attributes:
        decision: The decision (allow, deny, ask)
        reason: Human-readable reason for the decision
        risk_level: Risk level (low, medium, high, critical)
        requires_confirmation: Whether user confirmation is needed
    """
    decision: str
    reason: Optional[str] = None
    risk_level: Optional[str] = None
    requires_confirmation: bool = False

    @property
    def is_allowed(self) -> bool:
        """Check if the result is an allow decision."""
        return self.decision == PermissionDecision.ALLOW

    @property
    def is_denied(self) -> bool:
        """Check if the result is a deny decision."""
        return self.decision == PermissionDecision.DENY

    @property
    def needs_confirmation(self) -> bool:
        """Check if user confirmation is needed."""
        return self.requires_confirmation


class PermissionChecker:
    """
    Checks permissions for tool execution.
    
    Implements the permission checking logic:
    1. Check always_deny rules (highest priority)
    2. Check always_allow rules
    3. Check mode-based defaults
    4. Detect dangerous operations
    5. Assess risk level
    
    Example:
        ctx = PermissionContext(mode=PermissionMode.AUTO)
        checker = PermissionChecker(ctx)
        
        result = checker.check("bash", {"command": "ls -la"})
        if result.is_allowed:
            execute_tool()
        elif result.needs_confirmation:
            ask_user()
    """

    def __init__(self, context: PermissionContext):
        """
        Initialize the permission checker.
        
        Args:
            context: Permission context with rules and mode
        """
        self.context = context

    def check(self, tool_name: str, args: dict) -> PermissionResult:
        """
        Check if a tool execution is allowed.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            PermissionResult with decision and reasoning
        """
        # 1. Check always_deny rules first (highest priority)
        if self.context.should_auto_deny(tool_name, args):
            return PermissionResult(
                decision=PermissionDecision.DENY,
                reason=f"Tool '{tool_name}' matches always-deny rule",
                risk_level=RiskLevel.HIGH,
                requires_confirmation=False,
            )

        # 2. Check always_allow rules
        if self.context.should_auto_approve(tool_name, args):
            return PermissionResult(
                decision=PermissionDecision.ALLOW,
                reason=f"Tool '{tool_name}' matches always-allow rule",
                risk_level=RiskLevel.LOW,
                requires_confirmation=False,
            )

        # 3. Handle mode-based decisions
        if self.context.mode == PermissionMode.DENY:
            return PermissionResult(
                decision=PermissionDecision.DENY,
                reason="Permission mode is set to deny all",
                risk_level=RiskLevel.MEDIUM,
                requires_confirmation=False,
            )

        if self.context.mode == PermissionMode.BYPASS:
            return PermissionResult(
                decision=PermissionDecision.ALLOW,
                reason="Permission mode is set to bypass (dangerous!)",
                risk_level=RiskLevel.HIGH,
                requires_confirmation=False,
            )

        # 4. Detect dangerous operations
        danger = self._detect_danger(tool_name, args)
        if danger:
            risk_level, reason = danger
            return PermissionResult(
                decision=PermissionDecision.ASK if self.context.mode == PermissionMode.AUTO else PermissionDecision.DENY,
                reason=reason,
                risk_level=risk_level,
                requires_confirmation=True,
            )

        # 5. Assess general risk level
        risk_level, reason = assess_risk_level(tool_name, args)

        # 6. Decide based on mode
        if self.context.mode == PermissionMode.AUTO:
            if risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM):
                return PermissionResult(
                    decision=PermissionDecision.ALLOW,
                    reason=reason or f"Tool '{tool_name}' is low/medium risk",
                    risk_level=risk_level,
                    requires_confirmation=False,
                )
            else:
                return PermissionResult(
                    decision=PermissionDecision.ASK,
                    reason=reason or f"Tool '{tool_name}' is high risk",
                    risk_level=risk_level,
                    requires_confirmation=True,
                )

        # DEFAULT mode: ask for everything except trivial cases
        if risk_level == RiskLevel.LOW:
            return PermissionResult(
                decision=PermissionDecision.ALLOW,
                reason=reason or "Low risk operation",
                risk_level=risk_level,
                requires_confirmation=False,
            )

        return PermissionResult(
            decision=PermissionDecision.ASK,
            reason=reason or f"Tool '{tool_name}' requires confirmation",
            risk_level=risk_level,
            requires_confirmation=True,
        )

    def _detect_danger(self, tool_name: str, args: dict) -> Optional[tuple]:
        """
        Detect dangerous operations in tool arguments.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Tuple of (risk_level, reason) if danger detected, None otherwise
        """
        # For bash/shell commands, check the command string
        if tool_name.lower() in ("bash", "shell", "exec", "run"):
            command = args.get("command", args.get("cmd", ""))
            if isinstance(command, str):
                danger_reason = detect_dangerous_operation(command)
                if danger_reason:
                    return RiskLevel.CRITICAL, f"Dangerous command detected: {danger_reason}"
                
                # Check for system modification
                if any(kw in command.lower() for kw in ["sudo", "su -", "chmod 777", "rm -rf"]):
                    return RiskLevel.HIGH, "Command may modify system state"

        # For file operations, check paths
        paths = extract_paths_from_args(args)
        if paths:
            # Check if paths are within allowed directories
            if self.context.working_dirs:
                for path in paths:
                    safe, reason = is_safe_path(path, self.context.working_dirs)
                    if not safe:
                        return RiskLevel.HIGH, reason

            # Check for dangerous file patterns
            dangerous_extensions = [".exe", ".dll", ".so", ".dylib"]
            for path in paths:
                for ext in dangerous_extensions:
                    if path.endswith(ext):
                        return RiskLevel.MEDIUM, f"Binary file operation: {ext}"

        return None

    def check_interactive(self, tool_name: str, args: dict) -> PermissionResult:
        """
        Check permissions in interactive mode (for REPL).
        
        This is the same as check() but optimized for user interaction.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            PermissionResult
        """
        return self.check(tool_name, args)
