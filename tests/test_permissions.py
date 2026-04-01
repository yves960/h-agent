"""
tests/test_permissions.py - Permission System Tests

Tests for the permission system implementation.
"""

import pytest
from h_agent.permissions import (
    PermissionContext,
    PermissionMode,
    PermissionRule,
    PermissionChecker,
    PermissionDecision,
    PermissionResult,
    match_pattern,
    is_safe_path,
)


class TestPermissionContext:
    """Tests for PermissionContext."""

    def test_default_mode(self):
        """Test default permission mode."""
        ctx = PermissionContext()
        assert ctx.mode == PermissionMode.DEFAULT

    def test_bypass_mode(self):
        """Test bypass mode allows everything."""
        ctx = PermissionContext(mode=PermissionMode.BYPASS)
        assert ctx.should_auto_approve("any_tool", {}) is True

    def test_deny_mode(self):
        """Test deny mode blocks everything."""
        ctx = PermissionContext(mode=PermissionMode.DENY)
        assert ctx.should_auto_deny("any_tool", {}) is True

    def test_always_allow_rule(self):
        """Test always_allow rule."""
        ctx = PermissionContext()
        ctx.add_always_allow("bash", "ls", "pwd")
        
        assert ctx.should_auto_approve("bash", {"command": "ls"}) is True
        assert ctx.should_auto_approve("bash", {"command": "pwd"}) is True
        assert ctx.should_auto_approve("bash", {"command": "rm"}) is False

    def test_always_deny_rule(self):
        """Test always_deny rule."""
        ctx = PermissionContext()
        ctx.add_always_deny("bash", "rm -rf*")
        
        assert ctx.should_auto_deny("bash", {"command": "rm -rf /"}) is True
        assert ctx.should_auto_deny("bash", {"command": "rm -rf /home"}) is True
        assert ctx.should_auto_deny("bash", {"command": "ls"}) is False

    def test_wildcard_tool_name(self):
        """Test wildcard matching in tool names."""
        ctx = PermissionContext()
        ctx.add_always_allow("file_*", "*.py")
        
        assert ctx.should_auto_approve("file_read", {"path": "test.py"}) is True
        assert ctx.should_auto_approve("file_write", {"path": "test.py"}) is True

    def test_path_safety_check(self):
        """Test path safety checking."""
        ctx = PermissionContext(working_dirs=["/home/user/project"])
        
        assert ctx.is_path_safe("/home/user/project/file.py") is True
        assert ctx.is_path_safe("/home/user/other/file.py") is False
        assert ctx.is_path_safe("/etc/passwd") is False


class TestPermissionChecker:
    """Tests for PermissionChecker."""

    def test_safe_command_allowed(self):
        """Test that safe commands are allowed in auto mode."""
        ctx = PermissionContext(mode=PermissionMode.AUTO)
        ctx.add_always_allow("bash", "ls", "pwd")
        
        checker = PermissionChecker(ctx)
        result = checker.check("bash", {"command": "ls -la"})
        
        assert result.is_allowed is True

    def test_dangerous_command_denied(self):
        """Test that dangerous commands are denied."""
        ctx = PermissionContext(mode=PermissionMode.AUTO)
        ctx.add_always_deny("bash", "rm -rf*")
        
        checker = PermissionChecker(ctx)
        result = checker.check("bash", {"command": "rm -rf /"})
        
        assert result.is_denied is True

    def test_critical_risk_detection(self):
        """Test critical risk level detection."""
        ctx = PermissionContext(mode=PermissionMode.DEFAULT)
        
        checker = PermissionChecker(ctx)
        result = checker.check("bash", {"command": "rm -rf /"})
        
        assert result.risk_level == "critical"

    def test_tool_permission_check(self):
        """Test permission check via Tool.check_permissions."""
        from h_agent.tools.base import Tool, ToolResult
        
        class TestTool(Tool):
            name = "test_tool"
            description = "A test tool"
            
            @property
            def input_schema(self):
                return {"type": "object"}
            
            async def execute(self, args):
                return ToolResult.ok("done")
        
        ctx = PermissionContext(mode=PermissionMode.AUTO)
        tool = TestTool()
        
        result = tool.check_permissions({}, ctx)
        assert result is not None


class TestPatternMatching:
    """Tests for pattern matching utilities."""

    def test_glob_pattern(self):
        """Test glob pattern matching."""
        assert match_pattern("test.py", "*.py") is True
        assert match_pattern("test.js", "*.py") is False

    def test_substring_pattern(self):
        """Test substring pattern matching."""
        assert match_pattern("rm -rf /home", "rm -rf") is True
        assert match_pattern("ls -la", "rm -rf") is False

    def test_path_safety(self):
        """Test path safety checking."""
        allowed = ["/home/user/project"]
        
        safe, reason = is_safe_path("/home/user/project/file.py", allowed)
        assert safe is True
        
        safe, reason = is_safe_path("/etc/passwd", allowed)
        assert safe is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
