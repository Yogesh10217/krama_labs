"""
Phase 10 — Async Job Execution Models

Three immutable, append-only tables:
  job_executions — the primary execution record for each pipeline run
  job_events     — immutable event log (for audit trail)
  job_retries    — immutable retry history

All PKs are UUIDs stored as strings for SQLite compatibility.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Float
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.domain.enums import ExecutionStatus


def _uuid() -> str:
    return str(uuid.uuid4())


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(String, primary_key=True, default=_uuid)
    organization_id = Column(String, nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)

    job_type = Column(String, nullable=False)  # e.g. "DOCUMENT_PROCESSING"
    status = Column(String, default=ExecutionStatus.QUEUED.value, nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)

    # Worker tracking
    worker_id = Column(String, nullable=True)
    queue_name = Column(String, nullable=False, default="document-intelligence")
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)

    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Weighted progress 0–100
    progress = Column(Integer, default=0, nullable=False)

    # Checkpoint metadata for resumable execution
    current_stage = Column(String, nullable=True)
    last_successful_stage = Column(String, nullable=True)
    last_success_timestamp = Column(DateTime(timezone=True), nullable=True)
    checkpoint_version = Column(Integer, default=0, nullable=False)
    checkpoint_meta = Column(JSON, nullable=True)  # stage-specific state

    # Correlation ID for distributed tracing
    correlation_id = Column(String, nullable=True, index=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    document = relationship("Document", backref="job_executions", foreign_keys=[document_id])
    events = relationship(
        "JobEvent",
        back_populates="job_execution",
        cascade="all, delete-orphan",
        order_by="JobEvent.created_at",
        lazy="selectin"
    )
    retries = relationship(
        "JobRetry",
        back_populates="job_execution",
        cascade="all, delete-orphan",
        order_by="JobRetry.created_at",
        lazy="selectin"
    )


class JobEvent(Base):
    """Immutable event log entry for a JobExecution."""
    __tablename__ = "job_events"

    id = Column(String, primary_key=True, default=_uuid)
    job_execution_id = Column(String, ForeignKey("job_executions.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String, nullable=False)   # JobEventType enum value
    message = Column(String, nullable=True)
    stage_name = Column(String, nullable=True)
    progress = Column(Integer, nullable=True)
    correlation_id = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    job_execution = relationship("JobExecution", back_populates="events")


class JobRetry(Base):
    """Immutable retry history entry for a JobExecution."""
    __tablename__ = "job_retries"

    id = Column(String, primary_key=True, default=_uuid)
    job_execution_id = Column(String, ForeignKey("job_executions.id", ondelete="CASCADE"), nullable=False, index=True)

    attempt = Column(Integer, nullable=False)
    stage_name = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    backoff_seconds = Column(Float, nullable=True)
    correlation_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    job_execution = relationship("JobExecution", back_populates="retries")
