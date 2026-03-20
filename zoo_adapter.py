#!/usr/bin/env python3
"""
zoo_adapter.py - Adapter to integrate OpenAI Agent with Zoo Multi-Agent System

This adapter implements the AnimalService interface, allowing our agent
to work alongside xueqiu, liuliu, and xiaohuang in the zoo system.

Usage in zoo:
    from openai_agent_harness.zoo_adapter import OpenAIAgentService
    
    services = {
        "xueqiu": XueqiuService(),
        "liuliu": LiuliuService(),
        "xiaohuang": XiaohuangService(),
        "openai": OpenAIAgentService(),  # 新增
    }
"""

import os
import json
import asyncio
import subprocess
from typing import Any, Dict, List, Optional, Tuple, AsyncGenerator, Union

# 导入我们的 agent 核心
from s03_todo_write import (
    agent_loop,
    execute_tool_call,
    TOOLS,
    get_system_prompt,
    todo_manager,
)

# Zoo 的接口定义（简化版，避免循环导入）
class AnimalMessage:
    """Represents a message from an animal agent."""
    
    def __init__(
        self,
        animal_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        is_complete: bool = False,
    ):
        self.animal_id = animal_id
        self.content = content
        self.message_type = message_type
        self.metadata = metadata or {}
        self.is_complete = is_complete
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "animal_id": self.animal_id,
            "content": self.content,
            "message_type": self.message_type,
            "metadata": self.metadata,
            "is_complete": self.is_complete,
        }


class AnimalService:
    """Base class for animal services (simplified)."""
    
    def __init__(self, animal_id: str, config: Dict[str, Any] = None):
        self.animal_id = animal_id
        self.config = config or {}
        self.prompt = ""
        self.thread_id = ""
    
    def configure(self, prompt: str, thread_id: str, cli_spawner=None):
        self.prompt = prompt
        self.thread_id = thread_id


class OpenAIAgentService(AnimalService):
    """
    OpenAI Agent adapter for Zoo Multi-Agent System.
    
    This agent uses OpenAI-compatible APIs (智谱, DeepSeek, etc.)
    and implements all the tools from our agent harness.
    """
    
    def __init__(
        self,
        animal_id: str = "openai",
        config: Dict[str, Any] = None,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
    ):
        super().__init__(animal_id, config or {})
        
        # 配置 API
        self.model = model or os.getenv("MODEL_ID", "gpt-4o")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "sk-dummy")
        
        # Agent 信息
        self.name = "OpenAI Agent"
        self.species = "AI Assistant"
        self.color = "#9B59B6"  # 紫色
        self.description = "OpenAI-compatible agent with file tools"
    
    def get_animal_info(self) -> Dict[str, Any]:
        """返回 agent 信息，用于 /api/animals 端点"""
        return {
            "name": self.name,
            "species": self.species,
            "cli": "openai-agent",
            "color": self.color,
            "description": self.description,
            "tools": ["bash", "read", "write", "edit", "glob", "TodoWrite"],
        }
    
    def get_cli_command(self) -> Tuple[str, List[str]]:
        """
        返回 CLI 命令（用于进程模式）。
        
        由于我们的 agent 是纯 Python 实现，
        这里返回一个可以直接运行的 Python 脚本。
        """
        return (
            "python3",
            ["-m", "openai_agent_harness.zoo_adapter", "--mode", "cli"]
        )
    
    async def invoke(
        self,
        prompt: str,
        thread_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncGenerator[AnimalMessage, None]:
        """
        调用 agent 处理 prompt，异步生成消息。
        
        这是 Zoo 多 agent 系统的核心接口。
        """
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        while True:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": get_system_prompt()}] + messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=8000,
                )
                
                message = response.choices[0].message
                
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                })
                
                # 如果没有工具调用，返回最终结果
                if not message.tool_calls:
                    yield AnimalMessage(
                        animal_id=self.animal_id,
                        content=message.content or "",
                        message_type="text",
                        is_complete=True,
                    )
                    return
                
                # 执行工具调用
                for tool_call in message.tool_calls:
                    result = execute_tool_call(tool_call)
                    
                    # 发送工具执行信息
                    yield AnimalMessage(
                        animal_id=self.animal_id,
                        content=f"[{tool_call.function.name}] {result[:200]}",
                        message_type="tool_use",
                        is_complete=False,
                    )
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                    
            except Exception as e:
                yield AnimalMessage(
                    animal_id=self.animal_id,
                    content=f"Error: {str(e)}",
                    message_type="error",
                    is_complete=True,
                )
                return
    
    def transform_event(
        self, event: Union[str, Dict[str, Any]]
    ) -> Optional[AnimalMessage]:
        """
        转换事件到消息（用于 CLI 模式）。
        
        由于我们直接在 Python 中运行，这个方法主要用于
        处理外部 CLI 调用时的输出解析。
        """
        if isinstance(event, str):
            return AnimalMessage(
                animal_id=self.animal_id,
                content=event,
                message_type="text",
            )
        elif isinstance(event, dict):
            return AnimalMessage(
                animal_id=self.animal_id,
                content=event.get("content", ""),
                message_type=event.get("type", "text"),
                metadata=event.get("metadata"),
            )
        return None


# ============================================================
# CLI Mode (for standalone execution)
# ============================================================

def cli_mode():
    """独立 CLI 模式，用于测试或进程外调用。"""
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print(f"OpenAI Agent (Zoo Adapter)")
    print(f"Model: {os.getenv('MODEL_ID', 'gpt-4o')}")
    print("-" * 40)
    
    service = OpenAIAgentService()
    
    # 从 stdin 读取 prompt
    if len(sys.argv) > 1 and sys.argv[1] != "--mode":
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = sys.stdin.read().strip()
    
    if not prompt:
        print("Usage: python zoo_adapter.py <prompt>")
        print("       echo 'prompt' | python zoo_adapter.py")
        return
    
    # 异步运行
    async def run():
        async for msg in service.invoke(prompt, "cli-session"):
            print(msg.content)
            if msg.is_complete:
                break
    
    asyncio.run(run())


if __name__ == "__main__":
    cli_mode()