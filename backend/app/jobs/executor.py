"""
app/jobs/executor.py — JobExecutor

Orchestrates a single job execution:
  - Drives the PipelineStateMachine stage by stage.
  - Persists checkpoint metadata after each successful stage.
  - Records JobEvents for every state transition.
  - Records JobRetry entries on failures.
  - Checks the CancellationToken between every stage.
  - Applies per-stage retry policies with exponential back-off.

JobExecutor DOES NOT:
  - Know about the queue.
  - Know about workers.
  - Construct service objects (stages do that).
  - Call any HTTP APIs.
"""
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from app.db.models.job_execution import JobExecution, JobEvent, JobRetry
from app.domain.enums import ExecutionStatus, JobEventType
from app.jobs.context import JobContext
from app.jobs.cancellation import CancellationToken, CancelledError
from app.jobs.stage import PipelineStage
from app.jobs.state_machine import PipelineStateMachine

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record_event(
    db: Session,
    job_id: str,
    event_type: JobEventType,
    *,
    message: Optional[str] = None,
    stage_name: Optional[str] = None,
    progress: Optional[int] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    evt = JobEvent(
        id=str(uuid.uuid4()),
        job_execution_id=job_id,
        event_type=event_type.value,
        message=message,
        stage_name=stage_name,
        progress=progress,
        correlation_id=correlation_id,
        metadata_json=metadata,
        created_at=_now(),
    )
    db.add(evt)
    db.flush()


class JobExecutor:
    """
    Runs a single JobExecution through its pipeline stages.

    All decisions about which stage is next are delegated to PipelineStateMachine.
    """

    def __init__(self, db: Session, stages: List[PipelineStage]) -> None:
        self._db = db
        self._stages = stages

    def run(
        self,
        job: JobExecution,
        ctx: JobContext,
        cancellation_token: CancellationToken,
    ) -> None:
        """
        Execute all pipeline stages for the given job.

        This is a synchronous, blocking call. The caller (BackgroundWorker)
        is responsible for running it in a thread pool.
        """
        # Build state machine from current checkpoint
        checkpoints: Dict[str, dict] = job.checkpoint_meta or {}
        machine = PipelineStateMachine(
            stages=self._stages,
            last_successful_stage=job.last_successful_stage,
            checkpoints=checkpoints,
        )

        # Mark job as RUNNING
        job.status = ExecutionStatus.RUNNING.value
        job.started_at = job.started_at or _now()
        job.correlation_id = ctx.correlation_id
        self._db.flush()

        _record_event(
            self._db, job.id, JobEventType.JOB_STARTED,
            message="Job execution started",
            correlation_id=ctx.correlation_id,
        )
        self._db.commit()

        accumulated_progress = 0

        try:
            while not machine.is_terminal:
                # Cooperative cancellation check between every stage
                try:
                    cancellation_token.raise_if_cancelled()
                except CancelledError:
                    self._handle_cancellation(job, ctx, machine)
                    return

                transition = machine.next()
                if transition.is_terminal:
                    break

                stage = transition.next_stage
                checkpoint_data = machine.get_checkpoint(stage.stage_name()) if transition.resume_from_checkpoint else None

                # Update current stage on job record
                job.current_stage = stage.stage_name()
                self._db.flush()

                _record_event(
                    self._db, job.id, JobEventType.STAGE_STARTED,
                    stage_name=stage.stage_name(),
                    progress=accumulated_progress,
                    correlation_id=ctx.correlation_id,
                )
                self._db.commit()

                # Execute with per-stage retry policy
                result = self._execute_with_retry(
                    job=job,
                    stage=stage,
                    ctx=ctx,
                    cancellation_token=cancellation_token,
                    checkpoint_data=checkpoint_data,
                    accumulated_progress=accumulated_progress,
                )

                if result.success:
                    accumulated_progress += result.progress_contribution
                    job.progress = accumulated_progress
                    job.last_successful_stage = stage.stage_name()
                    job.last_success_timestamp = _now()
                    job.checkpoint_version += 1

                    # Persist stage output into checkpoint_meta
                    if result.output:
                        cp = dict(job.checkpoint_meta or {})
                        cp[stage.stage_name()] = result.output
                        job.checkpoint_meta = cp
                        machine.save_checkpoint(stage.stage_name(), result.output)

                    self._db.flush()
                    _record_event(
                        self._db, job.id, JobEventType.STAGE_COMPLETED,
                        stage_name=stage.stage_name(),
                        progress=accumulated_progress,
                        correlation_id=ctx.correlation_id,
                        metadata={"weight": stage.weight()},
                    )
                    self._db.commit()
                    machine.advance(success=True)

                else:
                    # Retry exhausted — abort
                    machine.mark_terminal()
                    self._handle_failure(job, ctx, stage.stage_name(), result.error_message or "Unknown error")
                    return

            # All stages complete
            job.status = ExecutionStatus.COMPLETED.value
            job.progress = 100
            job.current_stage = None
            job.completed_at = _now()
            self._db.flush()
            _record_event(
                self._db, job.id, JobEventType.JOB_COMPLETED,
                message="All pipeline stages completed successfully.",
                correlation_id=ctx.correlation_id,
            )
            self._db.commit()
            logger.info("[%s] Job %s completed successfully.", ctx.correlation_id, job.id)

        except CancelledError:
            self._handle_cancellation(job, ctx, machine)
            return
        except Exception as exc:
            logger.exception("[%s] Unexpected error in job %s: %s", ctx.correlation_id, job.id, exc)
            self._handle_failure(job, ctx, job.current_stage or "unknown", str(exc))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _execute_with_retry(
        self,
        job: JobExecution,
        stage: PipelineStage,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint_data: Optional[dict],
        accumulated_progress: int,
    ):
        policy = stage.retry_policy()
        last_result = None

        for attempt in range(1, policy.max_attempts + 1):
            try:
                cancellation_token.raise_if_cancelled()
            except CancelledError:
                raise

            result = stage.execute(ctx, cancellation_token, checkpoint_data)

            if result.success:
                return result

            last_result = result
            error_msg = result.error_message or "Stage failed"
            logger.warning(
                "[%s] Stage %s attempt %d/%d failed: %s",
                ctx.correlation_id, stage.stage_name(), attempt, policy.max_attempts, error_msg
            )

            # Record retry
            backoff = policy.backoff_for(attempt)
            retry = JobRetry(
                id=str(uuid.uuid4()),
                job_execution_id=job.id,
                attempt=attempt,
                stage_name=stage.stage_name(),
                reason=error_msg,
                backoff_seconds=backoff,
                correlation_id=ctx.correlation_id,
                created_at=_now(),
            )
            self._db.add(retry)
            job.retry_count += 1
            job.status = ExecutionStatus.RETRYING.value
            self._db.flush()
            _record_event(
                self._db, job.id, JobEventType.RETRY_STARTED,
                stage_name=stage.stage_name(),
                message=f"Attempt {attempt}/{policy.max_attempts}. Backoff {backoff}s",
                correlation_id=ctx.correlation_id,
            )
            self._db.commit()

            if attempt < policy.max_attempts:
                time.sleep(backoff)

        # All attempts exhausted
        _record_event(
            self._db, job.id, JobEventType.RETRY_EXHAUSTED,
            stage_name=stage.stage_name(),
            message=f"All {policy.max_attempts} attempts failed",
            correlation_id=ctx.correlation_id,
        )
        self._db.commit()
        return last_result

    def _handle_failure(
        self, job: JobExecution, ctx: JobContext, stage_name: str, reason: str
    ) -> None:
        job.status = ExecutionStatus.FAILED.value
        job.completed_at = _now()
        self._db.flush()
        _record_event(
            self._db, job.id, JobEventType.JOB_FAILED,
            stage_name=stage_name,
            message=reason,
            correlation_id=ctx.correlation_id,
        )
        self._db.commit()
        logger.error("[%s] Job %s FAILED at stage %s: %s", ctx.correlation_id, job.id, stage_name, reason)

    def _handle_cancellation(
        self, job: JobExecution, ctx: JobContext, machine: PipelineStateMachine
    ) -> None:
        machine.mark_terminal()
        job.status = ExecutionStatus.CANCELLED.value
        job.cancelled_at = _now()
        self._db.flush()
        _record_event(
            self._db, job.id, JobEventType.JOB_CANCELLED,
            message="Cooperative cancellation requested.",
            correlation_id=ctx.correlation_id,
        )
        self._db.commit()
        logger.info("[%s] Job %s was cancelled.", ctx.correlation_id, job.id)
