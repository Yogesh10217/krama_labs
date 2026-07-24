"""
app/jobs/queue.py — JobQueueProvider abstraction + InMemoryJobQueue

The queue is intentionally provider-agnostic. InMemoryJobQueue is used
in development / test. Replace with RabbitMQ/Redis streams in production
by implementing JobQueueProvider.

Workers NEVER communicate with each other directly; all coordination
is through the queue and the database.
"""
import threading
import queue as _stdlib_queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.jobs.context import JobContext


@dataclass
class QueueMessage:
    """A single item dequeued by a worker."""
    message_id: str
    job_execution_id: str
    context: JobContext
    enqueued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delivery_count: int = 0


@dataclass
class QueueHealth:
    provider: str
    is_healthy: bool
    approximate_size: int
    details: Dict[str, Any] = field(default_factory=dict)


class JobQueueProvider(ABC):
    """Abstract job queue interface. All providers must implement this."""

    @abstractmethod
    def enqueue(self, message: QueueMessage) -> None:
        """Enqueue a job message."""

    @abstractmethod
    def dequeue(self, timeout_seconds: float = 5.0) -> Optional[QueueMessage]:
        """Dequeue next message. Returns None on timeout."""

    @abstractmethod
    def ack(self, message_id: str) -> None:
        """Acknowledge a message (remove permanently)."""

    @abstractmethod
    def nack(self, message_id: str, requeue: bool = True) -> None:
        """Negative-acknowledge (reject/requeue) a message."""

    @abstractmethod
    def peek(self) -> Optional[QueueMessage]:
        """Return the head message without consuming it."""

    @abstractmethod
    def size(self) -> int:
        """Return the approximate number of messages in the queue."""

    @abstractmethod
    def health(self) -> QueueHealth:
        """Return health status of the queue."""


class InMemoryJobQueue(JobQueueProvider):
    """
    Thread-safe in-process queue using Python's queue.Queue.

    Intended for development and testing only.
    Not suitable for multi-process deployments.
    """

    def __init__(self, name: str = "inmemory") -> None:
        self._name = name
        self._queue: _stdlib_queue.Queue[QueueMessage] = _stdlib_queue.Queue()
        self._in_flight: Dict[str, QueueMessage] = {}
        self._lock = threading.Lock()

    def enqueue(self, message: QueueMessage) -> None:
        self._queue.put(message)

    def dequeue(self, timeout_seconds: float = 5.0) -> Optional[QueueMessage]:
        try:
            msg = self._queue.get(timeout=timeout_seconds)
            msg.delivery_count += 1
            with self._lock:
                self._in_flight[msg.message_id] = msg
            return msg
        except _stdlib_queue.Empty:
            return None

    def ack(self, message_id: str) -> None:
        with self._lock:
            self._in_flight.pop(message_id, None)

    def nack(self, message_id: str, requeue: bool = True) -> None:
        with self._lock:
            msg = self._in_flight.pop(message_id, None)
        if msg and requeue:
            self._queue.put(msg)

    def peek(self) -> Optional[QueueMessage]:
        """Non-destructive head peek; only works if queue is not empty."""
        with self._lock:
            try:
                return self._queue.queue[0]  # type: ignore[index]
            except IndexError:
                return None

    def size(self) -> int:
        return self._queue.qsize()

    def health(self) -> QueueHealth:
        return QueueHealth(
            provider="inmemory",
            is_healthy=True,
            approximate_size=self.size(),
            details={"in_flight": len(self._in_flight)}
        )


def get_queue_provider(provider_name: str, queue_name: str) -> JobQueueProvider:
    """Factory: return the queue provider specified by config."""
    if provider_name == "inmemory":
        return InMemoryJobQueue(name=queue_name)
    raise ValueError(f"Unknown queue provider: {provider_name!r}. Supported: 'inmemory'")
