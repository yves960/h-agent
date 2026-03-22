#!/usr/bin/env python3
"""
h_agent/concurrency/heartbeat.py - s07 Heartbeat Implementation

Lane mutual exclusion + should_run() preconditions.
"""

import threading
import time
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

lane_lock = threading.Lock()


class HeartbeatRunner:
    def __init__(
        self,
        heartbeat_path: Path,
        interval: float = 60.0,
        active_hours: Tuple[int, int] = (0, 24),
    ):
        self.heartbeat_path = Path(heartbeat_path)
        self.interval = interval
        self.active_hours = active_hours

        self.running = False
        self.last_run_at = 0.0
        self._thread: Optional[threading.Thread] = None
        self._stopped = False
        self._last_output = ""
        self._queue_lock = threading.Lock()
        self._output_queue = []

    def should_run(self) -> Tuple[bool, str]:
        if not self.heartbeat_path.exists():
            return False, "HEARTBEAT.md not found"

        if not self.heartbeat_path.read_text(encoding="utf-8").strip():
            return False, "HEARTBEAT.md is empty"

        elapsed = time.time() - self.last_run_at
        if elapsed < self.interval:
            return False, f"interval not elapsed ({self.interval - elapsed:.0f}s remaining)"

        hour = datetime.now().hour
        s, e = self.active_hours
        in_hours = (s <= hour < e) if s <= e else not (e <= hour < s)
        if not in_hours:
            return False, f"outside active hours ({s}:00-{e}:00)"

        if self.running:
            return False, "already running"

        return True, "all checks passed"

    def _execute(self) -> None:
        acquired = lane_lock.acquire(blocking=False)
        if not acquired:
            return

        self.running = True
        try:
            instructions = self.heartbeat_path.read_text(encoding="utf-8")
            response = self._run_agent_single_turn(instructions)
            meaningful = self._parse_response(response)
            if meaningful and meaningful.strip() != self._last_output:
                self._last_output = meaningful.strip()
                with self._queue_lock:
                    self._output_queue.append(meaningful)
        finally:
            self.running = False
            self.last_run_at = time.time()
            lane_lock.release()

    def _run_agent_single_turn(self, instructions: str) -> str:
        return "HEARTBEAT_OK"

    def _parse_response(self, response: str) -> str:
        if response.strip() == "HEARTBEAT_OK":
            return ""
        return response

    def start(self, daemon: bool = True) -> None:
        self._stopped = False
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=daemon)
        self._thread.start()

    def stop(self) -> None:
        self._stopped = True
        if self._thread:
            self._thread.join(timeout=5)

    def _heartbeat_loop(self) -> None:
        while not self._stopped:
            ok, reason = self.should_run()
            if ok:
                self._execute()
            time.sleep(1)

    def get_output(self) -> list:
        with self._queue_lock:
            output = list(self._output_queue)
            self._output_queue.clear()
            return output
