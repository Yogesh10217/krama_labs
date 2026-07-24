import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from app.extraction.schemas import DocumentSchema

class FieldEvidenceData(BaseModel):
    page_id: Optional[uuid.UUID] = None
    ocr_region_id: Optional[uuid.UUID] = None
    rule_id: str
    confidence: float = 0.0

class ExtractedFieldData(BaseModel):
    name: str
    raw_value: str
    normalized_value: str
    data_type: str
    confidence: float
    evidence: List[FieldEvidenceData]

class ExtractionResult(BaseModel):
    extractor_name: str
    extractor_version: str
    schema_name: str
    schema_version: str
    fields: List[ExtractedFieldData]

class ExtractionInput(BaseModel):
    document_id: uuid.UUID
    document_type: str
    extraction_schema: DocumentSchema
    pages: List[Any]  # List of OCRPageResult
    regions: List[Any] # List of OCRRegion

class StructuredExtractor:
    def extract(self, input_data: ExtractionInput) -> ExtractionResult:
        raise NotImplementedError
