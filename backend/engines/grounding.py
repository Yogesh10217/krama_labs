"""Grounding engine - matches VLM-extracted values to OCR source regions."""

import re
from typing import List, Optional

from rapidfuzz import fuzz

from models import BoundingBox, OCRRegion, GroundedValue


class GroundingEngine:
    """Grounds extracted values back to OCR text regions using 5 matching strategies."""

    def __init__(self, threshold: int = 75):
        self.threshold = threshold

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
    def normalize_number(text: str) -> str:
        if not text:
            return ""
        numbers = re.findall(r"[\d]+\.?[\d]*", str(text))
        return "".join(numbers)

    @staticmethod
    def get_tokens(text: str) -> set:
        if not text:
            return set()
        tokens = re.split(r"[\s,.\-/\\]+", text.lower())
        return {t for t in tokens if len(t) > 1}

    def find_match(self, value: str, ocr_regions: List[OCRRegion]) -> Optional[GroundedValue]:
        if not value or not ocr_regions:
            return None

        value_str = str(value).strip()
        norm_value = self.normalize(value_str)
        num_value = self.normalize_number(value_str)
        value_tokens = self.get_tokens(value_str)

        best_match = None
        best_score = 0.0

        for region in ocr_regions:
            norm_ocr = self.normalize(region.text)
            if not norm_ocr:
                continue

            score = 0.0
            method = "none"

            # Strategy 1: Exact match
            if norm_value == norm_ocr:
                return GroundedValue(
                    field_name="", value=value_str, source_text=region.text,
                    bbox=region.bbox, confidence=region.confidence,
                    match_score=100.0, extraction_method="exact",
                )

            # Strategy 2: Number matching
            if num_value and len(num_value) >= 2:
                num_ocr = self.normalize_number(region.text)
                if num_value == num_ocr:
                    score = 98.0
                    method = "number_exact"
                elif num_value in num_ocr or num_ocr in num_value:
                    score = max(score, 92.0)
                    method = "number_partial"

            # Strategy 3: Contained
            if norm_value in norm_ocr:
                new_score = 95.0 * (len(norm_value) / len(norm_ocr))
                if new_score > score:
                    score = new_score
                    method = "contained"

            # Strategy 4: Token overlap
            if value_tokens and len(value_tokens) >= 2:
                ocr_tokens = self.get_tokens(region.text)
                if ocr_tokens:
                    overlap = len(value_tokens & ocr_tokens)
                    if overlap > 0:
                        token_score = 85.0 * (overlap / max(len(value_tokens), len(ocr_tokens)))
                        if token_score > score:
                            score = token_score
                            method = "token"

            # Strategy 5: Fuzzy
            fuzzy_ratio = max(
                fuzz.ratio(norm_value, norm_ocr),
                fuzz.partial_ratio(norm_value, norm_ocr),
                fuzz.token_sort_ratio(norm_value, norm_ocr),
            )
            if fuzzy_ratio > score and fuzzy_ratio >= self.threshold:
                score = float(fuzzy_ratio)
                method = "fuzzy"

            if score > best_score and score >= self.threshold:
                best_score = score
                best_match = GroundedValue(
                    field_name="", value=value_str, source_text=region.text,
                    bbox=region.bbox, confidence=region.confidence * (score / 100),
                    match_score=score, extraction_method=method,
                )

        return best_match

    def ground_all(self, data, ocr_regions: List[OCRRegion]):
        grounded = {}

        def process(prefix: str, value):
            if value is None:
                return
            if isinstance(value, (str, int, float)):
                match = self.find_match(str(value), ocr_regions)
                if match:
                    match.field_name = prefix
                    grounded[prefix] = match
            elif isinstance(value, dict):
                for k, v in value.items():
                    process(f"{prefix}.{k}" if prefix else k, v)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    process(f"{prefix}[{i}]", item)

        process("", data)
        return grounded
