#!/usr/bin/env python3
"""
h_agent/concurrency/lanes.py - s10 LaneQueue Implementation

Named lanes with FIFO deque + threading.Condition + generation tracking.
"""

import threading
import concurrent.futures
from collections import deque
from dataclasses import dataclass
from typing import Optional, Callable, Any, Dict, List

@dataclass
class LaneStats:
    """Statistics for a lane."""
    name: str
    active: int
    queued: int
    max_concurrency: int
    generation: int

class LaneQueue:
    """
    A single named lane with FIFO queue and concurrency control.
    
    Uses threading.Condition for efficient wait/notify.
    Generation tracking prevents zombie tasks from pumping after restart.
    """
    
    def __init__(self, name: str, max_concurrency: int = 1):
        self.name = name
        self.max_concurrency = max(1, max_concurrency)
        self._deque = deque()
        self._condition = threading.Condition()
        self._active_count = 0
        self._generation = 0
    
    def enqueue(self, fn: Callable[[], Any], generation: Optional[int] = None) -> concurrent.futures.Future:
        """Enqueue a task and start execution if capacity available."""
        future = concurrent.futures.Future()
        with self._condition:
            gen = generation if generation is not None else self._generation
            self._deque.append((fn, future, gen))
            self._pump()
        return future
    
    def _pump(self) -> None:
        """Pop and start tasks while active < max_concurrency."""
        while self._active_count < self.max_concurrency and self._deque:
            fn, future, gen = self._deque.popleft()
            self._active_count += 1
            threading.Thread(
                target=self._run_task,
                args=(fn, future, gen),
                daemon=True,
            ).start()
    
    def _run_task(self, fn: Callable[[], Any], future: concurrent.futures.Future, gen: int) -> None:
        """Run the task and handle completion."""
        try:
            result = fn()
            future.set_result(result)
        except Exception as exc:
            future.set_exception(exc)
        finally:
            self._task_done(gen)
    
    def _task_done(self, gen: int) -> None:
        """Called when a task completes. Re-pump if generation matches."""
        with self._condition:
            self._active_count -= 1
            if gen == self._generation:
                self._pump()
            self._condition.notify_all()
    
    def wait_for_idle(self, timeout: Optional[float] = None) -> bool:
        """Wait until all active tasks complete. Returns True if idle."""
        with self._condition:
            if self._active_count == 0 and len(self._deque) == 0:
                return True
            self._condition.wait_for(
                lambda: self._active_count == 0 and len(self._deque) == 0,
                timeout=timeout,
            )
            return self._active_count == 0 and len(self._deque) == 0
    
    def stats(self) -> LaneStats:
        """Get current lane statistics."""
        with self._condition:
            return LaneStats(
                name=self.name,
                active=self._active_count,
                queued=len(self._deque),
                max_concurrency=self.max_concurrency,
                generation=self._generation,
            )
    
    def set_max_concurrency(self, max_concurrency: int) -> None:
        """Update max concurrency and re-pump if capacity available."""
        with self._condition:
            self.max_concurrency = max(1, max_concurrency)
            self._pump()
    
    def clear(self) -> int:
        """Clear all pending tasks. Returns count of cleared tasks."""
        with self._condition:
            count = len(self._deque)
            self._deque.clear()
            return count
    
    def reset(self) -> None:
        """Increment generation - stale tasks will not re-pump."""
        with self._condition:
            self._generation += 1


class CommandQueue:
    """
    Dispatcher with lazy lane creation.
    
    Manages multiple named LaneQueues.
    """
    
    LANE_MAIN = "main"
    LANE_CRON = "cron"
    LANE_HEARTBEAT = "heartbeat"
    
    def __init__(self):
        self._lanes: Dict[str, LaneQueue] = {}
        self._lock = threading.Lock()
    
    def get_or_create_lane(self, name: str, max_concurrency: int = 1) -> LaneQueue:
        """Get existing lane or create new one."""
        with self._lock:
            if name not in self._lanes:
                self._lanes[name] = LaneQueue(name, max_concurrency)
            return self._lanes[name]
    
    def enqueue(self, lane_name: str, fn: Callable[[], Any]) -> concurrent.futures.Future:
        """Enqueue a task into a named lane."""
        lane = self.get_or_create_lane(lane_name)
        return lane.enqueue(fn)
    
    def reset_all(self) -> None:
        """Increment generation on all lanes for restart recovery."""
        with self._lock:
            for lane in self._lanes.values():
                lane.reset()
    
    def stats_all(self) -> List[LaneStats]:
        """Get statistics for all lanes."""
        with self._lock:
            return [lane.stats() for lane in self._lanes.values()]
    
    def wait_all_idle(self, timeout: Optional[float] = None) -> bool:
        """Wait for all lanes to become idle."""
        with self._lock:
            lanes = list(self._lanes.values())
        all_idle = True
        for lane in lanes:
            if not lane.wait_for_idle(timeout=timeout):
                all_idle = False
        return all_idle
    
    def clear_all(self) -> Dict[str, int]:
        """Clear all pending tasks in all lanes."""
        with self._lock:
            lanes = list(self._lanes.values())
        return {lane.name: lane.clear() for lane in lanes}
    
    def get_lane(self, name: str) -> Optional[LaneQueue]:
        """Get a lane by name (None if doesn't exist)."""
        with self._lock:
            return self._lanes.get(name)


LANE_MAIN = "main"
LANE_CRON = "cron"
LANE_HEARTBEAT = "heartbeat"
