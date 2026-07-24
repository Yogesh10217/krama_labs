from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict

from app.domain.enums import ValidationStatus
from app.db.models.ocr import OCRPageResult, OCRRegion
from app.db.models.extraction import ExtractedField

class ValidationEvidenceModel(BaseModel):
    page_id: uuid.UUID
    ocr_region_id: uuid.UUID
    support_type: str
    confidence: float

class FieldValidationResult(BaseModel):
    extracted_field_id: uuid.UUID
    validation_status: ValidationStatus
    validation_score: float
    validation_reason: str
    evidence: List[ValidationEvidenceModel] = Field(default_factory=list)

class ValidationResult(BaseModel):
    validator_name: str
    validator_version: str
    fields: List[FieldValidationResult]

class ValidationInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    document_id: uuid.UUID
    document_type: str
    pages: List[OCRPageResult]
    regions: List[OCRRegion]
    extracted_fields: List[ExtractedField]

class Validator(ABC):
    @abstractmethod
    def validate(self, input_data: ValidationInput) -> ValidationResult:
        """Validates extracted fields against OCR evidence."""
        pass
