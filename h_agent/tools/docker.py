#!/usr/bin/env python3
"""
h_agent/tools/docker.py - Docker operation tools

Tools:
- docker_ps: List running containers
- docker_logs: Get container logs
- docker_exec: Execute command in container
- docker_images: List Docker images
- docker_build: Build Docker image
- docker_pull: Pull Docker image
"""

import subprocess
import json
from typing import Callable, Dict, List, Any

# ============================================================
# Tool Definitions
# ============================================================

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "docker_ps",
            "description": "List running Docker containers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "all": {"type": "boolean", "description": "Show all containers (including stopped)", "default": False},
                    "format": {"type": "string", "description": "Output format (table, json)", "default": "table"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_logs",
            "description": "Get logs from a Docker container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "container": {"type": "string", "description": "Container name or ID"},
                    "lines": {"type": "integer", "description": "Number of lines to show from end", "default": 100},
                    "follow": {"type": "boolean", "description": "Stream logs continuously", "default": False},
                    "timestamps": {"type": "boolean", "description": "Show timestamps", "default": False}
                },
                "required": ["container"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_exec",
            "description": "Execute a command inside a running Docker container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "container": {"type": "string", "description": "Container name or ID"},
                    "command": {"type": "string", "description": "Command to execute inside the container"},
                    "user": {"type": "string", "description": "Run as specified user", "default": ""},
                    "workdir": {"type": "string", "description": "Working directory inside container", "default": ""}
                },
                "required": ["container", "command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_images",
            "description": "List Docker images.",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {"type": "string", "description": "Output format (table, json)", "default": "table"},
                    "filter": {"type": "string", "description": "Filter by image name", "default": ""}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_build",
            "description": "Build a Docker image from Dockerfile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Build context path (directory containing Dockerfile)"},
                    "tag": {"type": "string", "description": "Image name and tag (e.g., 'myapp:latest')"},
                    "dockerfile": {"type": "string", "description": "Path to Dockerfile (relative to path)", "default": "Dockerfile"},
                    "no_cache": {"type": "boolean", "description": "Build without cache", "default": False}
                },
                "required": ["path", "tag"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_pull",
            "description": "Pull a Docker image from registry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "description": "Image name (e.g., 'nginx:latest', 'python:3.12')"},
                    "platform": {"type": "string", "description": "Platform (e.g., 'linux/amd64', 'linux/arm64')", "default": ""}
                },
                "required": ["image"]
            }
        }
    }
]


# ============================================================
# Tool Handlers
# ============================================================

def _run_docker(args: List[str], timeout: int = 60) -> str:
    """Run a docker command and return output."""
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        if not output:
            return "(no output)"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Error: Docker command timed out"
    except FileNotFoundError:
        return "Error: docker not found. Is Docker installed and in PATH?"
    except Exception as e:
        return f"Error: {e}"


def tool_docker_ps(all: bool = False, format: str = "table") -> str:
    """List running containers."""
    args = ["ps"]
    if all:
        args.append("-a")
    if format == "json":
        args.extend(["--format", "{{json .}}"])
    else:
        args.extend(["--format", "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}"])
    return _run_docker(args)


def tool_docker_logs(
    container: str,
    lines: int = 100,
    follow: bool = False,
    timestamps: bool = False
) -> str:
    """Get container logs."""
    args = ["logs"]
    args.extend(["--tail", str(lines)])
    if follow:
        args.append("-f")
    if timestamps:
        args.append("--timestamps")
    args.append(container)
    return _run_docker(args, timeout=30 if not follow else 60)


def tool_docker_exec(
    container: str,
    command: str,
    user: str = "",
    workdir: str = ""
) -> str:
    """Execute command in container."""
    args = ["exec"]
    if user:
        args.extend(["-u", user])
    if workdir:
        args.extend(["-w", workdir])
    args.append(container)
    args.append("/bin/sh")
    args.extend(["-c", command])
    return _run_docker(args, timeout=60)


def tool_docker_images(format: str = "table", filter: str = "") -> str:
    """List Docker images."""
    args = ["images"]
    if filter:
        args.extend(["--filter", f"reference={filter}"])
    if format == "json":
        args.extend(["--format", "{{json .}}"])
    else:
        args.extend(["--format", "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"])
    return _run_docker(args)


def tool_docker_build(
    path: str,
    tag: str,
    dockerfile: str = "Dockerfile",
    no_cache: bool = False
) -> str:
    """Build Docker image."""
    args = ["build"]
    if no_cache:
        args.append("--no-cache")
    args.extend(["-f", dockerfile])
    args.extend(["-t", tag])
    args.append(path)
    return _run_docker(args, timeout=600)


def tool_docker_pull(image: str, platform: str = "") -> str:
    """Pull Docker image."""
    args = ["pull"]
    if platform:
        args.extend(["--platform", platform])
    args.append(image)
    return _run_docker(args, timeout=300)


# ============================================================
# Handler Dispatch Map
# ============================================================

TOOL_HANDLERS: Dict[str, Callable] = {
    "docker_ps": tool_docker_ps,
    "docker_logs": tool_docker_logs,
    "docker_exec": tool_docker_exec,
    "docker_images": tool_docker_images,
    "docker_build": tool_docker_build,
    "docker_pull": tool_docker_pull,
}
