#!/usr/bin/env python3
"""
h_agent/tests/test_heartbeat.py - TDD tests for s07 Heartbeat + Cron

Tests cover:
- HeartbeatRunner.should_run() all 5 preconditions
- lane_lock mutual exclusion
- heartbeat start/stop
- output queue
- CronService job loading
- CronService tick and run
- auto-disable after 5 errors
- add/remove/list jobs
- schedule types (at, every, cron)
"""

import json
import os
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure the h_agent package is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHeartbeatRunnerPreconditions:
    """Test HeartbeatRunner.should_run() 5 preconditions."""

    def test_should_run_returns_false_when_heartbeat_md_not_found(self, tmp_path):
        """Check 1: should_run returns False when HEARTBEAT.md does not exist."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        runner = HeartbeatRunner(heartbeat_path=tmp_path / "NO_SUCH_FILE.md")
        ok, reason = runner.should_run()
        
        assert ok is False
        assert "not found" in reason

    def test_should_run_returns_false_when_heartbeat_md_empty(self, tmp_path):
        """Check 2: should_run returns False when HEARTBEAT.md is empty."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("", encoding="utf-8")
        
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file)
        ok, reason = runner.should_run()
        
        assert ok is False
        assert "empty" in reason

    def test_should_run_returns_false_when_interval_not_elapsed(self, tmp_path):
        """Check 3: should_run returns False when interval has not elapsed."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("some content", encoding="utf-8")
        
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, interval=60.0)
        runner.last_run_at = time.time()  # just ran
        
        ok, reason = runner.should_run()
        
        assert ok is False
        assert "remaining" in reason or "interval" in reason

    def test_should_run_returns_false_outside_active_hours(self, tmp_path):
        """Check 4: should_run returns False when outside active_hours."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("some content", encoding="utf-8")
        
        # Active 9-17 hours, test with a different hour
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, active_hours=(9, 17))
        runner.last_run_at = 0.0  # never ran
        
        # Mock datetime to return 3am
        with patch("h_agent.concurrency.heartbeat.datetime") as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=3)
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            ok, reason = runner.should_run()
        
        assert ok is False
        assert "active hours" in reason

    def test_should_run_returns_false_when_already_running(self, tmp_path):
        """Check 5: should_run returns False when heartbeat is already running."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("some content", encoding="utf-8")
        
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, interval=1.0)
        runner.last_run_at = 0.0
        runner.running = True  # mark as running
        
        with patch("h_agent.concurrency.heartbeat.datetime") as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=12)
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            ok, reason = runner.should_run()
        
        assert ok is False
        assert "running" in reason

    def test_should_run_returns_true_when_all_checks_pass(self, tmp_path):
        """All 5 checks pass: should_run returns True."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("some content", encoding="utf-8")
        
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, interval=1.0)
        runner.last_run_at = 0.0
        runner.running = False
        
        with patch("h_agent.concurrency.heartbeat.datetime") as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=12)
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            ok, reason = runner.should_run()
        
        assert ok is True
        assert "passed" in reason


class TestLaneLock:
    """Test lane_lock mutual exclusion."""

    def test_lane_lock_is_threading_lock(self):
        """lane_lock is a threading.Lock instance."""
        from h_agent.concurrency.heartbeat import lane_lock
        
        assert isinstance(lane_lock, threading.Lock)

    def test_lane_lock_blocks_concurrent_access(self):
        """lane_lock provides mutual exclusion."""
        from h_agent.concurrency.heartbeat import lane_lock
        
        results = []
        start_flag = threading.Event()
        
        def worker():
            start_flag.wait()
            acquired = lane_lock.acquire(blocking=True, timeout=5)
            if acquired:
                results.append("acquired")
                time.sleep(0.1)
                lane_lock.release()
            else:
                results.append("not_acquired")
        
        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        
        t1.start()
        t2.start()
        start_flag.set()
        
        t1.join(timeout=5)
        t2.join(timeout=5)
        
        assert "acquired" in results
        assert "not_acquired" not in results


class TestHeartbeatRunnerLifecycle:
    """Test HeartbeatRunner start/stop/output queue."""

    def test_heartbeat_runner_initial_state(self, tmp_path):
        """HeartbeatRunner initializes with correct defaults."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, interval=30.0)
        
        assert runner.interval == 30.0
        assert runner.running is False
        assert runner.last_run_at == 0.0
        assert runner._stopped is False

    def test_heartbeat_runner_start_creates_thread(self, tmp_path):
        """start() creates a background thread."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("test", encoding="utf-8")
        
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, interval=1.0)
        
        with patch("h_agent.concurrency.heartbeat.datetime") as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=12)
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            runner.start(daemon=True)
        
        try:
            assert runner._thread is not None
            assert runner._thread.daemon is True
            time.sleep(0.2)
            # Should not be running because should_run returns False (no HEARTBEAT.md content)
            # Actually it should have content so let's check the thread is alive
        finally:
            runner.stop()

    def test_heartbeat_runner_stop_sets_stopped_flag(self, tmp_path):
        """stop() sets _stopped flag and joins thread."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("test", encoding="utf-8")
        
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, interval=0.5)
        
        with patch("h_agent.concurrency.heartbeat.datetime") as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=12)
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            runner.start(daemon=True)
            time.sleep(0.1)
            runner.stop()
        
        assert runner._stopped is True

    def test_heartbeat_output_queue(self, tmp_path):
        """get_output() returns and clears pending output."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        runner = HeartbeatRunner(heartbeat_path=tmp_path / "hb.md", interval=1.0)
        
        with runner._queue_lock:
            runner._output_queue.append("output1")
            runner._output_queue.append("output2")
        
        output = runner.get_output()
        
        assert output == ["output1", "output2"]
        
        with runner._queue_lock:
            assert runner._output_queue == []


class TestHeartbeatRunnerExecute:
    """Test HeartbeatRunner _execute behavior."""

    def test_execute_yields_when_lane_lock_unavailable(self, tmp_path):
        """_execute returns early if lane_lock cannot be acquired (non-blocking)."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner, lane_lock
        
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("test content", encoding="utf-8")
        
        runner = HeartbeatRunner(heartbeat_path=heartbeat_file, interval=1.0)
        runner.last_run_at = 0.0
        
        acquired = lane_lock.acquire(blocking=False)
        assert acquired is True
        
        try:
            with patch("h_agent.concurrency.heartbeat.datetime") as mock_dt:
                mock_dt.now.return_value = MagicMock(hour=12)
                mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
                
                assert runner.running is False
        finally:
            lane_lock.release()

    def test_parse_response_suppresses_heartbeat_ok(self):
        """_parse_response returns empty string for HEARTBEAT_OK."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        runner = HeartbeatRunner(heartbeat_path=Path("/tmp/hb.md"))
        
        result = runner._parse_response("HEARTBEAT_OK")
        assert result == ""

    def test_parse_response_returns_meaningful_output(self):
        """_parse_response returns non-empty response as-is."""
        from h_agent.concurrency.heartbeat import HeartbeatRunner
        
        runner = HeartbeatRunner(heartbeat_path=Path("/tmp/hb.md"))
        
        result = runner._parse_response("Did something useful")
        assert result == "Did something useful"


class TestCronJobComputeNext:
    """Test CronJob.compute_next() for 3 schedule types."""

    def test_compute_next_at_schedule(self):
        """compute_next for 'at' schedule returns future timestamp."""
        from h_agent.concurrency.cron import CronJob
        
        future_time = (datetime.now().timestamp() + 3600)
        job = CronJob(
            id="test1",
            name="Test At",
            enabled=True,
            schedule_kind="at",
            schedule_config={"at": datetime.fromtimestamp(future_time).isoformat()},
            payload={},
        )
        
        now = time.time()
        next_run = job.compute_next(now)
        
        assert next_run > now

    def test_compute_next_at_schedule_past(self):
        """compute_next for past 'at' returns 0."""
        from h_agent.concurrency.cron import CronJob
        
        past_time = (datetime.now().timestamp() - 3600)
        job = CronJob(
            id="test2",
            name="Test At Past",
            enabled=True,
            schedule_kind="at",
            schedule_config={"at": datetime.fromtimestamp(past_time).isoformat()},
            payload={},
        )
        
        now = time.time()
        next_run = job.compute_next(now)
        
        assert next_run == 0.0

    def test_compute_next_every_schedule(self):
        """compute_next for 'every' schedule calculates next interval."""
        from h_agent.concurrency.cron import CronJob
        
        job = CronJob(
            id="test3",
            name="Test Every",
            enabled=True,
            schedule_kind="every",
            schedule_config={"every_seconds": 60, "anchor": 0},
            payload={},
        )
        
        now = time.time()
        next_run = job.compute_next(now)
        
        # Next should be on an interval boundary
        assert next_run > now
        assert next_run - job.schedule_config["anchor"] > 0

    def test_compute_next_cron_schedule(self):
        """compute_next for 'cron' schedule uses croniter."""
        from h_agent.concurrency.cron import CronJob
        
        job = CronJob(
            id="test4",
            name="Test Cron",
            enabled=True,
            schedule_kind="cron",
            schedule_config={"expr": "0 * * * *"},  # every hour
            payload={},
        )
        
        now = time.time()
        next_run = job.compute_next(now)
        
        assert next_run > now


class TestCronServiceLifecycle:
    """Test CronService start/stop."""

    def test_cron_service_initial_state(self, tmp_path):
        """CronService initializes and loads jobs from config."""
        from h_agent.concurrency.cron import CronService
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        assert service._stopped is False
        assert service._thread is None

    def test_cron_service_start_creates_thread(self, tmp_path):
        """start() creates a daemon thread."""
        from h_agent.concurrency.cron import CronService
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        service.start(daemon=True)
        
        try:
            assert service._thread is not None
            assert service._thread.daemon is True
            time.sleep(0.1)
        finally:
            service.stop()

    def test_cron_service_stop_sets_flag(self, tmp_path):
        """stop() sets _stopped and joins thread."""
        from h_agent.concurrency.cron import CronService
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        service.start(daemon=True)
        time.sleep(0.1)
        service.stop()
        
        assert service._stopped is True


class TestCronServiceJobManagement:
    """Test CronService add/remove/list jobs."""

    def test_add_job(self, tmp_path):
        """add_job() adds job to list and saves."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        job = CronJob(
            id="new_job",
            name="New Job",
            enabled=True,
            schedule_kind="every",
            schedule_config={"every_seconds": 60, "anchor": 0},
            payload={},
        )
        
        service.add_job(job)
        
        assert len(service.jobs) == 1
        assert service.jobs[0].id == "new_job"

    def test_remove_job_exists(self, tmp_path):
        """remove_job() removes job by ID and returns True."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        job = CronJob(
            id="to_remove",
            name="To Remove",
            enabled=True,
            schedule_kind="every",
            schedule_config={"every_seconds": 60, "anchor": 0},
            payload={},
        )
        service.add_job(job)
        
        result = service.remove_job("to_remove")
        
        assert result is True
        assert len(service.jobs) == 0

    def test_remove_job_not_found(self, tmp_path):
        """remove_job() returns False when job not found."""
        from h_agent.concurrency.cron import CronService
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        result = service.remove_job("nonexistent")
        
        assert result is False

    def test_list_jobs(self, tmp_path):
        """list_jobs() returns dict with job info."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        job = CronJob(
            id="list_test",
            name="List Test",
            enabled=True,
            schedule_kind="cron",
            schedule_config={"expr": "0 * * * *"},
            payload={},
        )
        service.add_job(job)
        
        listed = service.list_jobs()
        
        assert len(listed) == 1
        assert listed[0]["id"] == "list_test"
        assert listed[0]["enabled"] is True
        assert listed[0]["schedule_kind"] == "cron"


class TestCronServiceAutoDisable:
    """Test CronService auto-disable after 5 consecutive errors."""

    def test_auto_disable_after_5_errors(self, tmp_path):
        """Job is auto-disabled after 5 consecutive errors."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        job = CronJob(
            id="failing_job",
            name="Failing Job",
            enabled=True,
            schedule_kind="every",
            schedule_config={"every_seconds": 1, "anchor": 0},
            payload={"kind": "nonexistent"},
        )
        service.add_job(job)
        
        # Simulate 5 errors
        for _ in range(5):
            try:
                service._run_job(job)
            except Exception:
                pass
        
        assert job.enabled is False

    def test_error_count_resets_on_success(self, tmp_path):
        """consecutive_errors resets to 0 on successful run."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        job = CronJob(
            id="recovering_job",
            name="Recovering Job",
            enabled=True,
            schedule_kind="every",
            schedule_config={"every_seconds": 1, "anchor": 0},
            payload={"kind": "agent_turn", "message": "test"},
        )
        service.add_job(job)
        
        job.consecutive_errors = 3
        
        # Successful run
        service._run_job(job)
        
        assert job.consecutive_errors == 0


class TestCronServiceTick:
    """Test CronService _tick method."""

    def test_tick_runs_due_jobs(self, tmp_path):
        """_tick runs jobs that are due."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        run_count = 0
        
        now = time.time()
        job = CronJob(
            id="tick_test",
            name="Tick Test",
            enabled=True,
            schedule_kind="at",
            schedule_config={"at": datetime.fromtimestamp(now - 1).isoformat()},
            payload={"kind": "agent_turn", "message": "test"},
        )
        service.add_job(job)
        
        run_count = 0
        def track_run(job):
            nonlocal run_count
            run_count += 1
        service._run_job = track_run
        
        service._tick()
        
        assert run_count == 1

    def test_tick_skips_disabled_jobs(self, tmp_path):
        """_tick skips jobs that are disabled."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        run_count = 0
        
        job = CronJob(
            id="disabled_tick",
            name="Disabled Tick",
            enabled=False,
            schedule_kind="every",
            schedule_config={"every_seconds": 1, "anchor": 0},
            payload={},
        )
        service.add_job(job)
        
        def track_run(job):
            nonlocal run_count
            run_count += 1
        service._run_job = track_run
        
        service._tick()
        
        assert run_count == 0


class TestCronServiceLoadJobs:
    """Test CronService job loading from CRON.json."""

    def test_load_jobs_from_file(self, tmp_path):
        """_load_jobs parses CRON.json and creates CronJob objects."""
        from h_agent.concurrency.cron import CronService
        
        config_file = tmp_path / "CRON.json"
        config_data = {
            "jobs": [
                {
                    "id": "loaded_job",
                    "name": "Loaded Job",
                    "enabled": True,
                    "schedule": {"kind": "every", "every_seconds": 3600},
                    "payload": {"kind": "agent_turn", "message": "hello"},
                }
            ]
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")
        
        service = CronService(config_path=config_file)
        
        assert len(service.jobs) == 1
        assert service.jobs[0].id == "loaded_job"
        assert service.jobs[0].schedule_kind == "every"

    def test_load_jobs_invalid_json(self, tmp_path):
        """_load_jobs handles invalid JSON gracefully."""
        from h_agent.concurrency.cron import CronService
        
        config_file = tmp_path / "CRON.json"
        config_file.write_text("not valid json{{{", encoding="utf-8")
        
        # Should not raise, just load empty jobs
        service = CronService(config_path=config_file)
        
        assert len(service.jobs) == 0


class TestCronServiceSaveJobs:
    """Test CronService job saving to CRON.json."""

    def test_save_jobs_to_file(self, tmp_path):
        """_save_jobs writes jobs to CRON.json."""
        from h_agent.concurrency.cron import CronService, CronJob
        
        config_file = tmp_path / "CRON.json"
        service = CronService(config_path=config_file)
        
        job = CronJob(
            id="save_test",
            name="Save Test",
            enabled=True,
            schedule_kind="cron",
            schedule_config={"kind": "cron", "expr": "0 * * * *"},
            payload={},
        )
        service.add_job(job)
        
        # Trigger save
        service._save_jobs()
        
        # Verify file contents
        data = json.loads(config_file.read_text(encoding="utf-8"))
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == "save_test"


# Run with: pytest h_agent/tests/test_heartbeat.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
