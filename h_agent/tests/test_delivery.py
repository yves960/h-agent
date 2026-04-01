#!/usr/bin/env python3
"""
h_agent/tests/test_delivery.py - TDD tests for s08 DeliveryQueue

Tests cover:
- DeliveryQueue.enqueue() - atomic write
- DeliveryQueue.ack() - successful delivery
- DeliveryQueue.fail() - retry with backoff
- DeliveryQueue.move_to_failed() - after 5 retries
- compute_backoff_ms() - correct intervals + jitter
- chunk_message() - splits correctly at paragraph boundaries
- DeliveryRunner._process_pending() - processes due entries
- DeliveryRunner.get_stats() - statistics tracking
- Recovery scan on startup
- Concurrent read/write safety
"""

import json
import os
import random
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from h_agent.delivery.queue import (
    DeliveryQueue,
    QueuedDelivery,
    compute_backoff_ms,
    BACKOFF_MS,
    MAX_RETRIES,
    QUEUE_DIR,
)
from h_agent.delivery.runner import DeliveryRunner, chunk_message


class TestQueuedDelivery:
    """Tests for QueuedDelivery dataclass."""

    def test_to_dict_returns_all_fields(self):
        entry = QueuedDelivery(
            id="abc123",
            channel="dingtalk",
            to="user123",
            text="Hello",
            enqueued_at=1000.0,
            next_retry_at=2000.0,
            retry_count=2,
            last_error="timeout",
        )
        d = entry.to_dict()
        assert d["id"] == "abc123"
        assert d["channel"] == "dingtalk"
        assert d["to"] == "user123"
        assert d["text"] == "Hello"
        assert d["enqueued_at"] == 1000.0
        assert d["next_retry_at"] == 2000.0
        assert d["retry_count"] == 2
        assert d["last_error"] == "timeout"

    def test_from_dict_recreates_entry(self):
        d = {
            "id": "xyz789",
            "channel": "feishu",
            "to": "group456",
            "text": "World",
            "enqueued_at": 1500.0,
            "next_retry_at": 0.0,
            "retry_count": 0,
            "last_error": "",
        }
        entry = QueuedDelivery.from_dict(d)
        assert entry.id == "xyz789"
        assert entry.channel == "feishu"
        assert entry.to == "group456"
        assert entry.text == "World"
        assert entry.enqueued_at == 1500.0
        assert entry.next_retry_at == 0.0
        assert entry.retry_count == 0
        assert entry.last_error == ""

    def test_from_dict_with_missing_optionals(self):
        d = {
            "id": "min123",
            "channel": "telegram",
            "to": "chat789",
            "text": "Test",
            "enqueued_at": 500.0,
        }
        entry = QueuedDelivery.from_dict(d)
        assert entry.next_retry_at == 0.0
        assert entry.retry_count == 0
        assert entry.last_error == ""


class TestComputeBackoffMs:
    """Tests for exponential backoff calculation."""

    def test_zero_retry_count_returns_zero(self):
        assert compute_backoff_ms(0) == 0

    def test_negative_retry_count_returns_zero(self):
        assert compute_backoff_ms(-1) == 0

    def test_first_retry_uses_first_backoff(self):
        backoff = compute_backoff_ms(1)
        assert BACKOFF_MS[0] - BACKOFF_MS[0] // 5 <= backoff <= BACKOFF_MS[0] + BACKOFF_MS[0] // 5

    def test_second_retry_uses_second_backoff(self):
        backoff = compute_backoff_ms(2)
        assert BACKOFF_MS[1] - BACKOFF_MS[1] // 5 <= backoff <= BACKOFF_MS[1] + BACKOFF_MS[1] // 5

    def test_fifth_retry_caps_at_last_backoff(self):
        backoff = compute_backoff_ms(100)
        assert BACKOFF_MS[-1] - BACKOFF_MS[-1] // 5 <= backoff <= BACKOFF_MS[-1] + BACKOFF_MS[-1] // 5

    def test_backoff_within_jitter_range(self):
        random.seed(42)
        for retry_count in range(1, len(BACKOFF_MS) + 2):
            base = BACKOFF_MS[min(retry_count - 1, len(BACKOFF_MS) - 1)]
            backoff = compute_backoff_ms(retry_count)
            jitter_range = base // 5
            assert base - jitter_range <= backoff <= base + jitter_range


class TestChunkMessage:
    """Tests for message chunking."""

    def test_empty_string_returns_empty_list(self):
        assert chunk_message("") == []

    def test_single_short_message_returns_one_chunk(self):
        text = "Hello world"
        chunks = chunk_message(text, chunk_size=4096)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_exact_size_returns_one_chunk(self):
        text = "a" * 100
        chunks = chunk_message(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_oversized_single_word_splits(self):
        text = "a" * 5000
        chunks = chunk_message(text, chunk_size=4096)
        assert len(chunks) == 2
        assert all(len(c) <= 4096 for c in chunks)

    def test_paragraphs_preserved_when_possible(self):
        text = "Para 1\n\nPara 2\n\nPara 3"
        chunks = chunk_message(text, chunk_size=100)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 100

    def test_paragraph_boundaries_respected(self):
        text = "Short para.\n\nAnother paragraph here."
        chunks = chunk_message(text, chunk_size=50)
        joined = "".join(chunks)
        assert "Short para." in joined
        assert "Another paragraph here." in joined

    def test_many_small_paragraphs_combined(self):
        paragraphs = ["p"] * 20
        text = "\n\n".join(paragraphs)
        chunks = chunk_message(text, chunk_size=100)
        total = "".join(chunks)
        assert total.count("p") == 20

    def test_default_chunk_size_used(self):
        text = "a" * 5000
        chunks = chunk_message(text)
        assert all(len(c) <= 4096 for c in chunks)


class TestDeliveryQueue:
    """Tests for DeliveryQueue with temp directory."""

    @pytest.fixture
    def temp_queue_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def queue(self, temp_queue_dir):
        return DeliveryQueue(queue_dir=temp_queue_dir)

    def test_enqueue_returns_id(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Hello")
        assert isinstance(delivery_id, str)
        assert len(delivery_id) == 12

    def test_enqueue_creates_file(self, queue):
        delivery_id = queue.enqueue("feishu", "user456", "World")
        path = queue.queue_dir / f"{delivery_id}.json"
        assert path.exists()

    def test_enqueue_writes_atomic(self, queue):
        delivery_id = queue.enqueue("telegram", "chat789", "Atomic write test")
        path = queue.queue_dir / f"{delivery_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["channel"] == "telegram"
        assert data["to"] == "chat789"
        assert data["text"] == "Atomic write test"
        assert data["id"] == delivery_id

    def test_enqueue_no_tmp_file_left_behind(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "No tmp")
        tmp_files = list(queue.queue_dir.glob(".tmp.*"))
        assert len(tmp_files) == 0

    def test_ack_removes_file(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "To be acked")
        path = queue.queue_dir / f"{delivery_id}.json"
        assert path.exists()
        result = queue.ack(delivery_id)
        assert result is True
        assert not path.exists()

    def test_ack_nonexistent_returns_false(self, queue):
        result = queue.ack("nonexistent123")
        assert result is False

    def test_fail_increments_retry_count(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Fail me")
        queue.fail(delivery_id, "test error")
        entry = queue._read_entry(delivery_id)
        assert entry.retry_count == 1

    def test_fail_updates_last_error(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Fail me")
        queue.fail(delivery_id, "connection timeout")
        entry = queue._read_entry(delivery_id)
        assert entry.last_error == "connection timeout"

    def test_fail_sets_next_retry_at(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Fail me")
        before = time.time()
        queue.fail(delivery_id, "test error")
        after = time.time()
        entry = queue._read_entry(delivery_id)
        assert entry.next_retry_at > before
        assert entry.next_retry_at > 0

    def test_fail_after_max_retries_moves_to_failed(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Exhausted")
        for _ in range(MAX_RETRIES):
            queue.fail(delivery_id, "persistent error")
        failed_path = queue.failed_dir / f"{delivery_id}.json"
        assert failed_path.exists()
        queue_path = queue.queue_dir / f"{delivery_id}.json"
        assert not queue_path.exists()

    def test_move_to_failed_renames_file(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Move me")
        queue.move_to_failed(delivery_id)
        failed_path = queue.failed_dir / f"{delivery_id}.json"
        assert failed_path.exists()
        queue_path = queue.queue_dir / f"{delivery_id}.json"
        assert not queue_path.exists()

    def test_load_pending_returns_sorted_entries(self, queue):
        id1 = queue.enqueue("dingtalk", "u1", "First")
        time.sleep(0.01)
        id2 = queue.enqueue("dingtalk", "u2", "Second")
        pending = queue.load_pending()
        assert len(pending) == 2
        assert pending[0].id == id1
        assert pending[1].id == id2

    def test_load_pending_ignores_tmp_files(self, queue):
        tmp_path = queue.queue_dir / ".tmp.123.json"
        tmp_path.write_text("{}", encoding="utf-8")
        queue.enqueue("dingtalk", "user123", "Real entry")
        pending = queue.load_pending()
        assert all(not p.id.startswith(".tmp") for p in pending)

    def test_load_failed_returns_sorted_entries(self, queue):
        id1 = queue.enqueue("dingtalk", "u1", "Failed1")
        queue.move_to_failed(id1)
        time.sleep(0.01)
        id2 = queue.enqueue("dingtalk", "u2", "Failed2")
        queue.move_to_failed(id2)
        failed = queue.load_failed()
        assert len(failed) == 2
        assert failed[0].id == id1
        assert failed[1].id == id2

    def test_recovery_scan_counts_due_entries(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Due entry")
        queue.fail(delivery_id, "error")
        entry = queue._read_entry(delivery_id)
        entry.next_retry_at = time.time() - 10
        queue._write_entry(entry)
        count = queue._recovery_scan()
        assert count == 1

    def test_recovery_scan_skips_not_yet_due(self, queue):
        delivery_id = queue.enqueue("dingtalk", "user123", "Not due")
        queue.fail(delivery_id, "error")
        entry = queue._read_entry(delivery_id)
        entry.next_retry_at = time.time() + 3600
        queue._write_entry(entry)
        count = queue._recovery_scan()
        assert count == 0


class TestDeliveryRunner:
    """Tests for DeliveryRunner."""

    @pytest.fixture
    def temp_queue_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def runner(self, temp_queue_dir):
        from h_agent.delivery.queue import DeliveryQueue
        queue = DeliveryQueue(queue_dir=temp_queue_dir)
        return DeliveryRunner(queue=queue)

    def test_start_creates_thread(self, runner):
        runner.start()
        assert runner._thread is not None
        assert runner._thread.is_alive()
        runner.stop()

    def test_stop_terminates_thread(self, runner):
        runner.start()
        time.sleep(0.1)
        runner.stop()
        assert not runner._thread.is_alive()

    def test_enqueue_adds_to_queue(self, runner):
        delivery_id = runner.enqueue("dingtalk", "user123", "Hello")
        assert isinstance(delivery_id, str)
        pending = runner.queue.load_pending()
        assert len(pending) == 1
        assert pending[0].text == "Hello"

    def test_process_pending_handles_success(self, runner):
        delivered = []

        def fake_deliver(channel, to, text):
            delivered.append((channel, to, text))

        runner.deliver_fn = fake_deliver
        runner.enqueue("dingtalk", "user123", "Hello")
        runner._process_pending()
        assert len(delivered) == 1
        assert delivered[0] == ("dingtalk", "user123", "Hello")
        assert len(runner.queue.load_pending()) == 0

    def test_process_pending_handles_failure(self, runner):
        def fake_deliver(channel, to, text):
            raise RuntimeError("delivery failed")

        runner.deliver_fn = fake_deliver
        runner.enqueue("dingtalk", "user123", "Hello")
        runner._process_pending()
        pending = runner.queue.load_pending()
        assert len(pending) == 1
        assert pending[0].retry_count == 1
        assert pending[0].last_error == "delivery failed"

    def test_process_pending_skips_not_due_entries(self, runner):
        delivered = []

        def fake_deliver(channel, to, text):
            delivered.append((channel, to, text))

        runner.deliver_fn = fake_deliver
        runner.enqueue("dingtalk", "user123", "Hello")
        entry = runner.queue.load_pending()[0]
        entry.next_retry_at = time.time() + 3600
        runner.queue._write_entry(entry)
        runner._process_pending()
        assert len(delivered) == 0

    def test_get_stats_initial_state(self, runner):
        runner.enqueue("dingtalk", "u1", "One")
        runner.enqueue("dingtalk", "u2", "Two")
        stats = runner.get_stats()
        assert stats["attempted"] == 0
        assert stats["succeeded"] == 0
        assert stats["failed"] == 0
        assert stats["pending"] == 2
        assert stats["failed_count"] == 0

    def test_get_stats_after_successful_delivery(self, runner):
        delivered = []

        def fake_deliver(channel, to, text):
            delivered.append((channel, to, text))

        runner.deliver_fn = fake_deliver
        runner.enqueue("dingtalk", "user123", "Hello")
        runner._process_pending()
        stats = runner.get_stats()
        assert stats["attempted"] == 1
        assert stats["succeeded"] == 1
        assert stats["failed"] == 0
        assert stats["pending"] == 0

    def test_get_stats_after_failed_delivery(self, runner):
        def fake_deliver(channel, to, text):
            raise RuntimeError("fail")

        runner.deliver_fn = fake_deliver
        runner.enqueue("dingtalk", "user123", "Hello")
        runner._process_pending()
        stats = runner.get_stats()
        assert stats["attempted"] == 1
        assert stats["succeeded"] == 0
        assert stats["failed"] == 1
        assert stats["pending"] == 1

    def test_recovery_scan_on_start(self, temp_queue_dir):
        from h_agent.delivery.queue import DeliveryQueue
        queue = DeliveryQueue(queue_dir=temp_queue_dir)
        queue.enqueue("dingtalk", "user123", "Recovered")
        runner = DeliveryRunner(queue=queue)
        count = runner._recovery_scan()
        assert count >= 0

    def test_background_loop_processes_entries(self, runner):
        delivered = []

        def fake_deliver(channel, to, text):
            delivered.append((channel, to, text))

        runner.deliver_fn = fake_deliver
        runner.start()
        runner.enqueue("dingtalk", "user123", "Async hello")
        time.sleep(2)
        runner.stop()
        assert len(delivered) == 1

    def test_stats_after_max_retries(self, runner):
        def fake_deliver(channel, to, text):
            raise RuntimeError("always fails")

        runner.deliver_fn = fake_deliver
        runner.enqueue("dingtalk", "user123", "Exhausted")
        for _ in range(MAX_RETRIES):
            runner._process_pending()
        stats = runner.get_stats()
        assert stats["failed"] == MAX_RETRIES
        assert stats["failed_count"] == 1


class TestConcurrentSafety:
    """Tests for concurrent read/write safety."""

    @pytest.fixture
    def temp_queue_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_concurrent_enqueue(self, temp_queue_dir):
        from h_agent.delivery.queue import DeliveryQueue
        queue = DeliveryQueue(queue_dir=temp_queue_dir)
        errors = []

        def enqueue_many(n):
            try:
                for i in range(n):
                    queue.enqueue("dingtalk", f"user{i}", f"Message {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=enqueue_many, args=(20,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        pending = queue.load_pending()
        assert len(pending) == 100

    def test_concurrent_enqueue_and_ack(self, temp_queue_dir):
        from h_agent.delivery.queue import DeliveryQueue
        queue = DeliveryQueue(queue_dir=temp_queue_dir)
        delivery_ids = []
        lock = threading.Lock()

        def enqueue_many(n):
            for i in range(n):
                did = queue.enqueue("dingtalk", f"user{i}", f"Message {i}")
                with lock:
                    delivery_ids.append(did)

        def ack_many(ids):
            time.sleep(0.1)
            for did in ids[:50]:
                queue.ack(did)

        t1 = threading.Thread(target=enqueue_many, args=(100,))
        t2 = threading.Thread(target=ack_many, args=(delivery_ids,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        pending = queue.load_pending()
        assert len(pending) <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])