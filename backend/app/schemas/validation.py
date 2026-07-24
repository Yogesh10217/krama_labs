from datetime import datetime
from typing import List, Optional, Dict
import uuid
from pydantic import BaseModel, ConfigDict

from app.domain.enums import ValidationStatus

class ValidationEvidenceSchema(BaseModel):
    id: uuid.UUID
    validated_field_id: uuid.UUID
    page_id: uuid.UUID
    ocr_region_id: uuid.UUID
    support_type: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ValidatedFieldSchema(BaseModel):
    id: uuid.UUID
    extracted_field_id: uuid.UUID
    validation_status: ValidationStatus
    validation_score: Optional[float]
    validation_reason: Optional[str]
    evidence: List[ValidationEvidenceSchema]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ValidationRunSchema(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    extraction_run_id: uuid.UUID
    validator_name: str
    validator_version: str
    status: str
    artifact_storage_key: str
    started_at: datetime
    completed_at: Optional[datetime]
    processing_time_ms: Optional[float]
    fields: List[ValidatedFieldSchema]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ValidationSummarySchema(BaseModel):
    validation_run: ValidationRunSchema
    summary: Dict[ValidationStatus, int]
