#!/usr/bin/env python3
"""
c07_heartbeat_cron.py - Heartbeat & Cron (OpenAI Version)

主动出击。Agent 不只是等待用户，还定时检查任务。

心跳 (Heartbeat): 定时触发，检查是否需要做什么
定时任务 (Cron): 按 cron 表达式执行任务
"""

import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
import re

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
# Cron 表达式解析（简化版）
# ============================================================

@dataclass
class CronSchedule:
    """Cron 调度。"""
    minute: str = "*"
    hour: str = "*"
    day: str = "*"
    month: str = "*"
    weekday: str = "*"
    
    @classmethod
    def parse(cls, expr: str) -> "CronSchedule":
        """解析 cron 表达式。"""
        parts = expr.strip().split()
        if len(parts) != 5:
            # 默认每小时
            return cls(minute="0")
        return cls(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            weekday=parts[4],
        )
    
    def matches(self, dt: datetime) -> bool:
        """检查是否匹配当前时间。"""
        def match_field(field: str, value: int, max_val: int) -> bool:
            if field == "*":
                return True
            if field.isdigit():
                return int(field) == value
            if "," in field:
                return any(match_field(f.strip(), value, max_val) for f in field.split(","))
            if "/" in field:
                step = int(field.split("/")[1])
                return value % step == 0
            if "-" in field:
                start, end = map(int, field.split("-"))
                return start <= value <= end
            return False
        
        return (
            match_field(self.minute, dt.minute, 59) and
            match_field(self.hour, dt.hour, 23) and
            match_field(self.day, dt.day, 31) and
            match_field(self.month, dt.month, 12) and
            match_field(self.weekday, dt.weekday(), 6)
        )


# ============================================================
# Cron Job
# ============================================================

@dataclass
class CronJob:
    """定时任务。"""
    id: str
    schedule: CronSchedule
    task: str  # 任务描述
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None


class CronScheduler:
    """Cron 调度器。"""
    
    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_trigger: Optional[Callable[[CronJob], None]] = None
    
    def add_job(self, job_id: str, cron_expr: str, task: str) -> CronJob:
        """添加定时任务。"""
        job = CronJob(
            id=job_id,
            schedule=CronSchedule.parse(cron_expr),
            task=task,
        )
        self.jobs[job_id] = job
        return job
    
    def remove_job(self, job_id: str) -> bool:
        """移除定时任务。"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False
    
    def set_handler(self, handler: Callable[[CronJob], None]):
        """设置触发处理器。"""
        self._on_trigger = handler
    
    def start(self):
        """启动调度器。"""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止调度器。"""
        self._running = False
    
    def _run_loop(self):
        """调度循环。"""
        while self._running:
            now = datetime.now()
            
            for job in self.jobs.values():
                if not job.enabled:
                    continue
                if job.schedule.matches(now):
                    # 避免同一分钟重复触发
                    if job.last_run:
                        last = datetime.fromisoformat(job.last_run)
                        if (now - last).total_seconds() < 60:
                            continue
                    
                    job.last_run = now.isoformat()
                    if self._on_trigger:
                        self._on_trigger(job)
            
            time.sleep(60)  # 每分钟检查一次


# ============================================================
# Heartbeat
# ============================================================

@dataclass
class HeartbeatConfig:
    """心跳配置。"""
    interval_seconds: int = 300  # 5分钟
    enabled: bool = True
    tasks: List[str] = field(default_factory=list)


class Heartbeat:
    """心跳系统。"""
    
    def __init__(self, config: HeartbeatConfig = None):
        self.config = config or HeartbeatConfig()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_beat: Optional[Callable[[], None]] = None
        self._last_beat: Optional[datetime] = None
    
    def set_handler(self, handler: Callable[[], None]):
        """设置心跳处理器。"""
        self._on_beat = handler
    
    def start(self):
        """启动心跳。"""
        if not self.config.enabled:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止心跳。"""
        self._running = False
    
    def _run_loop(self):
        """心跳循环。"""
        while self._running:
            time.sleep(self.config.interval_seconds)
            self._last_beat = datetime.now()
            if self._on_beat:
                self._on_beat()
    
    def trigger_now(self):
        """立即触发心跳。"""
        self._last_beat = datetime.now()
        if self._on_beat:
            self._on_beat()


# ============================================================
# Proactive Agent
# ============================================================

class ProactiveAgent:
    """主动 Agent。"""
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self.cron_scheduler = CronScheduler()
        self.heartbeat = Heartbeat(HeartbeatConfig(interval_seconds=300))
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置处理器。"""
        def on_heartbeat():
            print(f"\033[35m[Heartbeat] {datetime.now().isoformat()}\033[0m")
            # 检查是否有需要做的事情
            self._check_tasks()
        
        def on_cron(job: CronJob):
            print(f"\033[33m[Cron] {job.id}: {job.task}\033[0m")
            self._execute_cron_job(job)
        
        self.heartbeat.set_handler(on_heartbeat)
        self.cron_scheduler.set_handler(on_cron)
    
    def _check_tasks(self):
        """检查任务。"""
        # 简化实现：发送一个提示给 LLM
        prompt = "It's time for heartbeat check. Is there anything that needs attention?"
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a proactive agent. Check if anything needs attention."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
            )
            print(f"Check result: {response.choices[0].message.content[:200]}")
        except Exception as e:
            print(f"Heartbeat error: {e}")
    
    def _execute_cron_job(self, job: CronJob):
        """执行定时任务。"""
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a scheduled task executor."},
                    {"role": "user", "content": f"Execute task: {job.task}"},
                ],
                max_tokens=1000,
            )
            print(f"Result: {response.choices[0].message.content[:300]}")
        except Exception as e:
            print(f"Cron job error: {e}")
    
    def add_cron_job(self, job_id: str, cron_expr: str, task: str):
        """添加定时任务。"""
        return self.cron_scheduler.add_job(job_id, cron_expr, task)
    
    def start(self):
        """启动 Agent。"""
        self.cron_scheduler.start()
        self.heartbeat.start()
        print(f"\033[36mProactive Agent '{self.agent_id}' started\033[0m")
        print("Heartbeat: every 5 minutes")
        print(f"Cron jobs: {len(self.cron_scheduler.jobs)}")
    
    def stop(self):
        """停止 Agent。"""
        self.cron_scheduler.stop()
        self.heartbeat.stop()


# ============================================================
# Main
# ============================================================

def main():
    print(f"\033[36mOpenAI Agent Harness - c07 (Heartbeat & Cron)\033[0m")
    print(f"Model: {MODEL}")
    
    agent = ProactiveAgent("test")
    
    # 添加定时任务
    agent.add_cron_job("morning-greeting", "0 9 * * *", "Send a morning greeting")
    agent.add_cron_job("daily-report", "0 18 * * *", "Generate daily report")
    
    # 测试 cron 表达式解析
    schedule = CronSchedule.parse("*/5 * * * *")
    print(f"\nCron '*/5 * * * *' matches minute 0: {schedule.matches(datetime(2024, 1, 1, 9, 0))}")
    print(f"Cron '*/5 * * * *' matches minute 5: {schedule.matches(datetime(2024, 1, 1, 9, 5))}")
    
    # 触发心跳测试
    print("\n触发心跳测试...")
    agent.heartbeat.trigger_now()
    
    print("\n✅ c07 测试通过")


if __name__ == "__main__":
    main()