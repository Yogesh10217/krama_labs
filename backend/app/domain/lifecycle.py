from app.domain.enums import ClaimStatus, JobStatus
from app.core.exceptions import KramaException
from fastapi import status

class InvalidStatusTransitionException(KramaException):
    def __init__(self, message: str):
        super().__init__(message, code="INVALID_STATUS_TRANSITION", status_code=status.HTTP_400_BAD_REQUEST)

ALLOWED_CLAIM_STATUS_TRANSITIONS = {
    ClaimStatus.DRAFT: [ClaimStatus.SUBMITTED, ClaimStatus.CANCELLED],
    ClaimStatus.SUBMITTED: [ClaimStatus.PROCESSING, ClaimStatus.CANCELLED],
    ClaimStatus.PROCESSING: [ClaimStatus.REVIEW_REQUIRED, ClaimStatus.COMPLETED, ClaimStatus.REJECTED],
    ClaimStatus.REVIEW_REQUIRED: [ClaimStatus.COMPLETED, ClaimStatus.REJECTED, ClaimStatus.PROCESSING],
    ClaimStatus.COMPLETED: [],
    ClaimStatus.REJECTED: [],
    ClaimStatus.CANCELLED: [],
}

ALLOWED_JOB_STATUS_TRANSITIONS = {
    JobStatus.PENDING: [JobStatus.QUEUED, JobStatus.CANCELLED],
    JobStatus.QUEUED: [JobStatus.RUNNING, JobStatus.CANCELLED],
    JobStatus.RUNNING: [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.SUCCEEDED: [],
    JobStatus.FAILED: [],
    JobStatus.CANCELLED: [],
}

def validate_claim_transition(current: ClaimStatus, target: ClaimStatus):
    """Validate if a claim status transition is allowed."""
    if current == target:
        return # No transition
    if target not in ALLOWED_CLAIM_STATUS_TRANSITIONS.get(current, []):
        raise InvalidStatusTransitionException(f"Cannot transition claim from {current.value} to {target.value}")

def validate_job_transition(current: JobStatus, target: JobStatus):
    """Validate if a job status transition is allowed."""
    if current == target:
        return
    if target not in ALLOWED_JOB_STATUS_TRANSITIONS.get(current, []):
        raise InvalidStatusTransitionException(f"Cannot transition job from {current.value} to {target.value}")
