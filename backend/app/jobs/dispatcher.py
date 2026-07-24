"""
app/jobs/dispatcher.py — JobDispatcher

Responsible for:
  - Creating JobExecution records in the database.
  - Idempotency: if a job is already QUEUED/RUNNING for the same
    document, return the existing execution rather than creating a duplicate.
  - Enqueuing the QueueMessage.

The dispatcher is the ONLY entry point for submitting new pipeline jobs.
API routes call the dispatcher; they never touch the queue directly.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import Config
from app.db.models.job_execution import JobExecution, JobEvent
from app.domain.enums import ExecutionStatus, JobEventType
from app.jobs.context import JobContext
from app.jobs.queue import JobQueueProvider, QueueMessage

logger = logging.getLogger(__name__)

_ACTIVE_STATUSES = {ExecutionStatus.QUEUED.value, ExecutionStatus.RUNNING.value, ExecutionStatus.RETRYING.value}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobDispatcher:
    """Creates and enqueues pipeline jobs, with idempotency guarantees."""

    def __init__(self, db: Session, queue: JobQueueProvider) -> None:
        self._db = db
        self._queue = queue

    def dispatch(
        self,
        organization_id: str,
        document_id: Optional[str] = None,
        job_type: str = "DOCUMENT_PROCESSING",
        priority: int = 0,
        correlation_id: Optional[str] = None,
    ) -> JobExecution:
        """
        Create a JobExecution and enqueue it.

        If an active job already exists for this document_id + job_type,
        return the existing job (idempotent).
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        # Idempotency check
        if document_id:
            existing = (
                self._db.query(JobExecution)
                .filter(
                    JobExecution.document_id == document_id,
                    JobExecution.job_type == job_type,
                    JobExecution.status.in_(list(_ACTIVE_STATUSES)),
                )
                .first()
            )
            if existing:
                logger.info(
                    "[%s] Idempotency hit — returning existing job %s for doc %s",
                    correlation_id, existing.id, document_id
                )
                return existing

        job_id = str(uuid.uuid4())
        now = _now()

        job = JobExecution(
            id=job_id,
            organization_id=organization_id,
            document_id=document_id,
            job_type=job_type,
            status=ExecutionStatus.QUEUED.value,
            priority=priority,
            queue_name=Config.QUEUE_NAME,
            max_retries=Config.MAX_RETRIES,
            progress=0,
            correlation_id=correlation_id,
            checkpoint_version=0,
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
        self._db.add(job)
        self._db.flush()

        # Record JOB_CREATED event
        evt = JobEvent(
            id=str(uuid.uuid4()),
            job_execution_id=job_id,
            event_type=JobEventType.JOB_CREATED.value,
            message=f"Job queued for {job_type}",
            correlation_id=correlation_id,
            created_at=now,
        )
        self._db.add(evt)
        self._db.commit()

        # Build context and enqueue
        ctx = JobContext(
            job_execution_id=job_id,
            document_id=document_id,
            organization_id=organization_id,
            correlation_id=correlation_id,
            job_type=job_type,
        )
        msg = QueueMessage(
            message_id=str(uuid.uuid4()),
            job_execution_id=job_id,
            context=ctx,
            enqueued_at=now,
        )
        self._queue.enqueue(msg)
        logger.info("[%s] Dispatched job %s (doc=%s)", correlation_id, job_id, document_id)
        return job
