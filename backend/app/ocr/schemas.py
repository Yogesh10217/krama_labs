"""Pydantic schemas for canonical OCR artifact serialization and API responses."""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class OCRRegionArtifact(BaseModel):
    """Single OCR region in the canonical JSON artifact."""
    region_index: int
    reading_order: int
    text: str
    confidence: float
    bounding_box: dict  # {"x1": f, "y1": f, "x2": f, "y2": f}
    polygon: Optional[List[List[float]]] = None
    region_type: str = "TEXT"


class OCRArtifact(BaseModel):
    """Canonical versioned OCR JSON artifact for a single page."""
    schema_version: str = "1.0"
    page_id: str
    page_number: int
    engine: str
    engine_version: str
    language: str
    page_width: int
    page_height: int
    full_text: str
    average_confidence: float
    region_count: int
    regions: List[OCRRegionArtifact]


# ─── API Response Schemas ─────────────────────────────────────────────────────

class OCRRegionResponse(BaseModel):
    """API response for a single OCR region."""
    id: uuid.UUID
    region_index: int
    reading_order: int
    text: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    polygon_json: Optional[str] = None
    region_type: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class OCRPageResultResponse(BaseModel):
    """API response for a page's OCR result."""
    id: uuid.UUID
    page_id: uuid.UUID
    engine: str
    engine_version: str
    language: str
    full_text: str
    region_count: int
    average_confidence: float
    processing_time_ms: float
    artifact_storage_key: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PageOCRDetailResponse(BaseModel):
    """Full OCR detail for a page including regions."""
    result: OCRPageResultResponse
    regions: List[OCRRegionResponse]


class DocumentOCRSummaryResponse(BaseModel):
    """Summary response after document OCR."""
    document_id: uuid.UUID
    status: str
    page_count: int
    ocr_pages_completed: int
    ocr_pages_failed: int
    total_regions: int


class DocumentOCRDetailResponse(BaseModel):
    """Full OCR detail for document (all pages)."""
    document_id: uuid.UUID
    status: str
    pages: List[PageOCRDetailResponse]
