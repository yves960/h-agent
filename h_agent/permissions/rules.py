"""
h_agent/permissions/rules.py - Rule Matching Utilities

Provides pattern matching and safety checking utilities.
"""

from __future__ import annotations

import os
import re
import fnmatch
from typing import List, Optional, Tuple


# ============================================================
# Pattern Matching
# ============================================================

def match_pattern(text: str, pattern: str) -> bool:
    """
    Check if text matches a pattern.
    
    Supports:
    - Glob patterns (*, ?)
    - Regular expressions (if wrapped in /.../)
    - Substring containment
    
    Args:
        text: Text to check
        pattern: Pattern to match against
        
    Returns:
        True if text matches pattern
    """
    if not pattern:
        return True
    
    # Regex pattern: /.../
    if pattern.startswith("/") and pattern.endswith("/"):
        try:
            return bool(re.search(pattern[1:-1], text))
        except re.error:
            return False
    
    # Glob pattern
    if "*" in pattern or "?" in pattern or "[" in pattern:
        return fnmatch.fnmatch(text, pattern)
    
    # Substring match (case-sensitive)
    if pattern in text:
        return True
    
    # Case-insensitive match
    if pattern.lower() in text.lower():
        return True
    
    return False


def match_any_pattern(text: str, patterns: List[str]) -> bool:
    """Check if text matches any of the patterns."""
    return any(match_pattern(text, p) for p in patterns)


def extract_paths_from_args(args: dict) -> List[str]:
    """
    Extract file/directory paths from tool arguments.
    
    Handles common argument names and nested structures.
    
    Args:
        args: Tool arguments dict
        
    Returns:
        List of file paths found
    """
    paths = []
    
    # Common path argument names
    path_keys = ["path", "file", "file_path", "directory", "dir", "target", "source", "destination"]
    
    for key, value in args.items():
        if key in path_keys and isinstance(value, str):
            paths.append(value)
        elif key in path_keys and isinstance(value, list):
            paths.extend(v for v in value if isinstance(v, str))
        elif isinstance(value, dict):
            # Recurse into nested dicts
            paths.extend(extract_paths_from_args(value))
    
    return paths


def is_safe_path(path: str, allowed_dirs: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Check if a path is safe (within allowed directories).
    
    Args:
        path: File path to check
        allowed_dirs: List of allowed directory paths
        
    Returns:
        Tuple of (is_safe, reason_if_unsafe)
    """
    if not allowed_dirs:
        return True, None
    
    # Expand user home
    path = os.path.expanduser(path)
    
    # Resolve to absolute path
    try:
        abs_path = os.path.abspath(path)
    except (OSError, ValueError):
        return False, "Invalid path"
    
    for allowed_dir in allowed_dirs:
        allowed_dir = os.path.expanduser(allowed_dir)
        abs_allowed = os.path.abspath(allowed_dir)
        
        if abs_path.startswith(abs_allowed + os.sep) or abs_path == abs_allowed:
            return True, None
    
    return False, f"Path '{path}' is outside allowed directories"


# ============================================================
# Dangerous Pattern Detection
# ============================================================

# Patterns that indicate dangerous operations
DANGEROUS_PATTERNS = [
    # Filesystem destruction
    (r"rm\s+-rf\s+/", "Attempting to delete root filesystem"),
    (r"rm\s+-rf\s+\*\s*$", "Recursive delete of current directory"),
    (r"dd\s+if=.*of=/dev/", "Direct disk write detected"),
    (r"mkfs", "Filesystem creation"),
    (r"fdisk", "Partition table manipulation"),
    
    # Network attacks
    (r"nmap\s+[^s]", "Network port scanning"),
    (r"curl.*--data-urldefault", "URL injection attempt"),
    (r"wget\s+-- Spider", "Web spidering"),
    
    # Database destruction
    (r"DROP\s+DATABASE", "Database deletion"),
    (r"DROP\s+TABLE", "Table deletion"),
    (r"DELETE\s+FROM\s+\w+\s*$", "Full table deletion"),
    (r"TRUNCATE", "Table truncation"),
    
    # System modification
    (r"chmod\s+777", "Overly permissive file permissions"),
    (r"chown\s+", "Ownership change"),
    (r"sudo\s+su", "Privilege escalation"),
    
    # Environment modification
    (r"export\s+.*=", "Environment variable modification"),
    (r"source\s+/etc/", "Loading system config"),
    
    # Process termination
    (r"kill\s+-9\s+1", "Killing init process"),
    (r"killall", "Killing all processes"),
]

# Patterns for read-only/safe operations
SAFE_PATTERNS = [
    r"^ls\b",
    r"^pwd\b",
    r"^cd\b",
    r"^echo\b",
    r"^cat\b",
    r"^head\b",
    r"^tail\b",
    r"^grep\b",
    r"^find\b.*-type\s+f",
    r"^git\s+status\b",
    r"^git\s+diff\b",
    r"^git\s+log\b",
    r"^git\s+branch\b",
    r"^git\s+remote\s+-v\b",
]


def detect_dangerous_operation(command: str) -> Optional[str]:
    """
    Detect if a command contains dangerous operations.
    
    Args:
        command: Command string to check
        
    Returns:
        Description of danger if found, None otherwise
    """
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return description
    return None


def is_read_only_operation(command: str) -> bool:
    """
    Check if a command is read-only.
    
    Args:
        command: Command string to check
        
    Returns:
        True if command appears read-only
    """
    for pattern in SAFE_PATTERNS:
        if re.match(pattern, command.strip()):
            return True
    return False


# ============================================================
# Risk Level Assessment
# ============================================================

class RiskLevel:
    """Risk level constants."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def assess_risk_level(tool_name: str, args: dict) -> Tuple[str, Optional[str]]:
    """
    Assess the risk level of a tool call.
    
    Args:
        tool_name: Name of the tool
        args: Tool arguments
        
    Returns:
        Tuple of (risk_level, reason)
    """
    # High-risk tools
    high_risk_tools = {"bash", "shell", "exec", "run", "sudo"}
    
    if tool_name.lower() in high_risk_tools:
        # Check command argument
        command = args.get("command", args.get("cmd", ""))
        if isinstance(command, str):
            # Check for dangerous patterns
            danger = detect_dangerous_operation(command)
            if danger:
                return RiskLevel.CRITICAL, danger
            
            # Check for write operations
            write_patterns = [r">\s*/dev/", r"\|\s*tee", r"chmod\s+[^0]", r"chown"]
            for pattern in write_patterns:
                if re.search(pattern, command):
                    return RiskLevel.HIGH, "Command modifies system state"
            
            # Check for system-level operations
            system_patterns = [r"sudo", r"su\s+-", r"\|\s*bash", r"&"]
            for pattern in system_patterns:
                if re.search(pattern, command):
                    return RiskLevel.MEDIUM, "Command may require elevated privileges"
    
    # Medium-risk: file write operations
    medium_risk_tools = {"write", "edit", "create", "mv", "cp"}
    if tool_name.lower() in medium_risk_tools:
        path = args.get("path", args.get("file", ""))
        if isinstance(path, str):
            # Check if system directories
            if path.startswith("/etc") or path.startswith("/bin") or path.startswith("/usr/bin"):
                return RiskLevel.HIGH, "Modifying system directory"
            return RiskLevel.MEDIUM, "File modification"
    
    # Low-risk: read operations
    low_risk_tools = {"read", "grep", "search", "find", "list"}
    if tool_name.lower() in low_risk_tools:
        return RiskLevel.LOW, "Read-only operation"
    
    # Default: assume medium risk for unknown tools
    return RiskLevel.MEDIUM, "Tool modifies state"
