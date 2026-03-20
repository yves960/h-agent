#!/usr/bin/env python3
"""
s01_agent_loop.py - OpenAI Protocol Version

The core agent loop, adapted for OpenAI's chat completions API.

Key differences from Anthropic:
1. Tool calls detected via `message.tool_calls` instead of `stop_reason`
2. Tool results sent as `role="tool"` messages
3. Tool definition uses `parameters` instead of `input_schema`

The pattern remains the same:
    while tool_calls exist:
        response = LLM(messages, tools)
        execute tools
        append results as tool messages
"""

import os
import json
import subprocess
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# 支持 OpenAI 兼容的 API（如智谱、DeepSeek、本地模型等）
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

# OpenAI 格式的工具定义
TOOLS = [{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command. Use for file operations, git, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                }
            },
            "required": ["command"]
        }
    }
}]


def run_bash(command: str) -> str:
    """Execute a shell command with safety checks."""
    # 危险命令黑名单
    dangerous = ["rm -rf /", "sudo rm", "mkfs", "dd if=", "> /dev/sd"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked for safety"
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=os.getcwd(),
            capture_output=True, 
            text=True, 
            timeout=120
        )
        output = (result.stdout + result.stderr).strip()
        # 限制输出长度，避免上下文爆炸
        return output[:50000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (120s limit)"
    except Exception as e:
        return f"Error: {str(e)}"


def execute_tool_call(tool_call) -> str:
    """Execute a single tool call and return the result."""
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    if function_name == "bash":
        return run_bash(arguments["command"])
    else:
        return f"Error: Unknown tool '{function_name}'"


def agent_loop(messages: list):
    """
    The core agent loop.
    
    Keep calling the LLM and executing tools until the model stops.
    """
    while True:
        # 调用 LLM
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=8000,
        )
        
        message = response.choices[0].message
        
        # 将 assistant 回复加入历史
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls,
        })
        
        # 如果没有工具调用，结束循环
        if not message.tool_calls:
            return
        
        # 执行每个工具调用，收集结果
        for tool_call in message.tool_calls:
            print(f"\033[33m$ {json.loads(tool_call.function.arguments).get('command', '')}\033[0m")
            
            # 执行工具
            result = execute_tool_call(tool_call)
            print(result[:200] + ("..." if len(result) > 200 else ""))
            
            # 将工具结果加入消息历史（OpenAI 格式）
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


def main():
    """Interactive REPL for the agent."""
    print(f"\033[36mOpenAI Agent Harness - s01\033[0m")
    print(f"Model: {MODEL}")
    print(f"Working directory: {os.getcwd()}")
    print("Type 'q' or 'exit' to quit, or press Enter\n")
    
    history = []
    
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if query.strip().lower() in ("q", "exit", ""):
            print("Goodbye!")
            break
        
        # 添加用户消息
        history.append({"role": "user", "content": query})
        
        # 运行 agent 循环
        agent_loop(history)
        
        # 打印最终回复
        last_message = history[-1]
        if last_message["role"] == "assistant" and last_message.get("content"):
            print(f"\n{last_message['content']}\n")


if __name__ == "__main__":
    main()