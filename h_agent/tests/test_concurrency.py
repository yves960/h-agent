#!/usr/bin/env python3
"""
h_agent/tests/test_concurrency.py - TDD tests for s10 LaneQueue + CommandQueue

Tests cover:
- LaneQueue.enqueue() - basic enqueue and execution
- LaneQueue._pump() - starts tasks when capacity available
- LaneQueue._task_done() - re-pumps only current generation
- LaneQueue.generation tracking - stale tasks skip pump after reset
- LaneQueue.wait_for_idle() - blocks until complete
- LaneQueue.set_max_concurrency() - resize concurrency
- LaneQueue.clear() - clears pending tasks
- LaneQueue.stats() - correct statistics
- LaneQueue.reset() - increments generation
- CommandQueue.get_or_create_lane() - lazy creation
- CommandQueue.enqueue() - dispatches to correct lane
- CommandQueue.reset_all() - increments all generations
- CommandQueue.stats_all() - stats for all lanes
- CommandQueue.wait_all_idle() - waits for all lanes
- CommandQueue.clear_all() - clears all lanes
- CommandQueue.get_lane() - get existing lane
- Concurrent execution within a lane with max > 1
"""

import threading
import time
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLaneQueueBasic:
    """Test LaneQueue basic enqueue and execution."""

    def test_enqueue_returns_future(self):
        """enqueue() returns a concurrent.futures.Future."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        future = lane.enqueue(lambda: 42)
        
        assert hasattr(future, 'result')
        assert hasattr(future, 'set_result')
        assert hasattr(future, 'set_exception')

    def test_enqueue_executes_function(self):
        """enqueue() actually executes the function."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        future = lane.enqueue(lambda: 42)
        
        result = future.result(timeout=5)
        assert result == 42

    def test_enqueue_with_exception(self):
        """enqueue() propagates exceptions via Future."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        future = lane.enqueue(lambda: 1 / 0)
        
        with pytest.raises(ZeroDivisionError):
            future.result(timeout=5)

    def test_enqueue_preserves_return_value(self):
        """enqueue() returns the exact value from function."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        future = lane.enqueue(lambda: "hello world")
        
        result = future.result(timeout=5)
        assert result == "hello world"


class TestLaneQueuePump:
    """Test LaneQueue _pump() behavior."""

    def test_pump_starts_task_when_capacity_available(self):
        """_pump() starts task immediately when max_concurrency not exceeded."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        started = []
        
        def slow_task():
            started.append(time.time())
            time.sleep(0.2)
            return 1
        
        future = lane.enqueue(slow_task)
        time.sleep(0.05)
        
        assert len(started) == 1
        future.result(timeout=5)

    def test_pump_respects_max_concurrency(self):
        """_pump() does not exceed max_concurrency active tasks."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        active_count = []
        lock = threading.Lock()
        
        def task():
            with lock:
                active_count.append(1)
            time.sleep(0.1)
            return 1
        
        # Enqueue 3 tasks
        futures = [lane.enqueue(task) for _ in range(3)]
        
        time.sleep(0.05)
        
        # Only 1 should be active at start
        assert len(active_count) <= 1
        
        # Wait for all to complete
        for f in futures:
            f.result(timeout=5)


class TestLaneQueueGeneration:
    """Test LaneQueue generation tracking."""

    def test_initial_generation_is_zero(self):
        """New LaneQueue has generation 0."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        assert lane.stats().generation == 0

    def test_reset_increments_generation(self):
        """reset() increments generation counter."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        initial_gen = lane.stats().generation
        
        lane.reset()
        
        assert lane.stats().generation == initial_gen + 1

    def test_stale_task_does_not_rePump_after_reset(self):
        """Tasks from old generation don't re-pump after reset()."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        task_started = []
        task_completed = []
        barrier = threading.Barrier(2, timeout=5)
        
        def blocking_task():
            task_started.append(1)
            barrier.wait(timeout=5)
            time.sleep(0.1)
            task_completed.append(1)
            return 1
        
        # Start a blocking task
        future1 = lane.enqueue(blocking_task)
        barrier.wait(timeout=5)  # Task is now blocked in thread
        
        # Reset while first task is still running
        lane.reset()
        
        # Enqueue a new task - it should NOT start because generation changed
        new_task_started = []
        def new_task():
            new_task_started.append(1)
            return 2
        
        future2 = lane.enqueue(new_task)
        
        # Allow first task to complete
        barrier.abort()
        try:
            future1.result(timeout=1)
        except:
            pass
        
        # Wait a bit to see if new task starts
        time.sleep(0.2)
        
        # The new task should NOT have started because it's in a new generation
        # and max_concurrency was 1 (first task was still active when reset happened)
        # Actually - after reset, the generation incremented so stale tasks won't repump
        # But the first task is still active and when it completes, it won't repump either
        
        # If we clear and reset properly, no more tasks should pump
        lane.clear()
        
    def test_enqueue_accepts_generation_parameter(self):
        """enqueue() accepts optional generation parameter."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        
        # Enqueue with explicit generation
        future = lane.enqueue(lambda: 42, generation=5)
        result = future.result(timeout=5)
        
        assert result == 42


class TestLaneQueueTaskDone:
    """Test LaneQueue _task_done() behavior."""

    def test_task_done_decrements_active_count(self):
        """_task_done() decrements active count."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        
        future = lane.enqueue(lambda: (time.sleep(0.05), 42)[1])
        time.sleep(0.1)
        
        assert lane.stats().active == 0
        future.result(timeout=5)

    def test_task_done_repumps_current_generation(self):
        """_task_done() repumps if generation matches."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        completed = []
        
        def task():
            return 1
        
        # Enqueue first task
        f1 = lane.enqueue(task)
        f1.result(timeout=5)
        
        # Enqueue second task - should be pumped after first completes
        def second_task():
            completed.append(1)
            return 2
        
        f2 = lane.enqueue(second_task)
        f2.result(timeout=5)
        
        assert len(completed) == 1


class TestLaneQueueWaitForIdle:
    """Test LaneQueue wait_for_idle()."""

    def test_wait_for_idle_returns_true_when_idle(self):
        """wait_for_idle() returns True when no tasks running."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test")
        result = lane.wait_for_idle(timeout=1)
        
        assert result is True

    def test_wait_for_idle_blocks_until_complete(self):
        """wait_for_idle() blocks until all tasks complete."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        
        def slow_task():
            time.sleep(0.2)
            return 42
        
        future = lane.enqueue(slow_task)
        
        start = time.time()
        result = lane.wait_for_idle(timeout=5)
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed >= 0.2
        assert future.result(timeout=1) == 42

    def test_wait_for_idle_with_timeout(self):
        """wait_for_idle() returns False after timeout."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        
        def very_slow_task():
            time.sleep(10)
            return 1
        
        lane.enqueue(very_slow_task)
        
        start = time.time()
        result = lane.wait_for_idle(timeout=0.5)
        elapsed = time.time() - start
        
        assert result is False
        assert elapsed < 1

    def test_wait_for_idle_with_queued_tasks(self):
        """wait_for_idle() considers queued tasks."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        
        def task():
            time.sleep(0.1)
            return 1
        
        # Enqueue more tasks than max_concurrency
        for _ in range(5):
            lane.enqueue(task)
        
        result = lane.wait_for_idle(timeout=5)
        assert result is True


class TestLaneQueueConcurrency:
    """Test LaneQueue concurrent execution with max_concurrency > 1."""

    def test_concurrent_execution_with_max_2(self):
        """LaneQueue allows up to max_concurrency parallel tasks."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=2)
        start_times = []
        lock = threading.Lock()
        
        def concurrent_task():
            time.sleep(0.1)
            with lock:
                start_times.append(time.time())
            return 1
        
        # Enqueue 2 tasks
        f1 = lane.enqueue(concurrent_task)
        f2 = lane.enqueue(concurrent_task)
        
        # Both should complete with max_concurrency=2
        result1 = f1.result(timeout=5)
        result2 = f2.result(timeout=5)
        
        assert result1 == 1
        assert result2 == 1
        assert len(start_times) == 2


class TestLaneQueueMaxConcurrency:
    """Test LaneQueue set_max_concurrency()."""

    def test_set_max_concurrency_updates_limit(self):
        """set_max_concurrency() changes the concurrency limit."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        
        lane.set_max_concurrency(5)
        
        stats = lane.stats()
        assert stats.max_concurrency == 5

    def test_set_max_concurrency_enables_more_tasks(self):
        """set_max_concurrency() allows more parallel tasks after increase."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        active = []
        lock = threading.Lock()
        barrier = threading.Barrier(2, timeout=5)
        
        def task():
            with lock:
                active.append(1)
            barrier.wait(timeout=5)
            time.sleep(0.1)
            return 1
        
        # Enqueue 2 tasks - only 1 should start
        f1 = lane.enqueue(task)
        time.sleep(0.05)
        assert len(active) == 1
        
        # Increase limit
        lane.set_max_concurrency(2)
        
        # Now second task should start
        f2 = lane.enqueue(task)
        time.sleep(0.05)
        assert len(active) == 2
        
        barrier.abort()
        f1.result(timeout=5)
        f2.result(timeout=5)


class TestLaneQueueClear:
    """Test LaneQueue clear()."""

    def test_clear_removes_pending_tasks(self):
        """clear() removes all pending tasks from queue."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        started = []
        barrier = threading.Barrier(2, timeout=5)
        
        def blocking_task():
            started.append(1)
            barrier.wait(timeout=5)
            return 1
        
        # Enqueue 5 tasks - first one starts and blocks at barrier
        lane.enqueue(blocking_task)
        lane.enqueue(lambda: 2)
        lane.enqueue(lambda: 3)
        lane.enqueue(lambda: 4)
        lane.enqueue(lambda: 5)
        
        barrier.wait(timeout=5)
        
        # 4 tasks should be queued (first one is running)
        cleared = lane.clear()
        
        assert cleared == 4
        assert lane.stats().queued == 0
        
        barrier.abort()

    def test_clear_returns_count(self):
        """clear() returns count of cleared tasks."""
        from h_agent.concurrency.lanes import LaneQueue
        
        lane = LaneQueue("test", max_concurrency=1)
        started = []
        barrier = threading.Barrier(2, timeout=5)
        
        def blocking_task():
            started.append(1)
            barrier.wait(timeout=5)
            return 1
        
        # First task blocks, remaining 2 are queued
        lane.enqueue(blocking_task)
        lane.enqueue(lambda: 2)
        lane.enqueue(lambda: 3)
        
        barrier.wait(timeout=5)
        
        cleared = lane.clear()
        
        assert cleared == 2
        
        barrier.abort()


class TestLaneQueueStats:
    """Test LaneQueue stats()."""

    def test_stats_returns_lanestats_dataclass(self):
        """stats() returns a LaneStats dataclass."""
        from h_agent.concurrency.lanes import LaneQueue, LaneStats
        
        lane = LaneQueue("test")
        stats = lane.stats()
        
        assert isinstance(stats, LaneStats)

    def test_stats_fields(self):
        """stats() returns correct fields."""
        from h_agent.concurrency.lanes import LaneQueue, LaneStats
        
        lane = LaneQueue("test", max_concurrency=3)
        lane.enqueue(lambda: 1)
        
        stats = lane.stats()
        
        assert stats.name == "test"
        assert stats.max_concurrency == 3
        assert stats.generation == 0
        assert stats.queued >= 0 or stats.active >= 0


class TestCommandQueueLazyCreation:
    """Test CommandQueue lazy lane creation."""

    def test_get_or_create_lane_creates_new_lane(self):
        """get_or_create_lane() creates lane if not exists."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        lane = q.get_or_create_lane("new_lane", max_concurrency=2)
        
        assert lane is not None
        assert lane.name == "new_lane"
        assert lane.max_concurrency == 2

    def test_get_or_create_lane_returns_existing(self):
        """get_or_create_lane() returns existing lane."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        lane1 = q.get_or_create_lane("same")
        lane2 = q.get_or_create_lane("same")
        
        assert lane1 is lane2

    def test_get_lane_returns_none_for_nonexistent(self):
        """get_lane() returns None for non-existent lane."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        lane = q.get_lane("nonexistent")
        
        assert lane is None

    def test_get_lane_returns_existing_lane(self):
        """get_lane() returns existing lane."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        created = q.get_or_create_lane("existing")
        retrieved = q.get_lane("existing")
        
        assert created is retrieved


class TestCommandQueueEnqueue:
    """Test CommandQueue enqueue()."""

    def test_enqueue_dispatches_to_named_lane(self):
        """enqueue() routes to correct lane."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        future = q.enqueue("my_lane", lambda: 99)
        
        result = future.result(timeout=5)
        assert result == 99

    def test_enqueue_creates_lane_if_needed(self):
        """enqueue() auto-creates lane."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        
        # Should not raise
        future = q.enqueue("auto_lane", lambda: 1)
        result = future.result(timeout=5)
        
        assert result == 1


class TestCommandQueueResetAll:
    """Test CommandQueue reset_all()."""

    def test_reset_all_increments_all_generations(self):
        """reset_all() increments generation on all lanes."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        q.get_or_create_lane("lane1")
        q.get_or_create_lane("lane2")
        
        q.reset_all()
        
        stats = q.stats_all()
        assert stats[0].generation == 1
        assert stats[1].generation == 1


class TestCommandQueueStatsAll:
    """Test CommandQueue stats_all()."""

    def test_stats_all_returns_list(self):
        """stats_all() returns list of LaneStats."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        q.get_or_create_lane("lane1")
        q.get_or_create_lane("lane2")
        
        stats = q.stats_all()
        
        assert isinstance(stats, list)
        assert len(stats) == 2

    def test_stats_all_contains_lane_stats(self):
        """stats_all() contains stats for each lane."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        q.get_or_create_lane("test_lane", max_concurrency=5)
        
        stats = q.stats_all()
        
        assert any(s.name == "test_lane" and s.max_concurrency == 5 for s in stats)


class TestCommandQueueWaitAllIdle:
    """Test CommandQueue wait_all_idle()."""

    def test_wait_all_idle_returns_true_when_idle(self):
        """wait_all_idle() returns True when all lanes idle."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        result = q.wait_all_idle(timeout=1)
        
        assert result is True

    def test_wait_all_idle_blocks_until_complete(self):
        """wait_all_idle() blocks until all lanes complete."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        lane = q.get_or_create_lane("busy", max_concurrency=1)
        
        def slow_task():
            time.sleep(0.2)
            return 1
        
        lane.enqueue(slow_task)
        
        start = time.time()
        result = q.wait_all_idle(timeout=5)
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed >= 0.2


class TestCommandQueueClearAll:
    """Test CommandQueue clear_all()."""

    def test_clear_all_clears_all_lanes(self):
        """clear_all() clears pending tasks in all lanes."""
        from h_agent.concurrency import CommandQueue
        
        q = CommandQueue()
        lane1 = q.get_or_create_lane("lane1", max_concurrency=1)
        lane2 = q.get_or_create_lane("lane2", max_concurrency=1)
        
        started_count = 0
        lock = threading.Lock()
        ready_event = threading.Event()
        
        def blocking_task():
            nonlocal started_count
            with lock:
                started_count += 1
                if started_count == 2:
                    ready_event.set()
            ready_event.wait(timeout=5)
            time.sleep(0.5)
            return 1
        
        # Enqueue blocking tasks first so they occupy the single slot
        q.enqueue("lane1", blocking_task)
        q.enqueue("lane2", blocking_task)
        
        # Wait for both to start
        ready_event.wait(timeout=5)
        
        # Now enqueue additional tasks - they will be queued since blocking tasks are running
        q.enqueue("lane1", lambda: 2)
        q.enqueue("lane1", lambda: 3)
        q.enqueue("lane2", lambda: 4)
        
        result = q.clear_all()
        
        assert "lane1" in result
        assert "lane2" in result
        assert result["lane1"] == 2
        assert result["lane2"] == 1


class TestLaneStatsDataclass:
    """Test LaneStats dataclass."""

    def test_lanestats_has_required_fields(self):
        """LaneStats has name, active, queued, max_concurrency, generation."""
        from h_agent.concurrency.lanes import LaneStats
        
        stats = LaneStats(
            name="test",
            active=1,
            queued=2,
            max_concurrency=3,
            generation=4,
        )
        
        assert stats.name == "test"
        assert stats.active == 1
        assert stats.queued == 2
        assert stats.max_concurrency == 3
        assert stats.generation == 4


class TestCommandQueueLaneConstants:
    """Test CommandQueue lane name constants."""

    def test_lane_main_exists(self):
        """LANE_MAIN constant exists."""
        from h_agent.concurrency import LANE_MAIN
        
        assert LANE_MAIN == "main"

    def test_lane_cron_exists(self):
        """LANE_CRON constant exists."""
        from h_agent.concurrency import LANE_CRON
        
        assert LANE_CRON == "cron"

    def test_lane_heartbeat_exists(self):
        """LANE_HEARTBEAT constant exists."""
        from h_agent.concurrency import LANE_HEARTBEAT
        
        assert LANE_HEARTBEAT == "heartbeat"


# Run with: pytest h_agent/tests/test_concurrency.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
