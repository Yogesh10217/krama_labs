"""
app/api/routes/v1/jobs_async.py — Phase 10 Async Job Execution API

Endpoints:
  POST   /jobs/async/submit          — Submit a new job (idempotent)
  GET    /jobs/async/{job_id}        — Get job execution detail
  GET    /jobs/async/                — List jobs (paged, filtered by status)
  DELETE /jobs/async/{job_id}/cancel — Request cancellation
  GET    /jobs/async/queue/health    — Queue health

The worker (BackgroundWorker) is stored as application state via app.state.
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.dependencies import get_organization_context
from app.core.config import Config
from app.db.models.job_execution import JobExecution
from app.domain.enums import ExecutionStatus
from app.jobs.dispatcher import JobDispatcher
from app.jobs.queue import get_queue_provider
from app.schemas.job_execution import (
    JobExecutionCreate,
    JobExecutionResponse,
    JobExecutionDetail,
    CancelJobResponse,
    QueueHealthResponse,
)

router = APIRouter(prefix="/jobs/async", tags=["Async Jobs (Phase 10)"])
logger = logging.getLogger(__name__)


def _get_queue():
    """Return the singleton queue provider. Lazy-init for simplicity."""
    return get_queue_provider(Config.JOB_QUEUE_PROVIDER, Config.QUEUE_NAME)


# -----------------------------------------------------------------------
# POST /jobs/async/submit
# -----------------------------------------------------------------------
@router.post(
    "/submit",
    response_model=JobExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an async pipeline job",
)
def submit_job(
    payload: JobExecutionCreate,
    db: Session = Depends(get_db),
    org=Depends(get_organization_context),
):
    """
    Submit a new document-processing job.

    Returns 202 Accepted immediately with the job record.
    Use GET /jobs/async/{job_id} to poll progress.
    """
    queue = _get_queue()
    dispatcher = JobDispatcher(db=db, queue=queue)
    job = dispatcher.dispatch(
        organization_id=str(org.id),
        document_id=payload.document_id,
        job_type=payload.job_type,
        priority=payload.priority,
        correlation_id=payload.correlation_id,
    )
    return job


# -----------------------------------------------------------------------
# GET /jobs/async/{job_id}
# -----------------------------------------------------------------------
@router.get(
    "/{job_id}",
    response_model=JobExecutionDetail,
    summary="Get async job execution details",
)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    org=Depends(get_organization_context),
):
    job = db.query(JobExecution).filter(
        JobExecution.id == job_id,
        JobExecution.organization_id == str(org.id),
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# -----------------------------------------------------------------------
# GET /jobs/async/
# -----------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[JobExecutionResponse],
    summary="List async job executions",
)
def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    document_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    org=Depends(get_organization_context),
):
    q = db.query(JobExecution).filter(JobExecution.organization_id == str(org.id))
    if status_filter:
        q = q.filter(JobExecution.status == status_filter)
    if document_id:
        q = q.filter(JobExecution.document_id == document_id)
    return q.order_by(JobExecution.created_at.desc()).offset(offset).limit(limit).all()


# -----------------------------------------------------------------------
# DELETE /jobs/async/{job_id}/cancel
# -----------------------------------------------------------------------
@router.delete(
    "/{job_id}/cancel",
    response_model=CancelJobResponse,
    summary="Request cancellation of an async job",
)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    org=Depends(get_organization_context),
):
    job = db.query(JobExecution).filter(
        JobExecution.id == job_id,
        JobExecution.organization_id == str(org.id),
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    terminal = {ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value, ExecutionStatus.CANCELLED.value}
    if job.status in terminal:
        return CancelJobResponse(
            job_execution_id=job_id,
            cancelled=False,
            message=f"Job is already in terminal state: {job.status}"
        )

    # Mark as CANCELLED in DB (worker will pick this up)
    from datetime import datetime, timezone
    job.status = ExecutionStatus.CANCELLED.value
    job.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    return CancelJobResponse(
        job_execution_id=job_id,
        cancelled=True,
        message="Cancellation requested. The job will stop at the next checkpoint."
    )


# -----------------------------------------------------------------------
# GET /jobs/async/queue/health
# -----------------------------------------------------------------------
@router.get(
    "/queue/health",
    response_model=QueueHealthResponse,
    summary="Queue provider health",
)
def queue_health():
    queue = _get_queue()
    h = queue.health()
    return QueueHealthResponse(
        provider=h.provider,
        is_healthy=h.is_healthy,
        approximate_size=h.approximate_size,
        details=h.details,
    )
