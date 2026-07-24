"""
app/jobs/registry.py — Concrete Pipeline Stage implementations

Each stage is a thin adapter over an existing service-layer function.
Stages NEVER instantiate services; they receive a db Session and call
service-layer functions directly, maintaining Phase 10's rule:
  "Workers must never call APIs internally; they execute service-layer
   logic directly."

Stage weights sum to 100 for clean percentage progress reporting:
  convert        → 10
  ocr            → 25
  classify       → 10
  extract        → 25
  validate       → 15
  workflow       → 10
  finalize       →  5
  ─────────────────
  Total          → 100
"""
import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.jobs.stage import PipelineStage, StageResult, RetryPolicy
from app.jobs.context import JobContext
from app.jobs.cancellation import CancellationToken
from app.domain.enums import DocumentStatus

logger = logging.getLogger(__name__)


class _BaseStage(PipelineStage):
    """Common base providing db session injection."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def can_resume(self) -> bool:
        return False

    def rollback(self, ctx: JobContext) -> None:
        pass


# ---------------------------------------------------------------------------
# Stage 1: Document Conversion (PDF → PNG pages)
# ---------------------------------------------------------------------------

class ConvertStage(_BaseStage):
    def stage_name(self) -> str:
        return "convert"

    def weight(self) -> int:
        return 10

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_attempts=2, backoff_seconds=1.0)

    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        try:
            cancellation_token.raise_if_cancelled()
            from app.services.conversion_service import ConversionService
            svc = ConversionService(self._db)
            svc.convert_document(ctx.document_id)
            logger.info("[%s] convert completed doc=%s", ctx.correlation_id, ctx.document_id)
            return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=self.weight())
        except Exception as exc:
            return StageResult(stage_name=self.stage_name(), success=False,
                               progress_contribution=0, error_message=str(exc))


# ---------------------------------------------------------------------------
# Stage 2: OCR
# ---------------------------------------------------------------------------

class OCRStage(_BaseStage):
    def stage_name(self) -> str:
        return "ocr"

    def weight(self) -> int:
        return 25

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_attempts=3, backoff_seconds=2.0, backoff_multiplier=2.0)

    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        try:
            cancellation_token.raise_if_cancelled()
            from app.services.ocr_service import OCRService
            svc = OCRService(self._db)
            svc.process_document(ctx.document_id)
            logger.info("[%s] ocr completed doc=%s", ctx.correlation_id, ctx.document_id)
            return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=self.weight())
        except Exception as exc:
            return StageResult(stage_name=self.stage_name(), success=False,
                               progress_contribution=0, error_message=str(exc))


# ---------------------------------------------------------------------------
# Stage 3: Classification
# ---------------------------------------------------------------------------

class ClassifyStage(_BaseStage):
    def stage_name(self) -> str:
        return "classify"

    def weight(self) -> int:
        return 10

    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        try:
            cancellation_token.raise_if_cancelled()
            from app.services.classification_service import ClassificationService
            svc = ClassificationService(self._db)
            svc.classify_document(ctx.document_id)
            logger.info("[%s] classify completed doc=%s", ctx.correlation_id, ctx.document_id)
            return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=self.weight())
        except Exception as exc:
            return StageResult(stage_name=self.stage_name(), success=False,
                               progress_contribution=0, error_message=str(exc))


# ---------------------------------------------------------------------------
# Stage 4: Extraction
# ---------------------------------------------------------------------------

class ExtractStage(_BaseStage):
    def stage_name(self) -> str:
        return "extract"

    def weight(self) -> int:
        return 25

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_attempts=3, backoff_seconds=3.0, backoff_multiplier=2.0)

    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        try:
            cancellation_token.raise_if_cancelled()
            from app.services.extraction_service import ExtractionService
            svc = ExtractionService(self._db)
            svc.extract_document(ctx.document_id)
            logger.info("[%s] extract completed doc=%s", ctx.correlation_id, ctx.document_id)
            return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=self.weight())
        except Exception as exc:
            return StageResult(stage_name=self.stage_name(), success=False,
                               progress_contribution=0, error_message=str(exc))


# ---------------------------------------------------------------------------
# Stage 5: Validation
# ---------------------------------------------------------------------------

class ValidateStage(_BaseStage):
    def stage_name(self) -> str:
        return "validate"

    def weight(self) -> int:
        return 15

    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        try:
            cancellation_token.raise_if_cancelled()
            from app.services.validation_service import ValidationService
            svc = ValidationService(self._db)
            svc.validate_document(ctx.document_id)
            logger.info("[%s] validate completed doc=%s", ctx.correlation_id, ctx.document_id)
            return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=self.weight())
        except Exception as exc:
            return StageResult(stage_name=self.stage_name(), success=False,
                               progress_contribution=0, error_message=str(exc))


# ---------------------------------------------------------------------------
# Stage 6: Workflow (auto-approve or create review)
# ---------------------------------------------------------------------------

class WorkflowStage(_BaseStage):
    def stage_name(self) -> str:
        return "workflow"

    def weight(self) -> int:
        return 10

    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        try:
            cancellation_token.raise_if_cancelled()
            from app.services.workflow_orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator(self._db)
            orchestrator.process_document(ctx.document_id)
            logger.info("[%s] workflow completed doc=%s", ctx.correlation_id, ctx.document_id)
            return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=self.weight())
        except Exception as exc:
            return StageResult(stage_name=self.stage_name(), success=False,
                               progress_contribution=0, error_message=str(exc))


# ---------------------------------------------------------------------------
# Stage 7: Finalization (mark FINALIZED)
# ---------------------------------------------------------------------------

class FinalizeStage(_BaseStage):
    def stage_name(self) -> str:
        return "finalize"

    def weight(self) -> int:
        return 5

    def execute(
        self,
        ctx: JobContext,
        cancellation_token: CancellationToken,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        try:
            cancellation_token.raise_if_cancelled()
            from app.repositories.document import DocumentRepository
            repo = DocumentRepository(self._db)
            doc = repo.get(ctx.document_id)
            if doc:
                doc.status = DocumentStatus.FINALIZED.value
                self._db.commit()
            logger.info("[%s] finalize completed doc=%s", ctx.correlation_id, ctx.document_id)
            return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=self.weight())
        except Exception as exc:
            return StageResult(stage_name=self.stage_name(), success=False,
                               progress_contribution=0, error_message=str(exc))


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def build_document_pipeline(db: Session) -> list:
    """
    Return the ordered list of stages for DOCUMENT_PROCESSING jobs.
    Weights must sum to 100.
    """
    return [
        ConvertStage(db),
        OCRStage(db),
        ClassifyStage(db),
        ExtractStage(db),
        ValidateStage(db),
        WorkflowStage(db),
        FinalizeStage(db),
    ]
