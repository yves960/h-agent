"""
h_agent/concurrency/__init__.py - Named lane concurrency module.

Provides:
- LaneQueue: a named FIFO queue with max_concurrency control
- CommandQueue: central dispatcher routing work to named lanes
- HeartbeatRunner: Background heartbeat with lane mutual exclusion
- CronService: Cron service with 3 schedule types, auto-disable after 5 errors
- CronJob: Scheduled job definition

Usage:
    from h_agent.concurrency import HeartbeatRunner, CronService, CronJob, lane_lock

    runner = HeartbeatRunner(heartbeat_path=Path("HEARTBEAT.md"))
    runner.start()

    service = CronService()
    service.start()
"""

from h_agent.concurrency.lanes import (
    LaneQueue,
    CommandQueue,
    LaneStats,
    LANE_MAIN,
    LANE_CRON,
    LANE_HEARTBEAT,
)
from h_agent.concurrency.heartbeat import HeartbeatRunner, lane_lock
from h_agent.concurrency.cron import CronService, CronJob

__all__ = [
    "LaneQueue",
    "CommandQueue",
    "LaneStats",
    "LANE_MAIN",
    "LANE_CRON",
    "LANE_HEARTBEAT",
    "HeartbeatRunner",
    "CronService",
    "CronJob",
    "lane_lock",
]
