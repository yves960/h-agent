"""
h_agent/tools/web_search.py - Web Search Tool

Search the web using DuckDuckGo.
"""

import re
import asyncio
import urllib.parse
from typing import Optional

from h_agent.tools.base import Tool, ToolResult

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class WebSearchTool(Tool):
    """Search the web using DuckDuckGo."""
    
    name = "web_search"
    description = "Search the web using DuckDuckGo. Returns titles, URLs, and snippets."
    concurrency_safe = True
    read_only = True
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 10)"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        query = args["query"]
        num_results = min(args.get("num_results", 5), 10)
        
        if not query or not query.strip():
            return ToolResult.err("Query cannot be empty")
        
        if HAS_AIOHTTP:
            return await self._search_aiohttp(query, num_results)
        else:
            return await self._search_urllib(query, num_results)
    
    async def _search_aiohttp(self, query: str, num_results: int) -> ToolResult:
        """Search using aiohttp with DuckDuckGo HTML."""
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url, 
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers={"User-Agent": "Mozilla/5.0"}
                ) as response:
                    if response.status != 200:
                        return ToolResult.err(f"Search failed: HTTP {response.status}")
                    
                    html = await response.text()
                    results = self._parse_results(html, num_results)
                    
                    if not results:
                        return ToolResult.ok(f"No results found for: {query}")
                    
                    lines = [f"Search results for: {query}\n"]
                    for i, (title, url, snippet) in enumerate(results, 1):
                        lines.append(f"{i}. {title}")
                        lines.append(f"   URL: {url}")
                        if snippet:
                            lines.append(f"   {snippet}")
                        lines.append("")
                    
                    return ToolResult.ok("\n".join(lines))
        
        except asyncio.TimeoutError:
            return ToolResult.err("Search timed out after 15 seconds")
        except aiohttp.ClientError as e:
            return ToolResult.err(f"Search failed: {e}")
    
    async def _search_urllib(self, query: str, num_results: int) -> ToolResult:
        """Fallback search using urllib."""
        import urllib.request
        
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode("utf-8", errors="replace")
                results = self._parse_results(html, num_results)
                
                if not results:
                    return ToolResult.ok(f"No results found for: {query}")
                
                lines = [f"Search results for: {query}\n"]
                for i, (title, url, snippet) in enumerate(results, 1):
                    lines.append(f"{i}. {title}")
                    lines.append(f"   URL: {url}")
                    if snippet:
                        lines.append(f"   {snippet}")
                    lines.append("")
                
                return ToolResult.ok("\n".join(lines))
        
        except Exception as e:
            return ToolResult.err(f"Search failed: {e}")
    
    def _parse_results(self, html: str, num_results: int) -> list:
        """Parse DuckDuckGo HTML results."""
        results = []
        
        # Pattern for result blocks
        result_pattern = re.compile(
            r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
        )
        
        # Pattern for snippets
        snippet_pattern = re.compile(
            r'<a class="result__snippet"[^>]*>([^<]+)</a>'
        )
        
        # Find all result links
        links = result_pattern.findall(html)
        snippets = snippet_pattern.findall(html)
        
        for i, (url, title) in enumerate(links[:num_results]):
            # Clean title
            title = re.sub(r'<[^>]+>', '', title)
            title = title.strip()
            
            # Clean snippet
            snippet = ""
            if i < len(snippets):
                snippet = re.sub(r'<[^>]+>', '', snippets[i])
                snippet = snippet.strip()
            
            results.append((title, url, snippet))
        
        return results
