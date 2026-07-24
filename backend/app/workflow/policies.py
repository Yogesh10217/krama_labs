from typing import List, Dict, Any, Tuple, Optional
from app.core.config import Config
from app.domain.enums import ReviewStatus, ReviewDecisionType, ValidationStatus
from app.db.models.validation import ValidationRun, ValidatedField
from app.db.models.review import ReviewSession, ReviewDecision

class CriticalFieldPolicy:
    @staticmethod
    def get_critical_fields(document_type: Optional[str] = None) -> List[str]:
        raw_fields = Config.CRITICAL_FIELDS
        if not raw_fields:
            return []
        return [f.strip().lower() for f in raw_fields.split(",") if f.strip()]

    @staticmethod
    def is_critical(field_name: str, document_type: Optional[str] = None) -> bool:
        critical_list = CriticalFieldPolicy.get_critical_fields(document_type)
        return field_name.lower() in critical_list


class AutoApprovalPolicy:
    @staticmethod
    def evaluate(validation_run: ValidationRun, document_type: Optional[str] = None) -> Tuple[bool, str]:
        # 1. Check if document type explicitly requires human review
        forced_types = [t.strip().lower() for t in Config.REQUIRE_REVIEW_FOR_DOCUMENT_TYPES.split(",") if t.strip()]
        if document_type and document_type.lower() in forced_types:
            return False, f"Document type '{document_type}' is configured to require human review"

        if not validation_run.fields:
            return False, "Validation run contains no fields"

        threshold = Config.AUTO_APPROVAL_THRESHOLD
        scores = []
        
        # 2. Check critical fields & individual scores
        for vf in validation_run.fields:
            field_name = vf.extracted_field.field_name if vf.extracted_field else ""
            score = vf.validation_score if vf.validation_score is not None else 0.0
            scores.append(score)
            
            # If critical field fails validation
            if CriticalFieldPolicy.is_critical(field_name, document_type):
                if vf.validation_status in [ValidationStatus.UNSUPPORTED, ValidationStatus.MISSING_EVIDENCE]:
                    return False, f"Critical field '{field_name}' failed validation status ({vf.validation_status.value})"
                if score < threshold:
                    return False, f"Critical field '{field_name}' score ({score}) below threshold ({threshold})"

        # 3. Check overall average score
        avg_score = sum(scores) / len(scores) if scores else 0.0
        if avg_score < threshold:
            return False, f"Overall validation score ({avg_score:.2f}) below threshold ({threshold})"

        return True, f"Validation score ({avg_score:.2f}) satisfies auto-approval criteria"


class AssignmentPolicy:
    @staticmethod
    def validate_assignment(session: ReviewSession, reviewer_id: str) -> Tuple[bool, str]:
        if session.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.AUTO_APPROVED]:
            return False, f"Cannot reassign review session in final state '{session.status.value}'"
        if not reviewer_id:
            return False, "Reviewer ID cannot be empty"
        return True, "Assignment valid"


class CompletionPolicy:
    @staticmethod
    def evaluate_completion(
        session: ReviewSession,
        validated_fields: List[ValidatedField],
        decisions: List[ReviewDecision],
        target_status: Optional[ReviewStatus] = None
    ) -> Tuple[bool, ReviewStatus, str]:
        if session.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.AUTO_APPROVED]:
            return False, session.status, f"Session is already closed in state '{session.status.value}'"

        decision_map: Dict[str, ReviewDecision] = {str(d.validated_field_id): d for d in decisions}
        
        has_rejections = False
        unresolved_critical = []
        
        for vf in validated_fields:
            field_name = vf.extracted_field.field_name if vf.extracted_field else ""
            field_id_str = str(vf.id)
            decision = decision_map.get(field_id_str)
            
            if decision:
                if decision.decision == ReviewDecisionType.REJECT:
                    has_rejections = True
            else:
                # Field has no decision
                if CriticalFieldPolicy.is_critical(field_name):
                    unresolved_critical.append(field_name)

        if unresolved_critical:
            return False, session.status, f"Cannot complete review: Critical fields unresolved: {', '.join(unresolved_critical)}"

        # Determine final status
        if target_status == ReviewStatus.REJECTED or has_rejections:
            final_status = ReviewStatus.REJECTED
        elif target_status == ReviewStatus.PARTIALLY_APPROVED:
            final_status = ReviewStatus.PARTIALLY_APPROVED
        else:
            final_status = ReviewStatus.APPROVED

        return True, final_status, f"Review completed with status '{final_status.value}'"
