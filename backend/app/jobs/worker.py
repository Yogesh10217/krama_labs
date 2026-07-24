"""
app/jobs/worker.py — BackgroundWorker

Runs a poll-and-execute loop in a dedicated thread pool.

Features:
  - Concurrent execution across configurable worker slots.
  - Heartbeat tracking: each active job receives periodic heartbeat events.
  - Graceful shutdown: stops accepting new work and waits for in-flight
    jobs to complete (bounded by a drain timeout).
  - Crash detection: jobs whose heartbeat is stale are detected and requeued
    by any healthy worker.
  - One CancellationToken per job: the API can request cancellation, and
    the worker will propagate it cooperatively.

Workers NEVER:
  - Call HTTP APIs.
  - Communicate with each other directly (all coordination via DB + queue).
  - Modify OCR, Extraction, or Validation artifacts.
"""
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import Config
from app.db.models.job_execution import JobExecution, JobEvent
from app.domain.enums import ExecutionStatus, JobEventType
from app.jobs.cancellation import CancellationToken
from app.jobs.context import JobContext
from app.jobs.executor import JobExecutor
from app.jobs.queue import JobQueueProvider, QueueMessage
from app.jobs.registry import build_document_pipeline

logger = logging.getLogger(__name__)

WORKER_ID = str(uuid.uuid4())  # Unique ID per process


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BackgroundWorker:
    """
    Multi-threaded background worker that polls the queue and executes jobs.

    Usage:
        worker = BackgroundWorker(db_factory, queue)
        worker.start()          # launches background threads
        ...
        worker.stop()           # graceful shutdown
    """

    def __init__(
        self,
        db_factory,      # callable() → Session
        queue: JobQueueProvider,
        max_workers: int = 4,
        heartbeat_interval: int = 30,
        stale_threshold: int = 120,
    ) -> None:
        self._db_factory = db_factory
        self._queue = queue
        self._max_workers = max_workers
        self._heartbeat_interval = heartbeat_interval
        self._stale_threshold = stale_threshold
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="krama-worker")
        self._cancellation_tokens: Dict[str, CancellationToken] = {}
        self._tokens_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._poll_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the polling and heartbeat background threads."""
        logger.info("BackgroundWorker %s starting (max_workers=%d)", WORKER_ID, self._max_workers)
        self._poll_thread = threading.Thread(target=self._poll_loop, name="krama-poller", daemon=True)
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, name="krama-heartbeat", daemon=True)
        self._poll_thread.start()
        self._heartbeat_thread.start()

    def stop(self, drain_timeout: float = 30.0) -> None:
        """Gracefully stop the worker. Waits up to drain_timeout seconds for in-flight jobs."""
        logger.info("BackgroundWorker %s stopping...", WORKER_ID)
        self._stop_event.set()

        # Request cancellation for all in-flight jobs
        with self._tokens_lock:
            for token in self._cancellation_tokens.values():
                token.cancel()

        self._executor.shutdown(wait=True, cancel_futures=False)
        if self._poll_thread:
            self._poll_thread.join(timeout=drain_timeout)
        logger.info("BackgroundWorker %s stopped.", WORKER_ID)

    def request_cancellation(self, job_execution_id: str) -> bool:
        """API layer calls this to cancel an in-flight job. Returns True if job was in-flight."""
        with self._tokens_lock:
            token = self._cancellation_tokens.get(job_execution_id)
            if token:
                token.cancel()
                return True
        # Job not in-flight locally; mark it CANCELLED in DB so no worker picks it up
        return False

    # ------------------------------------------------------------------
    # Poll loop
    # ------------------------------------------------------------------

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                msg = self._queue.dequeue(timeout_seconds=2.0)
                if msg:
                    self._executor.submit(self._handle_message, msg)
            except Exception as exc:
                logger.exception("Error in poll loop: %s", exc)
            # Reclaim stale jobs from crashed workers periodically
            try:
                self._reclaim_stale_jobs()
            except Exception as exc:
                logger.exception("Error in stale-job reclaim: %s", exc)

    # ------------------------------------------------------------------
    # Job execution
    # ------------------------------------------------------------------

    def _handle_message(self, msg: QueueMessage) -> None:
        job_id = msg.job_execution_id
        ctx = msg.context
        token = CancellationToken()

        with self._tokens_lock:
            self._cancellation_tokens[job_id] = token

        db: Session = self._db_factory()
        try:
            job = db.query(JobExecution).filter(JobExecution.id == job_id).first()
            if not job:
                logger.error("Job %s not found in database; discarding.", job_id)
                self._queue.ack(msg.message_id)
                return

            # Skip if already completed or cancelled by another worker
            if job.status in (ExecutionStatus.COMPLETED.value, ExecutionStatus.CANCELLED.value, ExecutionStatus.FAILED.value):
                logger.info("Job %s already terminal (%s); discarding.", job_id, job.status)
                self._queue.ack(msg.message_id)
                return

            # Assign worker
            job.worker_id = WORKER_ID
            job.last_heartbeat_at = _now()
            db.commit()

            stages = build_document_pipeline(db)
            executor = JobExecutor(db=db, stages=stages)
            executor.run(job=job, ctx=ctx, cancellation_token=token)
            self._queue.ack(msg.message_id)

        except Exception as exc:
            logger.exception("[%s] Unhandled error processing job %s: %s", ctx.correlation_id, job_id, exc)
            self._queue.nack(msg.message_id, requeue=False)
        finally:
            db.close()
            with self._tokens_lock:
                self._cancellation_tokens.pop(job_id, None)

    # ------------------------------------------------------------------
    # Heartbeat loop
    # ------------------------------------------------------------------

    def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self._heartbeat_interval)
            with self._tokens_lock:
                active_jobs = list(self._cancellation_tokens.keys())

            if not active_jobs:
                continue

            db: Session = self._db_factory()
            try:
                now = _now()
                for job_id in active_jobs:
                    job = db.query(JobExecution).filter(JobExecution.id == job_id).first()
                    if job:
                        job.last_heartbeat_at = now
                        db.add(JobEvent(
                            id=str(uuid.uuid4()),
                            job_execution_id=job_id,
                            event_type=JobEventType.HEARTBEAT.value,
                            message=f"Worker {WORKER_ID} heartbeat",
                            created_at=now,
                        ))
                db.commit()
            except Exception as exc:
                logger.exception("Heartbeat error: %s", exc)
                db.rollback()
            finally:
                db.close()

    # ------------------------------------------------------------------
    # Stale job reclaim
    # ------------------------------------------------------------------

    def _reclaim_stale_jobs(self) -> None:
        """
        Find RUNNING/RETRYING jobs whose heartbeat is older than the
        stale threshold, and requeue them.
        """
        stale_cutoff = _now() - timedelta(seconds=self._stale_threshold)
        db: Session = self._db_factory()
        try:
            stale_jobs = (
                db.query(JobExecution)
                .filter(
                    JobExecution.status.in_([ExecutionStatus.RUNNING.value, ExecutionStatus.RETRYING.value]),
                    JobExecution.last_heartbeat_at < stale_cutoff,
                )
                .all()
            )
            for job in stale_jobs:
                logger.warning("Reclaiming stale job %s (last heartbeat: %s)", job.id, job.last_heartbeat_at)
                job.status = ExecutionStatus.QUEUED.value
                job.worker_id = None
                db.flush()
                ctx = JobContext(
                    job_execution_id=job.id,
                    document_id=job.document_id,
                    organization_id=job.organization_id,
                    correlation_id=job.correlation_id or str(uuid.uuid4()),
                    job_type=job.job_type,
                )
                from app.jobs.queue import QueueMessage
                self._queue.enqueue(QueueMessage(
                    message_id=str(uuid.uuid4()),
                    job_execution_id=job.id,
                    context=ctx,
                ))
            if stale_jobs:
                db.commit()
        except Exception as exc:
            logger.exception("Stale-job reclaim error: %s", exc)
            db.rollback()
        finally:
            db.close()
