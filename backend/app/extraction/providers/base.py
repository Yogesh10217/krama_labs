import uuid
from typing import List, Dict, Any, Optional
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

class PromptPackage(BaseModel):
    system_prompt: str
    user_prompt: str
    schema_json: str
    version: str

class ExtractionRequest(BaseModel):
    organization_id: uuid.UUID
    document_id: uuid.UUID
    document_type: str
    schema: DocumentSchema
    ocr_pages: List[Any]
    ocr_regions: List[Any]
    language: str = "en"
    options: Dict[str, Any] = {}

class ExtractionResponse(BaseModel):
    provider: str
    model: str
    provider_version: str
    schema_version: str
    fields: List[ExtractedFieldData]
    confidence: float = 0.0
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    request_id: Optional[str] = None
    finish_reason: Optional[str] = None
    cached: bool = False
    prompt_version: Optional[str] = None
    provider_input_hash: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ExtractionProvider:
    def initialize(self) -> None:
        """Initialize any required resources (connections, models)."""
        pass

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        """Execute the extraction logic."""
        raise NotImplementedError

    def health(self) -> bool:
        """Check provider health and availability."""
        raise NotImplementedError

    def supported_models(self) -> List[str]:
        """List models supported by this provider."""
        raise NotImplementedError

    def provider_name(self) -> str:
        """Return the canonical provider name."""
        raise NotImplementedError

    def provider_version(self) -> str:
        """Return the provider implementation version."""
        raise NotImplementedError
