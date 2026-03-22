#!/usr/bin/env python3
"""
h_agent/delivery/queue.py - s08 DeliveryQueue Implementation

Write-ahead queue with atomic writes (tmp + fsync + os.replace).
"""

import json
import os
import random
import uuid
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

QUEUE_DIR = Path.home() / ".h-agent" / "delivery"
MAX_RETRIES = 5
BACKOFF_MS = [5_000, 25_000, 120_000, 600_000]

@dataclass
class QueuedDelivery:
    """A queued delivery entry."""
    id: str
    channel: str
    to: str
    text: str
    enqueued_at: float
    next_retry_at: float = 0.0
    retry_count: int = 0
    last_error: str = ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "to": self.to,
            "text": self.text,
            "enqueued_at": self.enqueued_at,
            "next_retry_at": self.next_retry_at,
            "retry_count": self.retry_count,
            "last_error": self.last_error,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "QueuedDelivery":
        return cls(
            id=d["id"],
            channel=d["channel"],
            to=d["to"],
            text=d["text"],
            enqueued_at=d["enqueued_at"],
            next_retry_at=d.get("next_retry_at", 0.0),
            retry_count=d.get("retry_count", 0),
            last_error=d.get("last_error", ""),
        )

def compute_backoff_ms(retry_count: int) -> int:
    """Exponential backoff with +/- 20% jitter."""
    if retry_count <= 0:
        return 0
    idx = min(retry_count - 1, len(BACKOFF_MS) - 1)
    base = BACKOFF_MS[idx]
    jitter = random.randint(-base // 5, base // 5)
    return max(0, base + jitter)

class DeliveryQueue:
    """
    Disk-persisted write-ahead queue.
    Enqueue writes to disk before attempting delivery.
    """
    
    def __init__(self, queue_dir: Optional[Path] = None):
        self.queue_dir = queue_dir or QUEUE_DIR
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir = self.queue_dir / "failed"
        self.failed_dir.mkdir(exist_ok=True)
    
    def enqueue(self, channel: str, to: str, text: str) -> str:
        """Enqueue a delivery - atomic write to disk first."""
        delivery_id = uuid.uuid4().hex[:12]
        entry = QueuedDelivery(
            id=delivery_id,
            channel=channel,
            to=to,
            text=text,
            enqueued_at=time.time(),
            next_retry_at=0.0,
        )
        self._write_entry(entry)
        return delivery_id
    
    def _write_entry(self, entry: QueuedDelivery) -> None:
        """Atomic write: tmp + fsync + os.replace."""
        final_path = self.queue_dir / f"{entry.id}.json"
        tmp_path = self.queue_dir / f".tmp.{os.getpid()}.{entry.id}.json"
        
        data = json.dumps(entry.to_dict(), indent=2, ensure_ascii=False)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        
        os.replace(str(tmp_path), str(final_path))
    
    def _read_entry(self, delivery_id: str) -> Optional[QueuedDelivery]:
        """Read a queue entry from disk."""
        path = self.queue_dir / f"{delivery_id}.json"
        if not path.exists():
            return None
        try:
            return QueuedDelivery.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError):
            return None
    
    def ack(self, delivery_id: str) -> bool:
        """Delivery succeeded - delete the queue file."""
        path = self.queue_dir / f"{delivery_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False
    
    def fail(self, delivery_id: str, error: str) -> None:
        """Increment retry_count, compute next retry time, or give up."""
        entry = self._read_entry(delivery_id)
        if not entry:
            return
        
        entry.retry_count += 1
        entry.last_error = error
        
        if entry.retry_count >= MAX_RETRIES:
            self.move_to_failed(delivery_id)
            return
        
        entry.next_retry_at = time.time()
        self._write_entry(entry)
    
    def move_to_failed(self, delivery_id: str) -> None:
        """Move to failed directory after max retries."""
        src = self.queue_dir / f"{delivery_id}.json"
        dst = self.failed_dir / f"{delivery_id}.json"
        if src.exists():
            src.rename(dst)
    
    def load_pending(self) -> List[QueuedDelivery]:
        """Load all pending (not yet delivered) entries."""
        entries = []
        for path in self.queue_dir.glob("*.json"):
            try:
                entry = QueuedDelivery.from_dict(json.loads(path.read_text(encoding="utf-8")))
                entries.append(entry)
            except (json.JSONDecodeError, KeyError):
                pass
        return sorted(entries, key=lambda e: e.enqueued_at)
    
    def load_failed(self) -> List[QueuedDelivery]:
        """Load all failed entries."""
        entries = []
        for path in self.failed_dir.glob("*.json"):
            try:
                entry = QueuedDelivery.from_dict(json.loads(path.read_text(encoding="utf-8")))
                entries.append(entry)
            except (json.JSONDecodeError, KeyError):
                pass
        return sorted(entries, key=lambda e: e.enqueued_at)
    
    def _recovery_scan(self) -> int:
        """On startup, retry pending entries from a previous crash."""
        count = 0
        for path in self.queue_dir.glob("*.json"):
            try:
                entry = QueuedDelivery.from_dict(json.loads(path.read_text(encoding="utf-8")))
                if entry.next_retry_at > time.time():
                    continue
                count += 1
            except (json.JSONDecodeError, KeyError):
                pass
        return count