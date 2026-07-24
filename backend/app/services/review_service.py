import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session as DBSession

from app.db.models.document import Document
from app.db.models.validation import ValidationRun, ValidatedField
from app.db.models.review import ReviewSession, ReviewDecision, ReviewComment, ReviewHistory
from app.domain.enums import DocumentStatus, ReviewStatus, ReviewDecisionType
from app.workflow.policies import AssignmentPolicy, CompletionPolicy
from app.schemas.review import ReviewHistoryMetadata
from app.core.exceptions import (
    ReviewSessionNotFoundException,
    ConcurrentReviewConflictException,
    ReviewStateInvalidException,
    KramaException
)

logger = logging.getLogger(__name__)

class ReviewService:
    def __init__(self, db: DBSession):
        self.db = db

    def _get_session_by_doc(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> ReviewSession:
        session = self.db.query(ReviewSession).filter(
            ReviewSession.organization_id == organization_id,
            ReviewSession.document_id == document_id
        ).first()
        if not session:
            raise ReviewSessionNotFoundException(str(document_id))
        return session

    def _verify_optimistic_lock(self, session: ReviewSession, expected_version: Optional[int]):
        if expected_version is not None and session.version != expected_version:
            raise ConcurrentReviewConflictException(
                f"Review session version mismatch (current: {session.version}, expected: {expected_version})"
            )

    def _log_history_event(
        self,
        session: ReviewSession,
        event: str,
        actor: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ):
        meta = ReviewHistoryMetadata(
            event_type=event,
            description=description,
            details=details or {}
        )
        history_entry = ReviewHistory(
            review_session_id=session.id,
            event=event,
            actor=actor,
            metadata_json=meta.model_dump()
        )
        self.db.add(history_entry)

    def create_session(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        auto_approve: bool = False,
        reason: str = ""
    ) -> ReviewSession:
        # Verify document exists and belongs to org
        doc = self.db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == organization_id
        ).first()
        if not doc:
            raise KramaException(f"Document {document_id} not found for tenant isolation", code="DOCUMENT_NOT_FOUND", status_code=404)

        # Check if session already exists
        existing = self.db.query(ReviewSession).filter(
            ReviewSession.organization_id == organization_id,
            ReviewSession.document_id == document_id
        ).first()
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        if auto_approve:
            status = ReviewStatus.AUTO_APPROVED
            completed_at = now
            doc.status = DocumentStatus.AUTO_APPROVED
        else:
            status = ReviewStatus.PENDING_REVIEW
            completed_at = None
            doc.status = DocumentStatus.REVIEW_PENDING

        session = ReviewSession(
            organization_id=organization_id,
            document_id=document_id,
            status=status,
            version=1,
            started_at=now,
            completed_at=completed_at
        )
        self.db.add(session)
        self.db.flush()

        event_name = "auto_approved" if auto_approve else "review_started"
        actor_name = "SYSTEM"
        desc = f"Review session auto-approved: {reason}" if auto_approve else "Review session created and pending human review"

        self._log_history_event(
            session=session,
            event=event_name,
            actor=actor_name,
            description=desc,
            details={"auto_approve": auto_approve, "reason": reason}
        )

        self.db.commit()
        self.db.refresh(session)

        if auto_approve:
            logger.info(f"auto_approved document_id={document_id} reason={reason}")
        else:
            logger.info(f"review_started document_id={document_id} session_id={session.id}")

        return session

    def assign_reviewer(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        expected_version: Optional[int] = None
    ) -> ReviewSession:
        session = self._get_session_by_doc(organization_id, document_id)
        self._verify_optimistic_lock(session, expected_version)

        is_valid, msg = AssignmentPolicy.validate_assignment(session, str(reviewer_id))
        if not is_valid:
            raise ReviewStateInvalidException(msg)

        old_assignee = str(session.assigned_user_id) if session.assigned_user_id else None
        session.assigned_user_id = reviewer_id
        session.version += 1

        if session.status == ReviewStatus.PENDING_REVIEW:
            session.status = ReviewStatus.IN_REVIEW
            doc = session.document
            if doc:
                doc.status = DocumentStatus.UNDER_REVIEW

        self._log_history_event(
            session=session,
            event="review_assigned",
            actor=str(reviewer_id),
            description=f"Assigned reviewer {reviewer_id}",
            details={"previous_assignee": old_assignee, "new_assignee": str(reviewer_id)}
        )

        self.db.commit()
        self.db.refresh(session)
        logger.info(f"review_assigned document_id={document_id} reviewer_id={reviewer_id} version={session.version}")
        return session

    def record_decision(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        validated_field_id: uuid.UUID,
        decision_type: ReviewDecisionType,
        reviewer_id: uuid.UUID,
        corrected_value: Optional[str] = None,
        reason: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> ReviewDecision:
        session = self._get_session_by_doc(organization_id, document_id)
        self._verify_optimistic_lock(session, expected_version)

        if session.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.AUTO_APPROVED]:
            raise ReviewStateInvalidException(f"Cannot record decision for closed review session in status {session.status.value}")

        # Verify validated field exists and belongs to this document's validation run
        vf = self.db.query(ValidatedField).filter(ValidatedField.id == validated_field_id).first()
        if not vf:
            raise KramaException(f"Validated field {validated_field_id} not found", code="VALIDATED_FIELD_NOT_FOUND", status_code=404)

        # Upsert decision
        existing_decision = self.db.query(ReviewDecision).filter(
            ReviewDecision.review_session_id == session.id,
            ReviewDecision.validated_field_id == validated_field_id
        ).first()

        if existing_decision:
            existing_decision.decision = decision_type
            existing_decision.corrected_value = corrected_value
            existing_decision.reason = reason
            existing_decision.reviewer_id = reviewer_id
            decision_obj = existing_decision
        else:
            decision_obj = ReviewDecision(
                review_session_id=session.id,
                validated_field_id=validated_field_id,
                decision=decision_type,
                corrected_value=corrected_value,
                reason=reason,
                reviewer_id=reviewer_id
            )
            self.db.add(decision_obj)

        session.version += 1
        if session.status == ReviewStatus.PENDING_REVIEW:
            session.status = ReviewStatus.IN_REVIEW
            if session.document:
                session.document.status = DocumentStatus.UNDER_REVIEW

        field_name = vf.extracted_field.field_name if vf.extracted_field else str(validated_field_id)
        event_type = "field_corrected" if decision_type == ReviewDecisionType.CORRECT else "field_decision_recorded"

        self._log_history_event(
            session=session,
            event=event_type,
            actor=str(reviewer_id),
            description=f"Field '{field_name}' decision set to {decision_type.value}",
            details={
                "validated_field_id": str(validated_field_id),
                "field_name": field_name,
                "decision": decision_type.value,
                "corrected_value": corrected_value,
                "reason": reason
            }
        )

        self.db.commit()
        self.db.refresh(decision_obj)
        self.db.refresh(session)
        logger.info(f"field_corrected document_id={document_id} field_id={validated_field_id} decision={decision_type.value}")
        return decision_obj

    def add_comment(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        comment_text: str,
        reviewer_id: uuid.UUID,
        validated_field_id: Optional[uuid.UUID] = None
    ) -> ReviewComment:
        session = self._get_session_by_doc(organization_id, document_id)

        comment_obj = ReviewComment(
            review_session_id=session.id,
            validated_field_id=validated_field_id,
            comment=comment_text,
            reviewer_id=reviewer_id
        )
        self.db.add(comment_obj)

        self._log_history_event(
            session=session,
            event="comment_added",
            actor=str(reviewer_id),
            description=f"Added comment on {'field ' + str(validated_field_id) if validated_field_id else 'session'}",
            details={"comment": comment_text, "validated_field_id": str(validated_field_id) if validated_field_id else None}
        )

        self.db.commit()
        self.db.refresh(comment_obj)
        return comment_obj

    def complete_review(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        target_status: Optional[ReviewStatus] = None,
        expected_version: Optional[int] = None
    ) -> ReviewSession:
        session = self._get_session_by_doc(organization_id, document_id)
        self._verify_optimistic_lock(session, expected_version)

        # Get validation run fields for completion policy evaluation
        val_run = session.document.validation_runs[0] if session.document.validation_runs else None
        val_fields = val_run.fields if val_run else []

        is_valid, final_status, msg = CompletionPolicy.evaluate_completion(
            session=session,
            validated_fields=val_fields,
            decisions=session.decisions,
            target_status=target_status
        )

        if not is_valid:
            raise ReviewStateInvalidException(msg)

        now = datetime.now(timezone.utc)
        session.status = final_status
        session.completed_at = now
        session.version += 1

        doc = session.document
        if doc:
            doc.status = DocumentStatus.REVIEW_COMPLETED
            self.db.flush()
            # Requirement #9: Separate workflow completion from final business completion by introducing a FINALIZED document state after REVIEW_COMPLETED
            doc.status = DocumentStatus.FINALIZED

        self._log_history_event(
            session=session,
            event="review_completed",
            actor=str(reviewer_id),
            description=f"Review completed with status {final_status.value}",
            details={"final_status": final_status.value, "reason": msg}
        )

        self.db.commit()
        self.db.refresh(session)
        logger.info(f"review_completed document_id={document_id} final_status={final_status.value}")
        return session

    def get_review_session(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> ReviewSession:
        return self._get_session_by_doc(organization_id, document_id)
