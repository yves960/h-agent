"""
h_agent/plugins/web_tools.py - Web Plugin (fetch & search)

Built-in plugin providing web fetch and search tools.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any

PLUGIN_NAME = "web_tools"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Web fetch and search tools"
PLUGIN_AUTHOR = "h-agent"

# ============================================================
# Tool Definitions
# ============================================================

PLUGIN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and extract readable content from a URL (HTML → text). Use for lightweight page access without browser automation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "HTTP or HTTPS URL to fetch."},
                    "max_chars": {"type": "integer", "description": "Maximum characters to return (truncates when exceeded).", "default": 50000}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using Brave Search API. Returns titles, URLs, and snippets for fast research.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string."},
                    "count": {"type": "integer", "description": "Number of results to return (1-10).", "default": 5},
                    "freshness": {"type": "string", "description": "Filter by time: 'day', 'week', 'month', or 'year'.", "default": None}
                },
                "required": ["query"]
            }
        }
    }
]


# ============================================================
# Tool Handlers
# ============================================================

def _fetch_url(url: str, max_chars: int = 50000) -> str:
    """Fetch URL content with timeout."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; h-agent/1.0)",
                "Accept": "text/html,application/xhtml+xml,*/*",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type and "application/json" not in content_type:
                return f"Content-Type {content_type} not supported. URL: {url}"

            raw = resp.read(max_chars + 10000)
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = raw.decode("latin-1", errors="replace")

            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[... content truncated ...]"

            return text

    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"


def _extract_text_from_html(html: str, max_chars: int) -> str:
    """Simple HTML to plain text extraction."""
    import re
    # Remove scripts and styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... content truncated ...]"
    return text


def tool_web_fetch(url: str, max_chars: int = 50000) -> str:
    """Fetch and extract readable content from URL."""
    raw = _fetch_url(url, max_chars + 5000)
    if raw.startswith("Error") or raw.startswith("HTTP") or raw.startswith("URL"):
        return raw
    return _extract_text_from_html(raw, max_chars)


def tool_web_search(query: str, count: int = 5, freshness: str = None) -> str:
    """Search the web using Brave Search."""
    import os

    api_key = os.getenv("BRAVE_API_KEY") or os.getenv("SEARCH_API_KEY")
    if not api_key:
        return "Error: Brave Search API key not found. Set BRAVE_API_KEY or SEARCH_API_KEY in your .env file."

    params = {
        "q": query,
        "count": min(count, 10),
        "safesearch": "moderate",
    }
    if freshness:
        freshness_map = {"day": "pd", "week": "pw", "month": "pm", "year": "py"}
        if freshness in freshness_map:
            params["freshness"] = freshness_map[freshness]

    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
        "User-Agent": "h-agent/1.0",
    })

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            results = data.get("web", {}).get("results", [])
            if not results:
                return "No results found."

            output = []
            for i, r in enumerate(results[:count], 1):
                title = r.get("title", "")
                url_r = r.get("url", "")
                snippet = r.get("description", "")
                output.append(f"{i}. {title}\n   {url_r}\n   {snippet}\n")

            return "\n".join(output)
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}"
    except Exception as e:
        return f"Error: {e}"


PLUGIN_HANDLERS = {
    "web_fetch": tool_web_fetch,
    "web_search": tool_web_search,
}
