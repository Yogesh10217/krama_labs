import uuid
import logging
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app.db.models.document import Document
from app.db.models.validation import ValidationRun
from app.db.models.review import ReviewSession
from app.services.review_service import ReviewService
from app.workflow.policies import AutoApprovalPolicy
from app.core.exceptions import KramaException

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    """Decouples ValidationService and ReviewService. Consumes ValidationRun and orchestrates workflow decisions."""

    def __init__(self, db: DBSession):
        self.db = db
        self.review_service = ReviewService(db)

    def process_validation_result(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        validation_run_id: Optional[uuid.UUID] = None
    ) -> ReviewSession:
        doc = self.db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == organization_id
        ).first()

        if not doc:
            raise KramaException(f"Document {document_id} not found", code="DOCUMENT_NOT_FOUND", status_code=404)

        if validation_run_id:
            val_run = self.db.query(ValidationRun).filter(
                ValidationRun.id == validation_run_id,
                ValidationRun.organization_id == organization_id
            ).first()
        else:
            val_run = self.db.query(ValidationRun).filter(
                ValidationRun.organization_id == organization_id,
                ValidationRun.document_id == document_id
            ).order_by(ValidationRun.created_at.desc()).first()

        if not val_run:
            raise KramaException(f"No validation run found for document {document_id}", code="VALIDATION_RUN_NOT_FOUND", status_code=404)

        can_auto_approve, reason = AutoApprovalPolicy.evaluate(val_run, doc.document_type)

        session = self.review_service.create_session(
            organization_id=organization_id,
            document_id=document_id,
            auto_approve=can_auto_approve,
            reason=reason
        )

        logger.info(f"workflow_processed document_id={document_id} auto_approved={can_auto_approve} reason={reason}")
        return session
