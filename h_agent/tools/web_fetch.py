"""
h_agent/tools/web_fetch.py - Web Fetch Tool

Fetch content from a URL with HTML parsing.
"""

import asyncio
import re
from typing import Optional

from h_agent.tools.base import Tool, ToolResult

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class WebFetchTool(Tool):
    """Fetch content from a URL and extract readable text."""
    
    name = "web_fetch"
    description = "Fetch a web page and extract its text content. Good for reading documentation, articles, or any public webpage."
    concurrency_safe = True
    read_only = True
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch"
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to return (default: 10000)"
                }
            },
            "required": ["url"]
        }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        url = args["url"]
        max_chars = args.get("max_chars", 10000)
        
        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            return ToolResult.err("URL must start with http:// or https://")
        
        # Block dangerous URLs
        blocked = ["localhost", "127.0.0.1", "0.0.0.0", "file://", "ftp://"]
        for blocked_prefix in blocked:
            if url.lower().startswith(blocked_prefix):
                return ToolResult.err(f"URL scheme not allowed: {url}")
        
        if not HAS_AIOHTTP:
            # Fallback to urllib if aiohttp not available
            return await self._fetch_urllib(url, max_chars)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        return ToolResult.err(f"HTTP {response.status}: {response.reason}")
                    
                    content = await response.text()
                    
                    # Extract readable text
                    text = self._extract_text(content, max_chars)
                    
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" in content_type:
                        return ToolResult.ok(f"[Fetched from {url}]\n\n{text}")
                    else:
                        return ToolResult.ok(f"[Fetched from {url}]\n\n{text}")
        
        except asyncio.TimeoutError:
            return ToolResult.err("Request timed out after 15 seconds")
        except aiohttp.ClientError as e:
            return ToolResult.err(f"Request failed: {e}")
    
    async def _fetch_urllib(self, url: str, max_chars: int) -> ToolResult:
        """Fallback using urllib when aiohttp is not available."""
        import urllib.request
        
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                content = response.read().decode("utf-8", errors="replace")
                text = self._extract_text(content, max_chars)
                return ToolResult.ok(f"[Fetched from {url}]\n\n{text}")
        except Exception as e:
            return ToolResult.err(f"Fetch failed: {e}")
    
    def _extract_text(self, html: str, max_chars: int) -> str:
        """Extract readable text from HTML."""
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        
        # Truncate
        text = text.strip()
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        return text
