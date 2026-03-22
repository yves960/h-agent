#!/usr/bin/env python3
"""
h_agent/delivery/runner.py - s08 DeliveryRunner Implementation

Background thread that processes pending entries with exponential backoff.
"""

import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, List
from h_agent.delivery.queue import DeliveryQueue, QueuedDelivery, MAX_RETRIES

class DeliveryRunner:
    """
    Background thread that processes pending deliveries.
    Runs recovery scan on startup for crash survival.
    """
    
    def __init__(
        self,
        queue: Optional[DeliveryQueue] = None,
        deliver_fn: Optional[Callable[[str, str, str], None]] = None,
    ):
        self.queue = queue or DeliveryQueue()
        self.deliver_fn = deliver_fn or self._default_deliver
        self._thread: Optional[threading.Thread] = None
        self._stopped = False
        self.total_attempted = 0
        self.total_succeeded = 0
        self.total_failed = 0
    
    def _default_deliver(self, channel: str, to: str, text: str) -> None:
        """Default deliver function - raises NotImplementedError."""
        raise NotImplementedError(f"No deliver_fn provided for {channel} -> {to}")
    
    def _process_pending(self) -> None:
        """Process all pending entries whose next_retry_at has passed."""
        pending = self.queue.load_pending()
        now = time.time()
        
        for entry in pending:
            if entry.next_retry_at > now:
                continue
            
            self.total_attempted += 1
            try:
                self.deliver_fn(entry.channel, entry.to, entry.text)
                self.queue.ack(entry.id)
                self.total_succeeded += 1
            except Exception as exc:
                self.queue.fail(entry.id, str(exc))
                self.total_failed += 1
    
    def _recovery_scan(self) -> int:
        """On startup, count pending entries from a previous crash."""
        return self.queue._recovery_scan()
    
    def start(self, daemon: bool = True) -> None:
        """Start the delivery background thread."""
        self._recovery_scan()
        self._stopped = False
        self._thread = threading.Thread(target=self._background_loop, daemon=daemon)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the delivery thread."""
        self._stopped = True
        if self._thread:
            self._thread.join(timeout=5)
    
    def _background_loop(self) -> None:
        """Main loop - scan pending entries every second."""
        while not self._stopped:
            self._process_pending()
            time.sleep(1)
    
    def get_stats(self) -> Dict:
        """Get delivery statistics."""
        return {
            "attempted": self.total_attempted,
            "succeeded": self.total_succeeded,
            "failed": self.total_failed,
            "pending": len(self.queue.load_pending()),
            "failed_count": len(self.queue.load_failed()),
        }
    
    def enqueue(self, channel: str, to: str, text: str) -> str:
        """Convenience method to enqueue a delivery."""
        return self.queue.enqueue(channel, to, text)

def chunk_message(text: str, chunk_size: int = 4096) -> List[str]:
    """Split text into chunks respecting paragraph boundaries."""
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    paragraphs = text.split("\n\n")
    current = ""
    
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            while len(para) > chunk_size:
                chunks.append(para[:chunk_size])
                para = para[chunk_size:]
            current = para
    
    if current:
        chunks.append(current)
    
    return chunks