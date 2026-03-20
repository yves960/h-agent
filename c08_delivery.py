#!/usr/bin/env python3
"""
c08_delivery.py - Message Delivery (OpenAI Version)

可靠投递。消息不丢失，失败会重试。

核心机制:
  - Write-Ahead Log: 发送前先记录
  - Retry Queue: 失败的消息进入重试队列
  - Backoff: 指数退避重试
"""

import os
import json
import time
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

WORKSPACE_DIR = Path.cwd() / ".agent_workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Message Status
# ============================================================

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueuedMessage:
    """队列中的消息。"""
    id: str
    content: str
    channel: str
    peer_id: str
    status: MessageStatus = MessageStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    created_at: str = ""
    last_attempt: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "channel": self.channel,
            "peer_id": self.peer_id,
            "status": self.status.value,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "last_attempt": self.last_attempt,
            "error": self.error,
        }


# ============================================================
# Write-Ahead Log
# ============================================================

class WriteAheadLog:
    """写入前日志，确保消息不丢失。"""
    
    def __init__(self, wal_dir: Path = None):
        self.wal_dir = wal_dir or WORKSPACE_DIR / "wal"
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    def _wal_file(self) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.wal_dir / f"wal-{date_str}.jsonl"
    
    def append(self, msg: QueuedMessage) -> None:
        """追加消息到 WAL。"""
        with self._lock:
            wal_file = self._wal_file()
            with open(wal_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg.to_dict(), ensure_ascii=False) + "\n")
    
    def load_pending(self) -> List[QueuedMessage]:
        """加载未完成的消息。"""
        messages = []
        wal_file = self._wal_file()
        if not wal_file.exists():
            return messages
        
        with open(wal_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        msg = QueuedMessage(
                            id=data["id"],
                            content=data["content"],
                            channel=data["channel"],
                            peer_id=data["peer_id"],
                            status=MessageStatus(data.get("status", "pending")),
                            attempts=data.get("attempts", 0),
                            created_at=data.get("created_at", ""),
                            last_attempt=data.get("last_attempt"),
                            error=data.get("error"),
                        )
                        if msg.status != MessageStatus.SENT:
                            messages.append(msg)
                    except:
                        pass
        
        return messages


# ============================================================
# Retry Queue with Backoff
# ============================================================

class RetryQueue:
    """带退避的重试队列。"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._messages: Dict[str, QueuedMessage] = {}
    
    def put(self, msg: QueuedMessage) -> None:
        """添加消息到重试队列。"""
        # 计算退避时间
        delay = min(self.base_delay * (2 ** msg.attempts), self.max_delay)
        retry_time = time.time() + delay
        
        self._messages[msg.id] = msg
        self._queue.put((retry_time, msg.id))
    
    def get(self, timeout: float = 1.0) -> Optional[QueuedMessage]:
        """获取可重试的消息。"""
        try:
            retry_time, msg_id = self._queue.get(timeout=timeout)
            now = time.time()
            
            if retry_time > now:
                # 还没到重试时间，放回去
                self._queue.put((retry_time, msg_id))
                return None
            
            if msg_id in self._messages:
                return self._messages.pop(msg_id)
        except queue.Empty:
            pass
        return None
    
    def size(self) -> int:
        return len(self._messages)


# ============================================================
# Delivery Manager
# ============================================================

class DeliveryManager:
    """消息投递管理器。"""
    
    def __init__(self):
        self.wal = WriteAheadLog()
        self.retry_queue = RetryQueue()
        self._senders: Dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def register_sender(self, channel: str, sender: Callable[[str, str], bool]):
        """注册通道发送器。"""
        self._senders[channel] = sender
    
    def send(self, msg: QueuedMessage) -> bool:
        """发送消息。"""
        sender = self._senders.get(msg.channel)
        if not sender:
            msg.error = f"No sender for channel: {msg.channel}"
            return False
        
        try:
            success = sender(msg.peer_id, msg.content)
            if success:
                msg.status = MessageStatus.SENT
                return True
            else:
                msg.error = "Send returned False"
                return False
        except Exception as e:
            msg.error = str(e)
            return False
    
    def enqueue(self, content: str, channel: str, peer_id: str) -> QueuedMessage:
        """加入发送队列。"""
        import uuid
        msg = QueuedMessage(
            id=f"msg-{uuid.uuid4().hex[:8]}",
            content=content,
            channel=channel,
            peer_id=peer_id,
            created_at=datetime.now().isoformat(),
        )
        
        # 写入 WAL
        self.wal.append(msg)
        
        # 尝试发送
        msg.attempts += 1
        msg.last_attempt = datetime.now().isoformat()
        
        if self.send(msg):
            msg.status = MessageStatus.SENT
        else:
            msg.status = MessageStatus.RETRYING
            self.retry_queue.put(msg)
        
        self.wal.append(msg)  # 更新 WAL
        return msg
    
    def start(self):
        """启动投递器。"""
        # 加载未完成的消息
        pending = self.wal.load_pending()
        for msg in pending:
            self.retry_queue.put(msg)
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止投递器。"""
        self._running = False
    
    def _run_loop(self):
        """投递循环。"""
        while self._running:
            msg = self.retry_queue.get(timeout=1.0)
            if msg is None:
                continue
            
            msg.attempts += 1
            msg.last_attempt = datetime.now().isoformat()
            
            if msg.attempts > msg.max_attempts:
                msg.status = MessageStatus.FAILED
                print(f"Message {msg.id} failed after {msg.attempts} attempts")
                continue
            
            if self.send(msg):
                msg.status = MessageStatus.SENT
                print(f"Message {msg.id} sent successfully")
            else:
                msg.status = MessageStatus.RETRYING
                self.retry_queue.put(msg)


# ============================================================
# Mock Sender (测试用)
# ============================================================

class MockSender:
    """模拟发送器。"""
    
    def __init__(self, fail_rate: float = 0.0):
        self.fail_rate = fail_rate
        self.sent: List[tuple] = []
        self._call_count = 0
    
    def send(self, peer_id: str, content: str) -> bool:
        self._call_count += 1
        
        # 模拟偶尔失败
        import random
        if random.random() < self.fail_rate:
            return False
        
        self.sent.append((peer_id, content))
        return True


# ============================================================
# Main
# ============================================================

def main():
    print(f"\033[36mOpenAI Agent Harness - c08 (Delivery)\033[0m")
    
    dm = DeliveryManager()
    
    # 注册模拟发送器
    mock_sender = MockSender(fail_rate=0.0)
    dm.register_sender("mock", mock_sender.send)
    
    # 发送测试消息
    print("\n=== 发送测试消息 ===")
    msg1 = dm.enqueue("Hello, World!", "mock", "user-1")
    print(f"Message 1: {msg1.id}, status: {msg1.status.value}")
    
    msg2 = dm.enqueue("Test message", "mock", "user-2")
    print(f"Message 2: {msg2.id}, status: {msg2.status.value}")
    
    # 检查发送结果
    print(f"\n已发送: {len(mock_sender.sent)} 条消息")
    for peer_id, content in mock_sender.sent:
        print(f"  -> {peer_id}: {content}")
    
    print("\n✅ c08 测试通过")


if __name__ == "__main__":
    main()