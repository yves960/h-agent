#!/usr/bin/env python3
"""
c05_gateway_routing.py - Gateway & Routing (OpenAI Version)

每条消息都能找到归宿。
Gateway 是消息枢纽，路由系统是五层绑定表。

路由层级:
  1. peer_id    - 特定用户
  2. guild_id   - 服务器/群组
  3. account_id - Bot账号
  4. channel    - 整个通道
  5. default    - 兜底
"""

import os
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORKSPACE_DIR = Path.cwd() / ".agent_workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 路由绑定
# ============================================================

@dataclass
class Binding:
    """路由绑定规则。"""
    agent_id: str
    tier: int  # 1-5, 越小越具体
    match_key: str  # "peer_id" | "guild_id" | "account_id" | "channel" | "default"
    match_value: str
    priority: int = 0
    
    def matches(self, context: dict) -> bool:
        """检查是否匹配上下文。"""
        if self.match_key == "default":
            return True
        value = context.get(self.match_key, "")
        return value == self.match_value or self.match_value == "*"


class BindingTable:
    """五层绑定表。"""
    
    def __init__(self):
        self._bindings: List[Binding] = []
    
    def add(self, binding: Binding) -> None:
        self._bindings.append(binding)
        self._bindings.sort(key=lambda b: (b.tier, -b.priority))
    
    def remove(self, agent_id: str, match_key: str, match_value: str) -> bool:
        before = len(self._bindings)
        self._bindings = [
            b for b in self._bindings
            if not (b.agent_id == agent_id and b.match_key == match_key and b.match_value == match_value)
        ]
        return len(self._bindings) < before
    
    def resolve(self, channel: str = "", account_id: str = "", 
                guild_id: str = "", peer_id: str = "") -> Optional[str]:
        """解析路由，返回 agent_id。"""
        context = {
            "peer_id": peer_id,
            "guild_id": guild_id,
            "account_id": account_id,
            "channel": channel,
        }
        
        for binding in self._bindings:
            if binding.matches(context):
                return binding.agent_id
        
        return "default"
    
    def list_all(self) -> List[Binding]:
        return list(self._bindings)


# ============================================================
# Gateway
# ============================================================

@dataclass
class InboundMessage:
    """入站消息。"""
    text: str
    sender_id: str
    channel: str = ""
    account_id: str = ""
    peer_id: str = ""
    guild_id: str = ""
    is_group: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class RoutedMessage:
    """路由后的消息。"""
    agent_id: str
    session_key: str
    inbound: InboundMessage


class Gateway:
    """消息网关。"""
    
    def __init__(self):
        self.binding_table = BindingTable()
        self._agent_handlers: Dict[str, Any] = {}
    
    def register_agent(self, agent_id: str, handler: Any):
        """注册 Agent 处理器。"""
        self._agent_handlers[agent_id] = handler
    
    def add_binding(self, agent_id: str, tier: int, match_key: str, 
                    match_value: str, priority: int = 0):
        """添加路由绑定。"""
        self.binding_table.add(Binding(
            agent_id=agent_id,
            tier=tier,
            match_key=match_key,
            match_value=match_value,
            priority=priority,
        ))
    
    def route(self, inbound: InboundMessage) -> RoutedMessage:
        """路由消息到对应的 Agent。"""
        agent_id = self.binding_table.resolve(
            channel=inbound.channel,
            account_id=inbound.account_id,
            guild_id=inbound.guild_id,
            peer_id=inbound.peer_id,
        )
        
        # 构建 session_key
        parts = [inbound.channel, inbound.account_id]
        if inbound.guild_id:
            parts.append(inbound.guild_id)
        if inbound.peer_id:
            parts.append(inbound.peer_id)
        session_key = ":".join(parts)
        
        return RoutedMessage(
            agent_id=agent_id,
            session_key=session_key,
            inbound=inbound,
        )
    
    def dispatch(self, routed: RoutedMessage) -> str:
        """分发消息到 Agent。"""
        agent_id = routed.agent_id
        if agent_id in self._agent_handlers:
            handler = self._agent_handlers[agent_id]
            return handler(routed)
        return f"No handler for agent: {agent_id}"


# ============================================================
# Agent Manager
# ============================================================

class AgentManager:
    """管理多个 Agent 实例。"""
    
    def __init__(self):
        self.agents: Dict[str, dict] = {}
        self._sessions: Dict[str, List[dict]] = {}
    
    def register(self, agent_id: str, config: dict = None):
        """注册 Agent。"""
        self.agents[agent_id] = config or {}
    
    def get_session(self, session_key: str) -> List[dict]:
        """获取会话。"""
        if session_key not in self._sessions:
            self._sessions[session_key] = []
        return self._sessions[session_key]
    
    def process(self, routed: RoutedMessage) -> str:
        """处理路由后的消息。"""
        agent_id = routed.agent_id
        session_key = routed.session_key
        
        # 获取会话历史
        messages = self.get_session(session_key)
        messages.append({"role": "user", "content": routed.inbound.text})
        
        # 获取 Agent 配置
        config = self.agents.get(agent_id, {})
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        
        # 调用 LLM
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system_prompt}] + messages[-20:],
                max_tokens=2048,
            )
            reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"Error: {e}"


# ============================================================
# Main
# ============================================================

def main():
    print(f"\033[36mOpenAI Agent Harness - c05 (Gateway Routing)\033[0m")
    print(f"Model: {MODEL}")
    
    # 创建 Gateway 和 AgentManager
    gateway = Gateway()
    agent_manager = AgentManager()
    
    # 注册 Agents
    agent_manager.register("main", {
        "system_prompt": "You are the main assistant."
    })
    agent_manager.register("support", {
        "system_prompt": "You are the support assistant."
    })
    
    # 设置路由绑定
    gateway.add_binding("support", 1, "peer_id", "user-123")  # 特定用户 -> support
    gateway.add_binding("support", 2, "guild_id", "guild-456")  # 特定群组 -> support
    gateway.add_binding("main", 5, "default", "*")  # 兜底 -> main
    
    # 注册处理器
    gateway.register_agent("main", agent_manager.process)
    gateway.register_agent("support", agent_manager.process)
    
    # 测试路由
    print("\n=== 路由测试 ===")
    
    # 测试 1: 普通用户 -> main
    msg1 = InboundMessage(text="Hello", sender_id="user-1", channel="cli")
    routed1 = gateway.route(msg1)
    print(f"User-1 -> agent: {routed1.agent_id}")
    
    # 测试 2: 特定用户 -> support
    msg2 = InboundMessage(text="Help", sender_id="user-123", peer_id="user-123", channel="cli")
    routed2 = gateway.route(msg2)
    print(f"User-123 -> agent: {routed2.agent_id}")
    
    # 测试 3: 特定群组 -> support
    msg3 = InboundMessage(text="Hi", sender_id="user-2", guild_id="guild-456", channel="cli")
    routed3 = gateway.route(msg3)
    print(f"Guild-456 -> agent: {routed3.agent_id}")
    
    print("\n✅ c05 测试通过")


if __name__ == "__main__":
    main()