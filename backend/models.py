"""Data models for Document Intelligence backend."""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class DocumentType(Enum):
    PDF = "pdf"
    PPTX = "pptx"
    EXCEL = "excel"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FLAGGED = "flagged"


class ValidationStatus(Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"
    CONFLICT = "conflict"


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    page: int = 0

    @property
    def xyxy(self) -> List[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class OCRRegion:
    text: str
    bbox: BoundingBox
    confidence: float
    page_num: int = 0


@dataclass
class GroundedValue:
    field_name: str
    value: str
    source_text: str
    bbox: Optional[BoundingBox]
    confidence: float
    match_score: float
    extraction_method: str


@dataclass
class ValidationResult:
    field_name: str
    ocr_value: str = ""
    ocr_confidence: float = 0.0
    ocr_bbox: Optional[BoundingBox] = None
    vlm_value: str = ""
    vlm_confidence: float = 0.0
    structure_value: str = ""
    structure_confidence: float = 0.0
    final_value: str = ""
    final_confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.FLAGGED
    validation_status: ValidationStatus = ValidationStatus.UNVERIFIED
    is_grounded: bool = False
    grounding_proof: Optional[GroundedValue] = None
    is_flagged: bool = True
    flag_reasons: List[str] = field(default_factory=list)


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    chunk_type: str  # 'text', 'table', 'heading', 'list_item', 'table_row'
    bbox: Optional[BoundingBox]
    page_num: int
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "type": self.chunk_type,
            "bbox": self.bbox.xyxy if self.bbox else None,
            "page": self.page_num,
            "confidence": round(self.confidence, 4),
            "metadata": self.metadata,
        }


@dataclass
class PageResult:
    page_num: int
    ocr_regions: List[OCRRegion]
    extracted_data: Dict[str, Any]
    validation_results: List[ValidationResult]
    chunks: List[DocumentChunk] = field(default_factory=list)
    markdown: str = ""


@dataclass
class DocumentResult:
    document_id: str
    file_path: str
    document_type: DocumentType
    document_class: str
    pages: List[PageResult]
    chunks: List[DocumentChunk]
    extracted_data: Dict[str, Any]
    validation_results: List[ValidationResult]
    overall_confidence: float
    accuracy_score: float
    grounding_coverage: float
    flagged_fields: List[str]
    processing_time: float
    markdown_content: str = ""
    document_category: str = ""
    document_label: str = ""
    classify_confidence: float = 0.0

    def to_json(self) -> Dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "document_class": self.document_class,
            "document_category": self.document_category,
            "document_label": self.document_label,
            "classify_confidence": round(self.classify_confidence, 4),
            "data": self.extracted_data,
            "markdown": self.markdown_content,
            "pages": [
                {
                    "page_num": p.page_num,
                    "document_type": self.document_label or self.document_class,
                    "extracted_data": {k: v for k, v in p.extracted_data.items() if not k.startswith("_")},
                    "ocr_regions": [
                        {"text": r.text, "bbox": r.bbox.xyxy, "confidence": round(r.confidence, 4)}
                        for r in p.ocr_regions
                    ],
                    "validation": [
                        {
                            "field_name": v.field_name,
                            "final_value": v.final_value,
                            "final_score": round(v.final_confidence, 4),
                            "ocr_score": round(v.ocr_confidence, 4),
                            "structure_score": round(getattr(v, 'structure_confidence', 0.0), 4),
                            "status": v.validation_status.value,
                        }
                        for v in p.validation_results
                    ],
                    "markdown": p.markdown,
                    "chunks": [c.to_dict() for c in p.chunks] if p.chunks else [],
                }
                for p in self.pages
            ],
            "chunks": [c.to_dict() for c in self.chunks],
            "validation": {
                "overall_confidence": round(self.overall_confidence, 4),
                "accuracy_score": round(self.accuracy_score, 4),
                "grounding_coverage": round(self.grounding_coverage, 4),
                "flagged_fields": self.flagged_fields,
            },
            "grounding": [
                {
                    "field": v.field_name,
                    "value": v.final_value,
                    "bbox": v.grounding_proof.bbox.xyxy
                    if v.grounding_proof and v.grounding_proof.bbox
                    else None,
                    "confidence": round(v.final_confidence, 4),
                    "status": v.validation_status.value,
                }
                for v in self.validation_results
                if v.final_value
            ],
            "processing_time": round(self.processing_time, 2),
        }
