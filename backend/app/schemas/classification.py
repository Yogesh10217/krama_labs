from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel

class ClassifierInfo(BaseModel):
    name: str
    version: str

class ClassificationEvidence(BaseModel):
    rule: Optional[str] = None
    score: Optional[float] = None
    max_possible: Optional[float] = None
    matched_keywords: Optional[List[str]] = None
    reason: Optional[str] = None
    
    model_config = {"extra": "allow"}

class ClassificationResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    document_type: str
    confidence: float
    classifier_name: str
    classifier_version: str
    evidence_json: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}
