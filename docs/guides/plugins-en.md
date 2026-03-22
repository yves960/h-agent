# Plugin System

*"Every rule needs to be broken once."* — Ekko

h-agent's plugin system allows dynamically loading extension modules to add new tools and capabilities to Agents.

---

## 1. Overview

### Plugins vs Skills vs Built-in Tools

| Type | Load Timing | Description |
|------|----------|------|
| Built-in Tools | At startup | Modules under `h_agent/tools/` (Git, Docker, HTTP, etc.) |
| Skills | On-demand | Markdown files, called by `load_skill` tool |
| Plugins | At startup | Python modules, can register tools, handlers, Channels |

### Plugin Structure

```
h_agent/plugins/
├── __init__.py          # Plugin manager
├── web_tools.py         # Built-in Web tools plugin
└── <third-party plugins>/         # User-installed plugins
    ├── __init__.py
    └── ...
```

---

## 2. Installation and Management

### Command Line Management

```bash
# List all plugins
h-agent plugin list

# View plugin details
h-agent plugin info my-plugin

# Enable plugin
h-agent plugin enable my-plugin

# Disable plugin
h-agent plugin disable my-plugin

# Install plugin (from URL or git repo)
h-agent plugin install https://github.com/user/h-agent-myplugin

# Uninstall plugin
h-agent plugin uninstall my-plugin
```

### Plugin List Output Example

```
$ h-agent plugin list
Plugins:
  ✓ web_tools    v1.0.0  - Web scraping and processing tools
  ✓ docker_helper v0.2.0  - Docker extensions
  ✗ custom_auth   v0.1.0  - Custom authentication (disabled)
```

---

## 3. Writing Plugins

### Minimal Plugin Example

```python
# my_plugin/__init__.py
"""
My Custom Plugin - Add custom tools to h-agent
"""

from typing import List, Dict, Any

PLUGIN_NAME = "my_plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Custom plugin example"
PLUGIN_AUTHOR = "Your Name"

# ─── Tool Definitions (OpenAI function calling format) ───

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "my_tool",
            "description": "My custom tool for executing specific tasks",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_text": {
                        "type": "string",
                        "description": "Input text"
                    }
                },
                "required": ["input_text"]
            }
        }
    }
]

# ─── Tool Handlers ───

def my_tool_handler(input_text: str) -> str:
    """Process input text and return result"""
    return f"Result: {input_text.upper()}"

TOOL_HANDLERS = {
    "my_tool": my_tool_handler,
}

# ─── Initialization Functions (optional)───

def on_load():
    """Called when plugin is loaded"""
    print(f"{PLUGIN_NAME} v{PLUGIN_VERSION} loaded!")

def on_unload():
    """Called when plugin is unloaded"""
    print(f"{PLUGIN_NAME} unloaded!")
```

### Register with Plugin System

Plugins are automatically discovered and loaded by `h_agent/plugins/__init__.py`:

```python
from h_agent.plugins import Plugin, _discover_plugins, load_plugin

# Discover plugins in plugins/ directory
plugin_paths = _discover_plugins()
for path in plugin_paths:
    plugin = load_plugin(path)
    print(f"Loaded: {plugin.name}")
```

---

## 4. Plugin Tool Loading Process

```
At startup:
  1. h_agent.core.tools imports h_agent.plugins
  2. plugins/__init__.py executes load_all_plugins()
  3. Iterate enabled plugins in ~/.h-agent/plugins.json
  4. Call get_enabled_tools() to get all plugin tools
  5. Merge into TOOLS list (deduplicate)
  6. Call get_enabled_handlers() to get handlers
  7. Merge into TOOL_HANDLERS dictionary

At runtime:
  - Agent calls tool → execute_tool_call()
  → Look up handler in TOOL_HANDLERS
  → Execute and return result
```

---

## 5. Plugin Configuration

### Plugin State Storage

Plugin enable/disable state is saved in `~/.h-agent/plugins.json`:

```json
{
  "plugins": {
    "web_tools": true,
    "docker_helper": true,
    "custom_auth": false
  }
}
```

### Programmatic Configuration

```python
from h_agent.plugins import (
    get_plugin_state, save_plugin_state,
    enable_plugin, disable_plugin
)

# Get all plugin states
state = get_plugin_state()
print(state)

# Enable plugin
enable_plugin("my_plugin")

# Disable plugin
disable_plugin("my_plugin")

# Save state
save_plugin_state({"web_tools": True, "custom": False})
```

---

## 6. Built-in Plugin: web_tools

`h_agent/plugins/web_tools.py` is a default built-in plugin providing Web-related tools:

### Available Tools

| Tool | Description |
|------|------|
| `web_fetch` | Fetch URL content (extract readable text) |
| `web_search` | Search engine query |

### Usage Example

```python
# Fetch web page content
from h_agent.plugins.web_tools import web_fetch_tool

result = web_fetch_tool(
    url="https://example.com",
    max_chars=5000
)
print(result)

# Web search
from h_agent.plugins.web_tools import web_search_tool

results = web_search_tool(
    query="Python async tutorial",
    count=5
)
print(results)
```

---

## 7. Plugin Publishing and Distribution

### Publish to Plugin Marketplace

Plugins can be published to `h-agent-plugins` repository:

```bash
# Directory structure
h-agent-plugins/
└── index.json    # Plugin index
    ├── my_plugin/
    │   ├── __init__.py
    │   └── README.md
    └── another_plugin/
```

### index.json Format

```json
{
  "plugins": [
    {
      "name": "my_plugin",
      "version": "1.0.0",
      "description": "My custom plugin",
      "author": "Your Name",
      "url": "https://github.com/user/h-agent-my-plugin",
      "tools": ["my_tool"],
      "dependencies": []
    }
  ]
}
```

---

## 8. Notes

- Plugin tool names cannot be the same as built-in tools (same names are ignored)
- Plugin load failure doesn't crash main program, only logs error
- Plugins can register Channel extensions for custom message channels
- Plugin `on_load()` is called when plugin is enabled, `on_unload()` is called when disabled
- Be cautious with third-party plugin sources, only install from trusted sources
