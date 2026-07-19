"""Triple validation engine - OCR + VLM + Structure weighted validation."""

from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from app.core.config import Config
from app.models import (
    BoundingBox,
    ConfidenceLevel,
    GroundedValue,
    ValidationResult,
    ValidationStatus,
)


class TripleValidator:
    """Triple validation: OCR + VLM + Structure."""

    def __init__(self):
        self.weights = {"ocr": 0.35, "vlm": 0.40, "structure": 0.25}

    def _get_confidence_level(self, conf: float) -> ConfidenceLevel:
        if conf >= Config.HIGH_CONFIDENCE:
            return ConfidenceLevel.HIGH
        elif conf >= Config.MEDIUM_CONFIDENCE:
            return ConfidenceLevel.MEDIUM
        elif conf >= Config.LOW_CONFIDENCE:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.FLAGGED

    def _normalize_value(self, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip().lower().replace(",", "").replace(" ", "")

    def validate_field(
        self,
        field_name: str,
        ocr_value: str,
        ocr_confidence: float,
        ocr_bbox: Optional[BoundingBox],
        vlm_value: str,
        vlm_confidence: float,
        struct_value: str,
        struct_confidence: float,
        grounding: Optional[GroundedValue] = None,
    ) -> ValidationResult:
        values = []
        if ocr_value and self._normalize_value(ocr_value):
            values.append((ocr_value, ocr_confidence, "ocr"))
        if vlm_value and self._normalize_value(vlm_value):
            values.append((vlm_value, vlm_confidence, "vlm"))
        if struct_value and self._normalize_value(struct_value):
            values.append((struct_value, struct_confidence, "structure"))

        if not values:
            return ValidationResult(
                field_name=field_name,
                is_flagged=True,
                flag_reasons=["No valid values from any source"],
            )

        groups: Dict[str, List[Tuple[str, float, str]]] = defaultdict(list)
        for val, conf, source in values:
            norm = self._normalize_value(val)
            groups[norm].append((val, conf, source))

        best_group = max(groups.values(), key=lambda g: (len(g), max(c for _, c, _ in g)))
        agreement_ratio = len(best_group) / len(values)

        final_val, final_conf, _ = max(best_group, key=lambda x: x[1])

        if agreement_ratio == 1.0 and len(values) >= 2:
            status = ValidationStatus.VERIFIED
            final_conf = min(final_conf * 1.1, 1.0)
        elif agreement_ratio >= 0.5:
            status = ValidationStatus.PARTIAL
        elif len(values) == 1:
            status = ValidationStatus.UNVERIFIED
        else:
            status = ValidationStatus.CONFLICT
            final_conf *= 0.8

        if grounding and grounding.match_score >= 90:
            final_conf = min(final_conf + 0.1, 1.0)

        flags = []
        if status == ValidationStatus.CONFLICT:
            flags.append("Value mismatch between sources")
        if final_conf < Config.FLAG_THRESHOLD:
            flags.append(f"Low confidence: {final_conf:.2f}")
        if not grounding:
            flags.append("Not grounded to source")

        return ValidationResult(
            field_name=field_name,
            ocr_value=ocr_value or "",
            ocr_confidence=ocr_confidence,
            ocr_bbox=ocr_bbox,
            vlm_value=vlm_value or "",
            vlm_confidence=vlm_confidence,
            structure_value=struct_value or "",
            structure_confidence=struct_confidence,
            final_value=final_val,
            final_confidence=final_conf,
            confidence_level=self._get_confidence_level(final_conf),
            validation_status=status,
            is_grounded=grounding is not None,
            grounding_proof=grounding,
            is_flagged=len(flags) > 0,
            flag_reasons=flags,
        )
