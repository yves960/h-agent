"""
h_agent/tools - Built-in tool modules

This package contains modular tool definitions:
- git: Git operations (status, commit, push, pull, log, branch)
- file_ops: File operations (read, write, edit, glob)
- shell: Shell command execution
- docker: Docker operations (ps, logs, exec, images)
- http_client: HTTP GET/POST/HEAD requests
- json_utils: JSON parse/format/query tools
"""

from .git import TOOLS as GIT_TOOLS, TOOL_HANDLERS as GIT_HANDLERS
from .file_ops import TOOLS as FILE_TOOLS, TOOL_HANDLERS as FILE_HANDLERS
from .shell import TOOLS as SHELL_TOOLS, TOOL_HANDLERS as SHELL_HANDLERS
from .docker import TOOLS as DOCKER_TOOLS, TOOL_HANDLERS as DOCKER_HANDLERS
from .http_client import TOOLS as HTTP_TOOLS, TOOL_HANDLERS as HTTP_HANDLERS
from .json_utils import TOOLS as JSON_TOOLS, TOOL_HANDLERS as JSON_HANDLERS

# Combined tools and handlers for all built-in tools
ALL_TOOLS = GIT_TOOLS + FILE_TOOLS + SHELL_TOOLS + DOCKER_TOOLS + HTTP_TOOLS + JSON_TOOLS
ALL_HANDLERS = {
    **GIT_HANDLERS,
    **FILE_HANDLERS,
    **SHELL_HANDLERS,
    **DOCKER_HANDLERS,
    **HTTP_HANDLERS,
    **JSON_HANDLERS,
}
