"""
Channels - 多通道支持
"""

import os
import json
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable


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
class OutboundMessage:
    """出站消息。"""
    text: str
    channel: str = ""
    peer_id: str = ""
    account_id: str = ""
    metadata: dict = field(default_factory=dict)


class Channel(ABC):
    """通道基类。"""
    
    def __init__(self, account_id: str = "default"):
        self.account_id = account_id
        self.on_message: Optional[Callable[[InboundMessage], None]] = None
    
    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def stop(self):
        pass
    
    @abstractmethod
    def send(self, msg: OutboundMessage):
        pass
    
    def set_handler(self, handler: Callable[[InboundMessage], None]):
        self.on_message = handler


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
        print("\033[36mCLI Channel started. Type 'quit' to exit.\033[0m")
        
        while self.running:
            try:
                text = input("\033[36mYou> \033[0m")
            except (EOFError, KeyboardInterrupt):
                break
            
            if not text.strip():
                continue
            
            if text.lower() == "quit":
                self.running = False
                break
            
            msg = InboundMessage(
                text=text,
                sender_id="user",
                channel="cli",
                account_id=self.account_id,
            )
            
            if self.on_message:
                self.on_message(msg)
    
    def send(self, msg: OutboundMessage):
        print(f"\033[32mAgent: {msg.text}\033[0m")


class MockChannel(Channel):
    """模拟通道（测试用）。"""
    
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


class ChannelManager:
    """通道管理器。"""
    
    def __init__(self):
        self.channels: Dict[str, Channel] = {}
    
    def register(self, channel: Channel):
        self.channels[channel.account_id] = channel
    
    def unregister(self, account_id: str) -> bool:
        if account_id in self.channels:
            del self.channels[account_id]
            return True
        return False
    
    def start_all(self):
        for channel in self.channels.values():
            channel.start()
    
    def stop_all(self):
        for channel in self.channels.values():
            channel.stop()
    
    def send(self, msg: OutboundMessage):
        account_id = msg.account_id or msg.channel
        if account_id in self.channels:
            self.channels[account_id].send(msg)
        else:
            for channel in self.channels.values():
                channel.send(msg)
    
    def broadcast(self, text: str, exclude: str = None):
        for account_id, channel in self.channels.items():
            if account_id != exclude:
                channel.send(OutboundMessage(text=text))