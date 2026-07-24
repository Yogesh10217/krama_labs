import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session as DBSession

from app.db.models.document import Document
from app.db.models.validation import ValidationRun, ValidatedField
from app.db.models.extraction import ExtractionRun, ExtractedField
from app.db.models.review import ReviewSession, ReviewDecision
from app.domain.enums import ReviewDecisionType
from app.schemas.review import FinalDocumentView, FinalDocumentField
from app.core.exceptions import KramaException

class FinalDocumentResolver:
    """Computes the authoritative FinalDocumentView on-the-fly without mutating canonical artifacts."""
    
    def __init__(self, db: DBSession):
        self.db = db

    def resolve(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> FinalDocumentView:
        # 1. Fetch document (with tenant isolation)
        doc = self.db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == organization_id
        ).first()
        
        if not doc:
            raise KramaException(f"Document {document_id} not found", code="DOCUMENT_NOT_FOUND", status_code=404)

        # Fetch latest review session if any
        review_session = self.db.query(ReviewSession).filter(
            ReviewSession.organization_id == organization_id,
            ReviewSession.document_id == document_id
        ).first()

        # Build decision map if review session exists
        decision_map: Dict[str, ReviewDecision] = {}
        if review_session:
            for d in review_session.decisions:
                decision_map[str(d.validated_field_id)] = d

        # Fetch latest validation run
        val_run = self.db.query(ValidationRun).filter(
            ValidationRun.organization_id == organization_id,
            ValidationRun.document_id == document_id
        ).order_by(ValidationRun.created_at.desc()).first()

        fields: List[FinalDocumentField] = []

        if val_run and val_run.fields:
            for vf in val_run.fields:
                ext_field = vf.extracted_field
                field_name = ext_field.field_name if ext_field else "unknown_field"
                data_type = ext_field.data_type if ext_field else "STRING"
                raw_val = ext_field.raw_value if ext_field else ""
                norm_val = ext_field.normalized_value if ext_field else raw_val

                decision = decision_map.get(str(vf.id))

                if decision and decision.decision == ReviewDecisionType.CORRECT and decision.corrected_value is not None:
                    final_val = decision.corrected_value
                    source = "REVIEWER_CORRECTION"
                    decision_id = decision.id
                elif decision and decision.decision == ReviewDecisionType.APPROVE:
                    final_val = decision.corrected_value if decision.corrected_value is not None else (norm_val or raw_val)
                    source = "REVIEWER_CORRECTION" if decision.corrected_value is not None else "VALIDATED"
                    decision_id = decision.id
                elif decision and decision.decision == ReviewDecisionType.REJECT:
                    final_val = "[REJECTED]"
                    source = "REVIEWER_CORRECTION"
                    decision_id = decision.id
                else:
                    final_val = norm_val or raw_val
                    source = "VALIDATED"
                    decision_id = None

                fields.append(FinalDocumentField(
                    field_name=field_name,
                    final_value=final_val,
                    raw_value=raw_val,
                    data_type=data_type,
                    source=source,
                    validation_status=vf.validation_status.value if vf.validation_status else None,
                    confidence=vf.validation_score,
                    validated_field_id=vf.id,
                    decision_id=decision_id
                ))
        else:
            # Fallback to ExtractionRun if validation run is missing
            ext_run = self.db.query(ExtractionRun).filter(
                ExtractionRun.organization_id == organization_id,
                ExtractionRun.document_id == document_id
            ).order_by(ExtractionRun.created_at.desc()).first()

            if ext_run and ext_run.fields:
                for ef in ext_run.fields:
                    fields.append(FinalDocumentField(
                        field_name=ef.field_name,
                        final_value=ef.normalized_value or ef.raw_value,
                        raw_value=ef.raw_value,
                        data_type=ef.data_type,
                        source="EXTRACTED",
                        validation_status=None,
                        confidence=ef.confidence,
                        validated_field_id=None,
                        decision_id=None
                    ))

        return FinalDocumentView(
            document_id=doc.id,
            organization_id=doc.organization_id,
            claim_id=doc.claim_id,
            document_type=doc.document_type,
            document_status=doc.status.value if hasattr(doc.status, "value") else str(doc.status),
            review_status=review_session.status.value if review_session and hasattr(review_session.status, "value") else (review_session.status if review_session else None),
            fields=fields,
            generated_at=datetime.now(timezone.utc)
        )
