import re
from typing import Dict, List, Optional
from app.extraction.base import StructuredExtractor, ExtractionInput, ExtractionResult, ExtractedFieldData, FieldEvidenceData
from app.extraction.normalizer import ExtractionNormalizer

class RulesExtractor(StructuredExtractor):
    def __init__(self):
        self.patterns = {
            "aadhaar_number": re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b'),
            "pan_number": re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b'),
            "date": re.compile(r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b'),
            "currency": re.compile(r'(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)', re.IGNORECASE),
            "phone": re.compile(r'\b(?:\+91[\s\-]?)?[6-9]\d{9}\b'),
            "email": re.compile(r'\b[\w\.\-]+@[\w\.\-]+\.\w+\b'),
            "pincode": re.compile(r'\b\d{6}\b'),
            "dl_number": re.compile(r'\b[A-Z]{2}\d{2}\s?\d{4,}\b'),
            "invoice_number": re.compile(r'\b(?:INV|BILL|REC)[/\-]?\d+\b', re.IGNORECASE),
            "gst_number": re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b')
        }

    def extract(self, input_data: ExtractionInput) -> ExtractionResult:
        extracted_fields = []
        
        # Sort regions vertically then horizontally
        sorted_regions = sorted(input_data.regions, key=lambda r: (r.y1, r.x1))
        
        for field_def in input_data.extraction_schema.fields:
            matched_region = None
            raw_val = ""
            conf = 0.0
            
            # Simple heuristic matching
            # First try specific regex based on name or type if available
            pattern = None
            if field_def.name in self.patterns:
                pattern = self.patterns[field_def.name]
            elif field_def.data_type == "DATE":
                pattern = self.patterns["date"]
            elif field_def.data_type == "CURRENCY":
                pattern = self.patterns["currency"]
            elif field_def.name == "gst_number":
                pattern = self.patterns["gst_number"]
            
            if pattern:
                for region in sorted_regions:
                    match = pattern.search(region.text)
                    if match:
                        raw_val = match.group(0)
                        if len(match.groups()) > 0:
                            raw_val = match.group(1) # Extract capture group if available
                        matched_region = region
                        conf = 0.8
                        break
            
            # If no pattern matched, try keyword proximity for STRING or specific labels
            if not raw_val and field_def.aliases:
                for idx, region in enumerate(sorted_regions):
                    lower_text = region.text.lower()
                    for alias in field_def.aliases:
                        if alias.lower() in lower_text:
                            # Usually the value is next region or after colon
                            if ":" in region.text:
                                parts = region.text.split(":", 1)
                                if parts[1].strip():
                                    raw_val = parts[1].strip()
                                    matched_region = region
                                    conf = 0.7
                                    break
                            
                            # Check next region if on same line (y diff small)
                            if not raw_val and idx + 1 < len(sorted_regions):
                                next_region = sorted_regions[idx+1]
                                if abs(next_region.y1 - region.y1) < 0.05: # same line heuristic
                                    raw_val = next_region.text
                                    matched_region = next_region
                                    conf = 0.6
                                    break
                    if raw_val:
                        break

            if raw_val:
                raw, norm = ExtractionNormalizer.normalize(raw_val, field_def.data_type)
                if norm or raw:
                    evidence = []
                    if matched_region:
                        evidence.append(FieldEvidenceData(
                            page_id=matched_region.ocr_result.page_id if getattr(matched_region, "ocr_result", None) else None,
                            ocr_region_id=matched_region.id,
                            rule_id=f"rules_v1_{field_def.name}",
                            confidence=conf
                        ))
                    
                    extracted_fields.append(ExtractedFieldData(
                        name=field_def.name,
                        raw_value=raw,
                        normalized_value=norm,
                        data_type=field_def.data_type,
                        confidence=conf,
                        evidence=evidence
                    ))

        return ExtractionResult(
            extractor_name="rules",
            extractor_version="1.0",
            schema_name=input_data.extraction_schema.schema_name,
            schema_version=input_data.extraction_schema.schema_version,
            fields=extracted_fields
        )
