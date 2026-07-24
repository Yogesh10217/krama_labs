"""
app/jobs/stage.py — PipelineStage abstract interface

Every pipeline stage MUST implement this interface.
Stages are responsible for:
  - Executing a single, well-scoped piece of pipeline work.
  - Reporting their own progress weight (used for weighted total progress).
  - Declaring whether they support resumption mid-execution.
  - Providing a rollback strategy (best-effort; pipelines are mostly append-only).
  - Defining their own retry policy.

Workers call stages through the JobExecutor; stages never communicate
with each other directly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.jobs.context import JobContext
from app.jobs.cancellation import CancellationToken


@dataclass(frozen=True)
class RetryPolicy:
    """Per-stage retry configuration."""
    max_attempts: int = 3
    backoff_seconds: float = 2.0
    backoff_multiplier: float = 2.0  # exponential back-off
    max_backoff_seconds: float = 30.0
    retryable_exceptions: tuple = ()  # empty = retry all exceptions

    def backoff_for(self, attempt: int) -> float:
        """Compute back-off delay for a given attempt (1-indexed)."""
        delay = self.backoff_seconds * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_backoff_seconds)


@dataclass
class StageResult:
    """Result returned by a stage after execution."""
    stage_name: str
    success: bool
    progress_contribution: int  # points to add to total progress
    output: Optional[Dict[str, Any]] = None  # stage-specific output persisted to checkpoint_meta
    error_message: Optional[str] = None
    skipped: bool = False


class PipelineStage(ABC):
    """
    Abstract base for all pipeline stages.

    Implementation notes:
      - execute() MUST be idempotent when can_resume() is True.
      - execute() MUST check the cancellation token before any long-running operation.
      - rollback() is best-effort; implementations should log but not raise.
    """

    @abstractmethod
    def stage_name(self) -> str:
        """Unique name for this stage (used as checkpoint key)."""

    @abstractmethod
    def weight(self) -> int:
        """
        Relative weight for progress calculation.
        All weights in the pipeline should sum to 100.
        """

    @abstractmethod
    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        """
        Execute the stage.

        :param ctx: Execution context (correlation_id, document_id, org_id, etc.)
        :param cancellation_token: Check before long-running sub-operations.
        :param checkpoint: Previous checkpoint metadata; non-None when resuming.
        :returns: StageResult with success flag and output.
        """

    def can_resume(self) -> bool:
        """
        Return True if this stage supports resuming from a checkpoint.
        Defaults to False — full re-execution on retry.
        """
        return False

    def rollback(self, ctx: JobContext) -> None:
        """
        Best-effort rollback. Called by the executor on downstream failure.
        Default: no-op (append-only pipelines rarely need rollback).
        """

    def retry_policy(self) -> RetryPolicy:
        """Return the retry policy for this stage. Override to customize."""
        return RetryPolicy()
