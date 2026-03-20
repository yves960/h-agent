"""
h_agent/tools/json_utils.py - JSON Manipulation Tools

Provides JSON parse, format, query, and validate tools.
"""

import json
from typing import Any

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "json_parse",
            "description": "Parse a JSON string and return structured data. Useful for extracting values from JSON text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "JSON string to parse"},
                    "pretty": {"type": "boolean", "description": "Format output with indentation", "default": False}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "json_format",
            "description": "Format and pretty-print a JSON string with indentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "JSON string to format"},
                    "indent": {"type": "integer", "description": "Indentation level", "default": 2}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "json_query",
            "description": "Query a JSON string using a dot-path (e.g., 'data.items[0].name') and return the value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "JSON string to query"},
                    "path": {"type": "string", "description": "Dot-path query (e.g., 'result.data[0].name')"}
                },
                "required": ["text", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "json_validate",
            "description": "Validate if a string is valid JSON and return metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "String to validate as JSON"}
                },
                "required": ["text"]
            }
        }
    }
]

TOOL_HANDLERS = {}


def _get_nested(data: Any, path: str) -> Any:
    """Navigate nested dict/list using dot-path like 'a.b[0].c'."""
    import re
    parts = re.split(r'\.(?!\d)|\[[\'"]?|[\'"]?\]', path)
    for part in parts:
        if not part:
            continue
        if isinstance(data, dict):
            data = data.get(part, None)
        elif isinstance(data, list):
            try:
                idx = int(part)
                data = data[idx] if 0 <= idx < len(data) else None
            except (ValueError, TypeError):
                return None
        else:
            return None
        if data is None:
            return None
    return data


def tool_json_parse(text: str, pretty: bool = False) -> str:
    """Parse JSON string."""
    try:
        data = json.loads(text)
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"JSON Parse Error at line {e.lineno}, col {e.colno}: {e.msg}\nPosition: {e.pos}\nText: {text[max(0,e.pos-20):e.pos+20]}"


def tool_json_format(text: str, indent: int = 2) -> str:
    """Format and pretty-print JSON."""
    try:
        data = json.loads(text)
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"JSON Parse Error: {e.msg}"


def tool_json_query(text: str, path: str) -> str:
    """Query JSON using dot-path."""
    try:
        data = json.loads(text)
        result = _get_nested(data, path)
        if result is None:
            return f"Path '{path}' not found or returned None"
        return json.dumps(result, indent=2, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"JSON Parse Error: {e.msg}"


def tool_json_validate(text: str) -> str:
    """Validate JSON and return metadata."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            kind = "object"
            keys = list(data.keys())
        elif isinstance(data, list):
            kind = "array"
            keys = [f"[{i}]" for i in range(min(len(data), 10))]
            if len(data) > 10:
                keys.append(f"... ({len(data)} items total)")
        else:
            kind = type(data).__name__
            keys = []
        return f"✅ Valid JSON\nType: {kind}\nKeys/Indices: {', '.join(str(k) for k in keys[:10])}"
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON\nError: {e.msg}\nLine {e.lineno}, Col {e.colno}"


TOOL_HANDLERS = {
    "json_parse": tool_json_parse,
    "json_format": tool_json_format,
    "json_query": tool_json_query,
    "json_validate": tool_json_validate,
}
