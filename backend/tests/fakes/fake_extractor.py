import uuid
from typing import List
from app.extraction.base import StructuredExtractor, ExtractionInput, ExtractionResult, ExtractedFieldData, FieldEvidenceData

class FakeExtractor(StructuredExtractor):
    def __init__(self):
        self.should_fail = False

    def extract(self, input_data: ExtractionInput) -> ExtractionResult:
        if self.should_fail:
            raise Exception("Fake extraction failure")
            
        fields = []
        if input_data.extraction_schema.schema_name == "aadhaar_card_extraction":
            fields.append(ExtractedFieldData(
                name="aadhaar_number",
                raw_value="1234 5678 9012",
                normalized_value="1234 5678 9012",
                data_type="IDENTIFIER",
                confidence=0.99,
                evidence=[FieldEvidenceData(
                    page_id=input_data.pages[0].page_id if input_data.pages else uuid.uuid4(),
                    ocr_region_id=input_data.regions[0].id if input_data.regions else uuid.uuid4(),
                    rule_id="fake_rule",
                    confidence=0.99
                )]
            ))
            
        return ExtractionResult(
            extractor_name="fake_extractor",
            extractor_version="1.0",
            schema_name=input_data.extraction_schema.schema_name,
            schema_version=input_data.extraction_schema.schema_version,
            fields=fields
        )
