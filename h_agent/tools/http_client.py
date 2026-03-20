"""
h_agent/tools/http_.py - HTTP Client Tool

Provides HTTP GET and POST tools.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Optional

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "http_get",
            "description": "Send an HTTP GET request and return the response body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "headers": {"type": "object", "description": "Optional HTTP headers as JSON string", "default": "{}"},
                    "timeout": {"type": "integer", "description": "Request timeout in seconds", "default": 10}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "http_post",
            "description": "Send an HTTP POST request and return the response body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to post to"},
                    "data": {"type": "string", "description": "Request body content", "default": ""},
                    "content_type": {"type": "string", "description": "Content-Type header", "default": "application/json"},
                    "headers": {"type": "object", "description": "Optional HTTP headers as JSON string", "default": "{}"},
                    "timeout": {"type": "integer", "description": "Request timeout in seconds", "default": 10}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "http_head",
            "description": "Send an HTTP HEAD request and return response headers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "headers": {"type": "object", "description": "Optional HTTP headers as JSON string", "default": "{}"}
                },
                "required": ["url"]
            }
        }
    }
]

TOOL_HANDLERS = {}


def tool_http_get(url: str, headers: str = "{}", timeout: int = 10) -> str:
    """Send HTTP GET request."""
    try:
        h = json.loads(headers) if isinstance(headers, str) else headers
        h["User-Agent"] = h.get("User-Agent", "h-agent/1.0")

        req = urllib.request.Request(url, headers=h, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read(100000).decode("utf-8", errors="replace")
            hdrs = {k: v for k, v in resp.headers.items()}
            return f"Status: {status}\nHeaders: {json.dumps(hdrs, indent=2)}\n\nBody:\n{body}"
    except urllib.error.HTTPError as e:
        body = e.read(5000).decode("utf-8", errors="replace")
        return f"HTTP {e.code} {e.reason}\n\n{body}"
    except urllib.error.URLError as e:
        return f"Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"


def tool_http_post(url: str, data: str = "", content_type: str = "application/json",
                   headers: str = "{}", timeout: int = 10) -> str:
    """Send HTTP POST request."""
    try:
        h = json.loads(headers) if isinstance(headers, str) else headers
        h["User-Agent"] = h.get("User-Agent", "h-agent/1.0")
        h["Content-Type"] = content_type

        body_bytes = data.encode("utf-8") if data else b""
        req = urllib.request.Request(url, data=body_bytes, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read(100000).decode("utf-8", errors="replace")
            hdrs = {k: v for k, v in resp.headers.items()}
            return f"Status: {status}\nHeaders: {json.dumps(hdrs, indent=2)}\n\nBody:\n{body}"
    except urllib.error.HTTPError as e:
        body = e.read(5000).decode("utf-8", errors="replace")
        return f"HTTP {e.code} {e.reason}\n\n{body}"
    except urllib.error.URLError as e:
        return f"Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"


def tool_http_head(url: str, headers: str = "{}") -> str:
    """Send HTTP HEAD request."""
    try:
        h = json.loads(headers) if isinstance(headers, str) else headers
        h["User-Agent"] = h.get("User-Agent", "h-agent/1.0")

        req = urllib.request.Request(url, headers=h, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            hdrs = {k: v for k, v in resp.headers.items()}
            return f"Status: {resp.status}\n\nHeaders:\n{json.dumps(hdrs, indent=2)}"
    except urllib.error.HTTPError as e:
        hdrs = {k: v for k, v in e.headers.items()}
        return f"HTTP {e.code} {e.reason}\n\nHeaders:\n{json.dumps(hdrs, indent=2)}"
    except urllib.error.URLError as e:
        return f"Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"


TOOL_HANDLERS = {
    "http_get": tool_http_get,
    "http_post": tool_http_post,
    "http_head": tool_http_head,
}
