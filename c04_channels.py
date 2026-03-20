#!/usr/bin/env python3
"""
c04_channels.py - Multi-Channel Support (OpenAI Version)

同一大脑，多个嘴巴。
Channel 封装了平台差异，使 agent 循环只看到统一的 InboundMessage。

支持的通道:
  - CLI (标准输入输出)
  - Telegram (需要 TELEGRAM_BOT_TOKEN)
  - 可扩展其他平台
"""

import os
import json
import asyncio
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

# ============================================================
# 数据结构
# ============================================================

@dataclass
class InboundMessage:
    """所有通道都规范化为此结构。"""
    text: str
    sender_id: str
    channel: str = ""
    account_id: str = ""
    peer_id: str = ""  # 群组/频道 ID
    is_group: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class OutboundMessage:
    """输出消息。"""
    text: str
    channel: str = ""
    peer_id: str = ""
    metadata: dict = field(default_factory=dict)


# ============================================================
# Channel 抽象基类
# ============================================================

class Channel(ABC):
    """通道抽象基类。"""
    
    def __init__(self, account_id: str = "default"):
        self.account_id = account_id
        self.on_message: Optional[Callable[[InboundMessage], None]] = None
    
    @abstractmethod
    def start(self):
        """启动通道。"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止通道。"""
        pass
    
    @abstractmethod
    def send(self, msg: OutboundMessage):
        """发送消息。"""
        pass
    
    def set_handler(self, handler: Callable[[InboundMessage], None]):
        """设置消息处理函数。"""
        self.on_message = handler


# ============================================================
# CLI Channel (标准输入输出)
# ============================================================

class CLIChannel(Channel):
    """命令行通道。"""
    
    def __init__(self, account_id: str = "cli"):
        super().__init__(account_id)
        self.running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self.running = False
    
    def _run_loop(self):
        """读取标准输入。"""
        print("\033[36mCLI Channel started. Type 'quit' to exit.\033[0m")
        
        while self.running:
            try:
                text = input("\033[36mYou > \033[0m")
            except (EOFError, KeyboardInterrupt):
                break
            
            if not text.strip():
                continue
            
            if text.lower() == "quit":
                self.running = False
                break
            
            # 构造 InboundMessage
            msg = InboundMessage(
                text=text,
                sender_id="user",
                channel="cli",
                account_id=self.account_id,
            )
            
            # 调用处理函数
            if self.on_message:
                self.on_message(msg)
    
    def send(self, msg: OutboundMessage):
        """打印到标准输出。"""
        print(f"\033[32mAgent: {msg.text}\033[0m")


# ============================================================
# Mock Channel (测试用)
# ============================================================

class MockChannel(Channel):
    """模拟通道，用于测试。"""
    
    def __init__(self, account_id: str = "mock"):
        super().__init__(account_id)
        self.messages: List[InboundMessage] = []
        self.sent: List[OutboundMessage] = []
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def send(self, msg: OutboundMessage):
        self.sent.append(msg)
    
    def receive(self, text: str, sender_id: str = "test-user"):
        """模拟接收消息。"""
        msg = InboundMessage(
            text=text,
            sender_id=sender_id,
            channel="mock",
            account_id=self.account_id,
        )
        self.messages.append(msg)
        if self.on_message:
            self.on_message(msg)
        return msg


# ============================================================
# Channel Manager
# ============================================================

class ChannelManager:
    """管理多个通道。"""
    
    def __init__(self):
        self.channels: Dict[str, Channel] = {}
        self._message_queue: List[InboundMessage] = []
        self._lock = threading.Lock()
    
    def register(self, channel: Channel):
        """注册通道。"""
        self.channels[channel.account_id] = channel
    
    def start_all(self):
        """启动所有通道。"""
        for channel in self.channels.values():
            channel.start()
    
    def stop_all(self):
        """停止所有通道。"""
        for channel in self.channels.values():
            channel.stop()
    
    def send(self, msg: OutboundMessage):
        """发送消息到指定通道。"""
        account_id = msg.account_id or msg.channel
        if account_id in self.channels:
            self.channels[account_id].send(msg)
        else:
            # 默认发送到所有通道
            for channel in self.channels.values():
                channel.send(msg)
    
    def broadcast(self, text: str, exclude_channel: str = None):
        """广播消息到所有通道。"""
        for account_id, channel in self.channels.items():
            if account_id != exclude_channel:
                channel.send(OutboundMessage(text=text, channel=account_id))


# ============================================================
# Multi-Channel Agent
# ============================================================

class MultiChannelAgent:
    """多通道 Agent。"""
    
    def __init__(self):
        self.channel_manager = ChannelManager()
        self.conversations: Dict[str, List[dict]] = {}  # peer_id -> messages
    
    def get_system_prompt(self) -> str:
        return "You are a helpful AI assistant connected to multiple channels."
    
    def handle_message(self, inbound: InboundMessage):
        """处理来自任意通道的消息。"""
        # 获取或创建对话
        peer_key = f"{inbound.channel}:{inbound.peer_id or inbound.sender_id}"
        
        if peer_key not in self.conversations:
            self.conversations[peer_key] = []
        
        messages = self.conversations[peer_key]
        messages.append({"role": "user", "content": inbound.text})
        
        # 调用 LLM
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()}
                ] + messages[-20:],  # 限制上下文长度
                max_tokens=2048,
            )
            
            reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
            
            # 发送回复
            outbound = OutboundMessage(
                text=reply,
                channel=inbound.channel,
                peer_id=inbound.peer_id,
                account_id=inbound.account_id,
            )
            
            # 找到对应通道并发送
            if inbound.account_id in self.channel_manager.channels:
                self.channel_manager.channels[inbound.account_id].send(outbound)
            else:
                # 回退到广播
                self.channel_manager.broadcast(reply, exclude_channel=None)
            
        except Exception as e:
            error_msg = f"Error: {e}"
            print(f"\033[31m{error_msg}\033[0m")
    
    def add_channel(self, channel: Channel):
        """添加通道。"""
        channel.set_handler(self.handle_message)
        self.channel_manager.register(channel)
    
    def run(self):
        """运行 Agent。"""
        self.channel_manager.start_all()
        
        # 等待所有通道停止
        try:
            while True:
                running = any(
                    getattr(c, 'running', True)
                    for c in self.channel_manager.channels.values()
                )
                if not running:
                    break
                import time
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        
        self.channel_manager.stop_all()


# ============================================================
# Main
# ============================================================

def main():
    print(f"\033[36mOpenAI Agent Harness - c04 (Channels)\033[0m")
    print(f"Model: {MODEL}")
    print()
    
    agent = MultiChannelAgent()
    
    # 添加 CLI 通道
    cli = CLIChannel()
    agent.add_channel(cli)
    
    # 运行
    agent.run()


if __name__ == "__main__":
    main()