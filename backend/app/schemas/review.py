import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.domain.enums import ReviewStatus, ReviewDecisionType

class ReviewDecisionCreate(BaseModel):
    validated_field_id: uuid.UUID
    decision: ReviewDecisionType
    corrected_value: Optional[str] = None
    reason: Optional[str] = None
    expected_version: Optional[int] = None

class ReviewDecisionResponse(BaseModel):
    id: uuid.UUID
    review_session_id: uuid.UUID
    validated_field_id: uuid.UUID
    decision: ReviewDecisionType
    corrected_value: Optional[str] = None
    reason: Optional[str] = None
    reviewer_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewCommentCreate(BaseModel):
    comment: str
    validated_field_id: Optional[uuid.UUID] = None

class ReviewCommentResponse(BaseModel):
    id: uuid.UUID
    review_session_id: uuid.UUID
    validated_field_id: Optional[uuid.UUID] = None
    comment: str
    reviewer_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewAssignRequest(BaseModel):
    reviewer_id: uuid.UUID
    expected_version: Optional[int] = None

class ReviewCompleteRequest(BaseModel):
    target_status: Optional[ReviewStatus] = None
    expected_version: Optional[int] = None


class ReviewHistoryMetadata(BaseModel):
    event_type: str
    description: str
    details: Dict[str, Any] = {}

class ReviewHistoryResponse(BaseModel):
    id: uuid.UUID
    review_session_id: uuid.UUID
    event: str
    actor: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewSessionResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    document_id: uuid.UUID
    assigned_user_id: Optional[uuid.UUID] = None
    status: ReviewStatus
    version: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    decisions: List[ReviewDecisionResponse] = []
    comments: List[ReviewCommentResponse] = []
    history: List[ReviewHistoryResponse] = []

    class Config:
        from_attributes = True


class FinalDocumentField(BaseModel):
    field_name: str
    final_value: str
    raw_value: Optional[str] = None
    data_type: Optional[str] = None
    source: str  # 'REVIEWER_CORRECTION' | 'VALIDATED' | 'EXTRACTED'
    validation_status: Optional[str] = None
    confidence: Optional[float] = None
    validated_field_id: Optional[uuid.UUID] = None
    decision_id: Optional[uuid.UUID] = None

class FinalDocumentView(BaseModel):
    document_id: uuid.UUID
    organization_id: uuid.UUID
    claim_id: uuid.UUID
    document_type: Optional[str] = None
    document_status: str
    review_status: Optional[str] = None
    fields: List[FinalDocumentField]
    generated_at: datetime
