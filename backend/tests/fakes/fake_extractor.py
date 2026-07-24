import uuid
from typing import List
from app.extraction.providers.base import ExtractionProvider, ExtractionRequest, ExtractionResponse, ExtractedFieldData, FieldEvidenceData

class FakeExtractor(ExtractionProvider):
    def __init__(self):
        self.should_fail = False

    def initialize(self) -> None:
        pass

    def health(self) -> bool:
        return True

    def supported_models(self) -> List[str]:
        return ["fake_model"]

    def provider_name(self) -> str:
        return "fake_provider"

    def provider_version(self) -> str:
        return "1.0"

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        if self.should_fail:
            raise Exception("Fake extraction failure")
            
        fields = []
        if request.schema.schema_name == "aadhaar_card_extraction":
            fields.append(ExtractedFieldData(
                name="aadhaar_number",
                raw_value="1234 5678 9012",
                normalized_value="1234 5678 9012",
                data_type="IDENTIFIER",
                confidence=0.99,
                evidence=[FieldEvidenceData(
                    page_id=request.ocr_pages[0].page_id if request.ocr_pages else uuid.uuid4(),
                    ocr_region_id=request.ocr_regions[0].id if request.ocr_regions else uuid.uuid4(),
                    rule_id="fake_rule",
                    confidence=0.99
                )]
            ))
            
        return ExtractionResponse(
            provider="fake_provider",
            model="fake_model",
            provider_version="1.0",
            schema_version=request.schema.schema_version,
            fields=fields,
            confidence=0.99,
            latency_ms=10,
            prompt_tokens=100,
            completion_tokens=50
        )
