#!/usr/bin/env python3
"""
Test script for h-agent restructured tools and engine.
Tests the core functionality after Phase 1 refactor.
"""

import asyncio
import tempfile
import os
from pathlib import Path

from h_agent.tools.registry import get_registry, ToolRegistry
from h_agent.tools.base import ToolResult
from h_agent.core.engine import QueryEngine


async def test_tool_registry():
    """Test the tool registry functionality."""
    print("=== Testing Tool Registry ===")
    
    # Get the global registry
    registry = get_registry()
    
    # List available tools
    tools = registry.list_tools()
    print(f"Available tools: {tools}")
    
    # Check for expected tools
    expected_tools = {"bash", "read", "write", "edit"}
    available_tools = set(tools)
    missing_tools = expected_tools - available_tools
    extra_tools = available_tools - expected_tools
    
    if missing_tools:
        print(f"❌ Missing expected tools: {missing_tools}")
    else:
        print("✅ All expected tools present")
    
    if extra_tools:
        print(f"ℹ️ Additional tools: {extra_tools}")
    
    # Test getting individual tools
    for tool_name in expected_tools.intersection(available_tools):
        tool = registry.get(tool_name)
        if tool:
            print(f"✅ Found tool '{tool_name}': {tool.description}")
        else:
            print(f"❌ Could not get tool '{tool_name}'")
    
    return len(missing_tools) == 0


async def test_bash_tool():
    """Test the bash tool functionality."""
    print("\n=== Testing Bash Tool ===")
    
    registry = get_registry()
    bash_tool = registry.get("bash")
    
    if not bash_tool:
        print("❌ Bash tool not found")
        return False
    
    # Test a simple command
    result = await bash_tool.execute({"command": "echo 'Hello, World!'"})
    print(f"Bash echo result: success={result.success}, output='{result.output[:50]}{'...' if len(result.output) > 50 else ''}'")
    
    if result.success and "Hello, World!" in result.output:
        print("✅ Bash tool basic command works")
    else:
        print("❌ Bash tool basic command failed")
        return False
    
    # Test dangerous command blocking
    dangerous_commands = [
        "rm -rf /",
        "sudo rm -rf /",
        ":(){ :|:& };:",
    ]
    
    for cmd in dangerous_commands:
        result = await bash_tool.execute({"command": cmd})
        if not result.success and "blocked" in result.error.lower():
            print(f"✅ Dangerous command '{cmd[:20]}...' correctly blocked")
        else:
            print(f"❌ Dangerous command '{cmd[:20]}...' was not blocked")
            return False
    
    return True


async def test_file_operations():
    """Test file read/write/edit tools."""
    print("\n=== Testing File Operations ===")
    
    registry = get_registry()
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write("Original content\nSecond line\nThird line\n")
        temp_file = tmp.name
    
    try:
        # Test read tool
        read_tool = registry.get("read")
        if not read_tool:
            print("❌ Read tool not found")
            return False
        
        result = await read_tool.execute({"path": temp_file})
        if result.success and "Original content" in result.output:
            print("✅ Read tool works")
        else:
            print(f"❌ Read tool failed: {result.error}")
            return False
        
        # Test write tool
        write_tool = registry.get("write")
        if not write_tool:
            print("❌ Write tool not found")
            return False
        
        new_content = "New file content\nModified line\nThird line\n"
        result = await write_tool.execute({
            "path": temp_file,
            "content": new_content
        })
        
        if result.success:
            print("✅ Write tool works")
        else:
            print(f"❌ Write tool failed: {result.error}")
            return False
        
        # Verify written content
        result = await read_tool.execute({"path": temp_file})
        if result.success and "New file content" in result.output:
            print("✅ Write operation verified")
        else:
            print("❌ Written content verification failed")
            return False
        
        # Test edit tool
        edit_tool = registry.get("edit")
        if not edit_tool:
            print("❌ Edit tool not found")
            return False
        
        # Replace "Second line" with "Modified line"
        result = await edit_tool.execute({
            "path": temp_file,
            "old_text": "New file content\nModified line\n",
            "new_text": "New file content\nCompletely new line\n",
        })
        
        if result.success:
            print("✅ Edit tool works")
        else:
            print(f"❌ Edit tool failed: {result.error}")
            return False
        
        # Verify edit
        result = await read_tool.execute({"path": temp_file})
        if result.success and "Completely new line" in result.output:
            print("✅ Edit operation verified")
        else:
            print("❌ Edit operation verification failed")
            return False
            
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    return True


async def test_token_counting():
    """Test the token counting functionality."""
    print("\n=== Testing Token Counting ===")
    
    from h_agent.core.engine import TokenCounter
    
    try:
        counter = TokenCounter()
        
        # Test simple text
        text = "Hello world, this is a test."
        token_count = counter.count_text(text)
        print(f"Token count for '{text[:20]}...': {token_count}")
        
        # Test messages
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        msg_token_count = counter.count_messages(messages)
        print(f"Token count for messages: {msg_token_count}")
        
        print("✅ Token counting works")
        return True
        
    except Exception as e:
        print(f"❌ Token counting failed: {e}")
        return False


async def test_query_engine():
    """Test the query engine (without actual API call)."""
    print("\n=== Testing Query Engine ===")
    
    try:
        # Create engine
        engine = QueryEngine(max_tokens=100, timeout=10)
        
        # Test token counter
        counter = engine.token_counter
        text = "Test message for token counting"
        tokens = counter.count_text(text)
        print(f"Engine token count: {tokens}")
        
        # Test usage tracking
        usage = engine.get_usage()
        print(f"Initial usage: {usage.total_tokens} tokens")
        
        print("✅ Query engine initialization works")
        return True
        
    except Exception as e:
        print(f"❌ Query engine test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Testing h-agent Phase 1 Refactor\n")
    
    results = []
    
    results.append(await test_tool_registry())
    results.append(await test_bash_tool())
    results.append(await test_file_operations())
    results.append(await test_token_counting())
    results.append(await test_query_engine())
    
    print(f"\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)