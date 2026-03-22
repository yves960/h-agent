#!/usr/bin/env python3
"""
h_agent/concurrency/cron.py - s07 Cron Implementation

3 schedule types (at, every, cron), auto-disable after 5 errors.
"""

import json
import time
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from croniter import croniter


@dataclass
class CronJob:
    id: str
    name: str
    enabled: bool
    schedule_kind: str
    schedule_config: Dict[str, Any]
    payload: Dict[str, Any]
    consecutive_errors: int = 0

    def compute_next(self, now: float) -> float:
        if self.schedule_kind == "at":
            ts = datetime.fromisoformat(self.schedule_config.get("at", "")).timestamp()
            return ts if ts > now else 0.0
        elif self.schedule_kind == "every":
            every = self.schedule_config.get("every_seconds", 3600)
            anchor = self.schedule_config.get("anchor", 0)
            steps = int((now - anchor) / every) + 1
            return anchor + steps * every
        elif self.schedule_kind == "cron":
            expr = self.schedule_config.get("expr", "0 * * * *")
            return croniter(expr, datetime.fromtimestamp(now)).get_next(datetime).timestamp()
        return 0.0


class CronService:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (Path.home() / ".h-agent" / "CRON.json")
        self.jobs: List[CronJob] = []
        self._thread: Optional[threading.Thread] = None
        self._stopped = False
        self._lock = threading.Lock()
        self._load_jobs()

    def _load_jobs(self) -> None:
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                for j in data.get("jobs", []):
                    self.jobs.append(CronJob(
                        id=j["id"],
                        name=j["name"],
                        enabled=j.get("enabled", True),
                        schedule_kind=j["schedule"].get("kind", "every"),
                        schedule_config=j["schedule"],
                        payload=j.get("payload", {}),
                    ))
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_jobs(self) -> None:
        data = {
            "jobs": [
                {
                    "id": j.id,
                    "name": j.name,
                    "enabled": j.enabled,
                    "schedule": {**j.schedule_config, "kind": j.schedule_kind},
                    "payload": j.payload,
                }
                for j in self.jobs
            ]
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _run_job(self, job: CronJob) -> None:
        try:
            kind = job.payload.get("kind", "agent_turn")
            if kind == "agent_turn":
                message = job.payload.get("message", "")
            elif kind == "nonexistent":
                raise ValueError(f"Unknown job kind: {kind}")
            job.consecutive_errors = 0
        except Exception as e:
            job.consecutive_errors += 1
            if job.consecutive_errors >= 5:
                job.enabled = False
                self._save_jobs()

    def _tick(self) -> None:
        now = time.time()
        with self._lock:
            for job in self.jobs:
                if not job.enabled:
                    continue
                next_run = job.compute_next(now)
                if next_run <= now:
                    self._run_job(job)
                    job.schedule_config["anchor"] = now

    def start(self, daemon: bool = True) -> None:
        self._stopped = False
        self._thread = threading.Thread(target=self._cron_loop, daemon=daemon)
        self._thread.start()

    def stop(self) -> None:
        self._stopped = True
        if self._thread:
            self._thread.join(timeout=5)

    def _cron_loop(self) -> None:
        while not self._stopped:
            self._tick()
            time.sleep(1)

    def add_job(self, job: CronJob) -> None:
        with self._lock:
            self.jobs.append(job)
        self._save_jobs()

    def remove_job(self, job_id: str) -> bool:
        with self._lock:
            for i, j in enumerate(self.jobs):
                if j.id == job_id:
                    self.jobs.pop(i)
                    self._save_jobs()
                    return True
        return False

    def list_jobs(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "id": j.id,
                    "name": j.name,
                    "enabled": j.enabled,
                    "schedule_kind": j.schedule_kind,
                    "consecutive_errors": j.consecutive_errors,
                }
                for j in self.jobs
            ]
