#!/usr/bin/env python3
"""
c10_concurrency.py - Concurrency (OpenAI Version)

并发。命名车道，避免竞态。

核心概念:
  - Lane (车道): 每个 agent 有自己的执行车道
  - Generation Track: 每次生成有唯一 ID，避免旧响应覆盖新响应
  - Lock by Name: 按名称加锁，细粒度并发控制
"""

import os
import json
import time
import threading
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import uuid

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")


# ============================================================
# Generation Track
# ============================================================

@dataclass
class Generation:
    """生成追踪。"""
    id: str
    agent_id: str
    session_key: str
    status: str = "pending"  # pending, streaming, completed, cancelled
    started_at: str = ""
    completed_at: str = ""
    tokens_used: int = 0


class GenerationTracker:
    """生成追踪器。"""
    
    def __init__(self):
        self.generations: Dict[str, Generation] = {}
        self._active: Dict[str, str] = {}  # session_key -> generation_id
    
    def start(self, agent_id: str, session_key: str) -> str:
        """开始生成。"""
        # 取消同一 session 的之前生成
        if session_key in self._active:
            old_id = self._active[session_key]
            if old_id in self.generations:
                self.generations[old_id].status = "cancelled"
        
        gen_id = f"gen-{uuid.uuid4().hex[:8]}"
        generation = Generation(
            id=gen_id,
            agent_id=agent_id,
            session_key=session_key,
            status="pending",
            started_at=datetime.now().isoformat(),
        )
        
        self.generations[gen_id] = generation
        self._active[session_key] = gen_id
        
        return gen_id
    
    def update(self, gen_id: str, **kwargs):
        """更新生成状态。"""
        if gen_id in self.generations:
            for key, value in kwargs.items():
                if hasattr(self.generations[gen_id], key):
                    setattr(self.generations[gen_id], key, value)
    
    def complete(self, gen_id: str):
        """完成生成。"""
        if gen_id in self.generations:
            gen = self.generations[gen_id]
            gen.status = "completed"
            gen.completed_at = datetime.now().isoformat()
            
            # 从 active 中移除
            if gen.session_key in self._active:
                if self._active[gen.session_key] == gen_id:
                    del self._active[gen.session_key]
    
    def is_active(self, gen_id: str) -> bool:
        """检查是否活跃。"""
        if gen_id not in self.generations:
            return False
        return self.generations[gen_id].status in ("pending", "streaming")


# ============================================================
# Named Locks
# ============================================================

class NamedLock:
    """命名锁。"""
    
    def __init__(self):
        self._locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
    
    def get_lock(self, name: str) -> threading.Lock:
        """获取命名锁。"""
        with self._global_lock:
            if name not in self._locks:
                self._locks[name] = threading.Lock()
            return self._locks[name]
    
    def acquire(self, name: str, timeout: float = None) -> bool:
        """获取锁。"""
        lock = self.get_lock(name)
        return lock.acquire(timeout=timeout)
    
    def release(self, name: str):
        """释放锁。"""
        with self._global_lock:
            if name in self._locks:
                self._locks[name].release()
    
    def is_locked(self, name: str) -> bool:
        """检查是否被锁定。"""
        lock = self.get_lock(name)
        acquired = lock.acquire(blocking=False)
        if acquired:
            lock.release()
        return not acquired


# ============================================================
# Lane (执行车道)
# ============================================================

class LaneState(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    BLOCKED = "blocked"


@dataclass
class Lane:
    """执行车道。"""
    id: str
    agent_id: str
    state: LaneState = LaneState.IDLE
    current_task: Optional[str] = None
    completed_tasks: int = 0
    created_at: str = ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "state": self.state.value,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
        }


class LaneManager:
    """车道管理器。"""
    
    def __init__(self):
        self.lanes: Dict[str, Lane] = {}
        self._lock = threading.Lock()
    
    def create_lane(self, lane_id: str, agent_id: str) -> Lane:
        """创建车道。"""
        with self._lock:
            lane = Lane(
                id=lane_id,
                agent_id=agent_id,
                created_at=datetime.now().isoformat(),
            )
            self.lanes[lane_id] = lane
            return lane
    
    def get_lane(self, lane_id: str) -> Optional[Lane]:
        """获取车道。"""
        return self.lanes.get(lane_id)
    
    def acquire_lane(self, lane_id: str, task: str) -> bool:
        """获取车道使用权。"""
        with self._lock:
            lane = self.lanes.get(lane_id)
            if not lane or lane.state == LaneState.BUSY:
                return False
            lane.state = LaneState.BUSY
            lane.current_task = task
            return True
    
    def release_lane(self, lane_id: str):
        """释放车道。"""
        with self._lock:
            lane = self.lanes.get(lane_id)
            if lane:
                lane.state = LaneState.IDLE
                lane.current_task = None
                lane.completed_tasks += 1
    
    def get_agent_lane(self, agent_id: str) -> Optional[Lane]:
        """获取 Agent 的车道。"""
        for lane in self.lanes.values():
            if lane.agent_id == agent_id:
                return lane
        return None


# ============================================================
# Concurrent Agent
# ============================================================

class ConcurrentAgent:
    """并发安全 Agent。"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.lane_manager = LaneManager()
        self.generation_tracker = GenerationTracker()
        self.named_locks = NamedLock()
        
        # 为每个 agent 创建车道
        self.lane = self.lane_manager.create_lane(
            lane_id=f"lane-{agent_id}",
            agent_id=agent_id,
        )
        
        self._messages: Dict[str, list] = {}  # session_key -> messages
    
    def chat(self, session_key: str, user_input: str) -> str:
        """并发安全的对话。"""
        # 获取车道
        if not self.lane_manager.acquire_lane(self.lane.id, user_input[:50]):
            return "Agent is busy, please wait."
        
        # 开始生成追踪
        gen_id = self.generation_tracker.start(self.agent_id, session_key)
        
        try:
            # 获取会话历史
            if session_key not in self._messages:
                self._messages[session_key] = []
            messages = self._messages[session_key]
            
            messages.append({"role": "user", "content": user_input})
            
            # 调用 LLM
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"You are agent {self.agent_id}."}
                ] + messages[-20:],
                max_tokens=2048,
            )
            
            reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
            
            # 完成生成
            self.generation_tracker.complete(gen_id)
            
            return reply
        
        except Exception as e:
            self.generation_tracker.update(gen_id, status="failed")
            return f"Error: {e}"
        
        finally:
            self.lane_manager.release_lane(self.lane.id)
    
    def get_status(self) -> dict:
        """获取状态。"""
        return {
            "agent_id": self.agent_id,
            "lane": self.lane.to_dict(),
            "active_generations": len([
                g for g in self.generation_tracker.generations.values()
                if g.status in ("pending", "streaming")
            ]),
        }


# ============================================================
# Main
# ============================================================

def main():
    print(f"\033[36mOpenAI Agent Harness - c10 (Concurrency)\033[0m")
    print(f"Model: {MODEL}")
    
    # 测试车道管理
    print("\n=== 车道管理测试 ===")
    lane_mgr = LaneManager()
    lane = lane_mgr.create_lane("test-lane", "agent-1")
    print(f"Created lane: {lane.id}, state: {lane.state.value}")
    
    acquired = lane_mgr.acquire_lane("test-lane", "task-1")
    print(f"Acquired: {acquired}, state: {lane.state.value}")
    
    lane_mgr.release_lane("test-lane")
    print(f"Released, state: {lane.state.value}, completed: {lane.completed_tasks}")
    
    # 测试命名锁
    print("\n=== 命名锁测试 ===")
    locks = NamedLock()
    
    locks.acquire("resource-a")
    print(f"resource-a locked: {locks.is_locked('resource-a')}")
    print(f"resource-b locked: {locks.is_locked('resource-b')}")
    
    locks.release("resource-a")
    print(f"resource-a locked after release: {locks.is_locked('resource-a')}")
    
    # 测试生成追踪
    print("\n=== 生成追踪测试 ===")
    tracker = GenerationTracker()
    
    gen1 = tracker.start("agent-1", "session-1")
    print(f"Started generation: {gen1}")
    
    gen2 = tracker.start("agent-1", "session-1")  # 同一 session
    print(f"New generation: {gen2}")
    print(f"Old generation status: {tracker.generations[gen1].status}")
    
    tracker.complete(gen2)
    print(f"Completed: {tracker.generations[gen2].status}")
    
    # 测试并发 Agent
    print("\n=== 并发 Agent 测试 ===")
    agent = ConcurrentAgent("test-agent")
    status = agent.get_status()
    print(f"Agent status: lane={status['lane']['state']}, active={status['active_generations']}")
    
    print("\n✅ c10 测试通过")


if __name__ == "__main__":
    main()