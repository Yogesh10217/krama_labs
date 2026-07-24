import uuid
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

class FieldEvidenceResponse(BaseModel):
    id: uuid.UUID
    page_id: Optional[uuid.UUID]
    ocr_region_id: Optional[uuid.UUID]
    evidence_type: str
    confidence: float

class ExtractedFieldResponse(BaseModel):
    id: uuid.UUID
    field_name: str
    raw_value: Optional[str]
    normalized_value: Optional[str]
    data_type: str
    confidence: float
    evidence: List[FieldEvidenceResponse] = []

class ExtractionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    organization_id: uuid.UUID
    classification_id: uuid.UUID
    
    extractor_name: str
    extractor_version: str
    schema_name: str
    schema_version: str
    
    status: str
    fields: List[ExtractedFieldResponse] = []
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    
    class Config:
        from_attributes = True
