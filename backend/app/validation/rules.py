import re
from typing import List, Optional, Tuple, Dict
import uuid

from app.core.config import Config
from app.validation.base import Validator, ValidationInput, ValidationResult, FieldValidationResult, ValidationEvidenceModel
from app.domain.enums import ValidationStatus
from app.db.models.ocr import OCRRegion
from app.db.models.extraction import ExtractedField

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

class ValidationPolicies:
    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        text = str(text).strip().lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[$€£¥₹]", "", text)
        text = re.sub(r"[,\-/\\():]", "", text)
        return text.strip()

    @staticmethod
    def exact_match(extracted: str, ocr_text: str) -> bool:
        return ValidationPolicies.normalize(extracted) == ValidationPolicies.normalize(ocr_text)

    @staticmethod
    def contained_match(extracted: str, ocr_text: str) -> bool:
        norm_ext = ValidationPolicies.normalize(extracted)
        norm_ocr = ValidationPolicies.normalize(ocr_text)
        return norm_ext in norm_ocr if norm_ext and norm_ocr else False

    @staticmethod
    def fuzzy_match(extracted: str, ocr_text: str, threshold: float) -> Tuple[bool, float]:
        if fuzz is None:
            return False, 0.0
        
        norm_ext = ValidationPolicies.normalize(extracted)
        norm_ocr = ValidationPolicies.normalize(ocr_text)
        
        if not norm_ext or not norm_ocr:
            return False, 0.0

        fuzzy_ratio = max(
            fuzz.ratio(norm_ext, norm_ocr),
            fuzz.partial_ratio(norm_ext, norm_ocr),
            fuzz.token_sort_ratio(norm_ext, norm_ocr)
        )
        return fuzzy_ratio >= threshold, fuzzy_ratio

class RuleValidator(Validator):
    def __init__(self):
        self.threshold = Config.VALIDATION_FUZZY_THRESHOLD

    def _evaluate_region(self, field: ExtractedField, region: OCRRegion) -> Tuple[ValidationStatus, float, str, str]:
        """Evaluates a single region against an extracted field."""
        if not field.raw_value or not region.text:
            return ValidationStatus.UNSUPPORTED, 0.0, "Missing value or OCR text", "none"

        # 1. Exact Match
        if ValidationPolicies.exact_match(field.raw_value, region.text):
            return ValidationStatus.SUPPORTED, 1.0, "Exact OCR match", "exact_match"
        
        # 2. Contained Match
        if ValidationPolicies.contained_match(field.raw_value, region.text):
            return ValidationStatus.SUPPORTED, 0.95, "Contained in OCR text", "contained_match"
            
        # 3. Fuzzy Match
        is_fuzzy, score = ValidationPolicies.fuzzy_match(field.raw_value, region.text, self.threshold)
        if is_fuzzy:
            normalized_score = score / 100.0
            return ValidationStatus.PARTIALLY_SUPPORTED, normalized_score, f"Fuzzy OCR match (score {score:.1f})", "fuzzy_match"
            
        return ValidationStatus.UNSUPPORTED, 0.0, "OCR text does not match", "unsupported"

    def validate(self, input_data: ValidationInput) -> ValidationResult:
        results = []
        
        # Build lookups for regions
        region_map = {r.id: r for r in input_data.regions}
        page_regions: Dict[uuid.UUID, List[OCRRegion]] = {}
        page_map = {p.id: p.page_id for p in input_data.pages}
        
        for r in input_data.regions:
            real_page_id = page_map.get(r.ocr_result_id)
            if real_page_id:
                page_regions.setdefault(real_page_id, []).append(r)

        for field in input_data.extracted_fields:
            if not field.raw_value:
                results.append(FieldValidationResult(
                    extracted_field_id=field.id,
                    validation_status=ValidationStatus.MISSING_EVIDENCE,
                    validation_score=0.0,
                    validation_reason="No extracted value to validate",
                    evidence=[]
                ))
                continue

            best_status = ValidationStatus.MISSING_EVIDENCE
            best_score = 0.0
            best_reason = "No evidence found"
            best_evidence = None

            # Track pages where evidence was found for Tier 2 fallback
            linked_pages = set()
            
            # --- TIER 1: Validate against Phase 6 FieldEvidence ---
            for ev in field.evidence:
                linked_pages.add(ev.page_id)
                region = region_map.get(ev.ocr_region_id)
                if not region:
                    continue
                
                status, score, reason, support_type = self._evaluate_region(field, region)
                
                if status == ValidationStatus.SUPPORTED or score > best_score:
                    best_status = status
                    best_score = score
                    best_reason = reason
                    best_evidence = ValidationEvidenceModel(
                        page_id=ev.page_id,
                        ocr_region_id=ev.ocr_region_id,
                        support_type=support_type,
                        confidence=score
                    )
                    
                    if best_status == ValidationStatus.SUPPORTED:
                        break # Stop looking in Tier 1 if we found full support
            
            # --- TIER 2: Search all OCRRegions on the same page(s) ---
            if best_status not in (ValidationStatus.SUPPORTED, ValidationStatus.PARTIALLY_SUPPORTED) and linked_pages:
                for page_id in linked_pages:
                    for region in page_regions.get(page_id, []):
                        status, score, reason, support_type = self._evaluate_region(field, region)
                        if status == ValidationStatus.SUPPORTED or score > best_score:
                            best_status = status
                            best_score = score
                            best_reason = f"{reason} (Tier 2 Page Fallback)"
                            best_evidence = ValidationEvidenceModel(
                                page_id=page_id,
                                ocr_region_id=region.id,
                                support_type=f"{support_type}_page_fallback",
                                confidence=score
                            )
                            if best_status == ValidationStatus.SUPPORTED:
                                break
                    if best_status == ValidationStatus.SUPPORTED:
                        break
            
            # --- TIER 3: Search all OCRRegions across the document ---
            if best_status not in (ValidationStatus.SUPPORTED, ValidationStatus.PARTIALLY_SUPPORTED):
                for region in input_data.regions:
                    real_page_id = page_map.get(region.ocr_result_id)
                    # Skip regions we already checked in Tier 2
                    if real_page_id in linked_pages:
                        continue
                        
                    status, score, reason, support_type = self._evaluate_region(field, region)
                    if status == ValidationStatus.SUPPORTED or score > best_score:
                        best_status = status
                        best_score = score
                        best_reason = f"{reason} (Tier 3 Doc Fallback)"
                        best_evidence = ValidationEvidenceModel(
                            page_id=real_page_id,
                            ocr_region_id=region.id,
                            support_type=f"{support_type}_doc_fallback",
                            confidence=score
                        )
                        if best_status == ValidationStatus.SUPPORTED:
                            break

            evidence_list = [best_evidence] if best_evidence and best_status != ValidationStatus.UNSUPPORTED else []
            if best_status == ValidationStatus.MISSING_EVIDENCE and evidence_list:
                 best_status = ValidationStatus.UNSUPPORTED # Downgrade if we found evidence but it wasn't a match

            results.append(FieldValidationResult(
                extracted_field_id=field.id,
                validation_status=best_status,
                validation_score=best_score,
                validation_reason=best_reason,
                evidence=evidence_list
            ))

        return ValidationResult(
            validator_name="rules",
            validator_version="1.0",
            fields=results
        )
