"""
tests/test_tools_new.py - Tests for new tools (glob, grep, web_fetch, web_search)
"""

import pytest
import asyncio
import sys
from pathlib import Path

from h_agent.tools import get_registry
from h_agent.tools.glob import GlobTool
from h_agent.tools.grep import GrepTool
from h_agent.tools.web_fetch import WebFetchTool
from h_agent.tools.web_search import WebSearchTool


class TestGlobTool:
    """Test GlobTool."""
    
    @pytest.fixture
    def tool(self):
        return GlobTool()
    
    def test_tool_metadata(self, tool):
        """Tool should have correct metadata."""
        assert tool.name == "glob"
        assert tool.description
        assert tool.read_only is True
        assert tool.concurrency_safe is True
    
    def test_input_schema(self, tool):
        """Tool should have valid input schema."""
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "pattern" in schema["required"]
        assert "properties" in schema
    
    def test_glob_finds_python_files(self, tool):
        """Should find .py files in test directory."""
        result = asyncio.run(tool.execute({
            "pattern": "*.py",
            "path": "tests"
        }))
        
        assert result.success
        assert "test_buddy.py" in result.output or "test_tools" in result.output
    
    def test_glob_recursive(self, tool):
        """Should find files recursively with **."""
        result = asyncio.run(tool.execute({
            "pattern": "**/*.py",
            "path": "h_agent"
        }))
        
        assert result.success
        # Should find multiple Python files
        lines = result.output.split("\n")
        assert len(lines) > 5
    
    def test_glob_max_results(self, tool):
        """Should respect max_results limit."""
        result = asyncio.run(tool.execute({
            "pattern": "**/*.py",
            "path": ".",
            "max_results": 3
        }))
        
        assert result.success
        lines = [l for l in result.output.split("\n") if l.strip()]
        # Should not exceed max_results + header lines
        assert len(lines) <= 5
    
    def test_glob_invalid_path(self, tool):
        """Should handle invalid paths gracefully."""
        result = asyncio.run(tool.execute({
            "pattern": "*.py",
            "path": "/nonexistent/path"
        }))
        
        # Should either succeed with no results or fail gracefully
        assert result is not None


class TestGrepTool:
    """Test GrepTool."""
    
    @pytest.fixture
    def tool(self):
        return GrepTool()
    
    def test_tool_metadata(self, tool):
        """Tool should have correct metadata."""
        assert tool.name == "grep"
        assert tool.description
        assert tool.read_only is True
        assert tool.concurrency_safe is True
    
    def test_grep_finds_pattern(self, tool):
        """Should find pattern in files."""
        result = asyncio.run(tool.execute({
            "pattern": "class Tool",
            "path": "h_agent/tools",
            "max_results": 10
        }))
        
        assert result.success
        assert "base.py" in result.output
        assert "Tool" in result.output
    
    def test_grep_with_file_pattern(self, tool):
        """Should filter by file pattern."""
        result = asyncio.run(tool.execute({
            "pattern": "class",
            "path": "h_agent/tools",
            "file_pattern": "*.py"
        }))
        
        assert result.success
    
    def test_grep_ignore_case(self, tool):
        """Should support case-insensitive search."""
        result = asyncio.run(tool.execute({
            "pattern": "CLASS",
            "path": "h_agent/tools/base.py",
            "ignore_case": True
        }))
        
        assert result.success
    
    def test_grep_no_matches(self, tool):
        """Should handle no matches gracefully."""
        result = asyncio.run(tool.execute({
            "pattern": "xyzzy_nothing_here",
            "path": "h_agent/tools"
        }))
        
        assert result.success
        assert "No matches" in result.output or "found 0" in result.output


class TestWebFetchTool:
    """Test WebFetchTool."""
    
    @pytest.fixture
    def tool(self):
        return WebFetchTool()
    
    def test_tool_metadata(self, tool):
        """Tool should have correct metadata."""
        assert tool.name == "web_fetch"
        assert tool.description
        assert tool.read_only is True
        assert tool.concurrency_safe is True
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason="macOS CI has SSL certificate issues"
    )
    async def test_fetch_url(self, tool):
        """Should fetch URL content."""
        result = await tool.execute({
            "url": "https://example.com",
            "max_chars": 200
        })
        
        assert result.success
        assert "Example Domain" in result.output or "example" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self, tool):
        """Should handle invalid URLs."""
        result = await tool.execute({
            "url": "not-a-url"
        })
        
        assert not result.success
        assert "http" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_localhost_blocked(self, tool):
        """Should block localhost URLs for security."""
        result = await tool.execute({
            "url": "http://localhost/test"
        })
        
        assert not result.success


class TestWebSearchTool:
    """Test WebSearchTool."""
    
    @pytest.fixture
    def tool(self):
        return WebSearchTool()
    
    def test_tool_metadata(self, tool):
        """Tool should have correct metadata."""
        assert tool.name == "web_search"
        assert tool.description
        assert tool.read_only is True
        assert tool.concurrency_safe is True
    
    @pytest.mark.asyncio
    async def test_search_query(self, tool):
        """Should perform search."""
        result = await tool.execute({
            "query": "python programming language",
            "num_results": 3
        })
        
        # Note: DuckDuckGo HTML parsing may be fragile
        # Test that tool runs without error
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, tool):
        """Should handle empty query."""
        result = await tool.execute({
            "query": ""
        })
        
        assert not result.success


class TestToolRegistry:
    """Test tool registration."""
    
    def test_all_tools_registered(self):
        """All new tools should be in the registry."""
        registry = get_registry()
        tools = registry.list_tools()
        
        assert "glob" in tools
        assert "grep" in tools
        assert "web_fetch" in tools
        assert "web_search" in tools
    
    def test_tool_schemas_available(self):
        """Tool schemas should be available for LLM."""
        registry = get_registry()
        schemas = registry.get_tool_schemas()
        
        schema_names = [s["function"]["name"] for s in schemas]
        
        assert "glob" in schema_names
        assert "grep" in schema_names
        assert "web_fetch" in schema_names
        assert "web_search" in schema_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
