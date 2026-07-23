import math
from typing import Dict, Any, List
from .base import ClassificationResult
from .taxonomy import is_valid_type

class ClassificationNormalizer:
    """Normalizes and validates raw classification results."""
    
    @staticmethod
    def normalize(result: ClassificationResult, fallback_type: str = "unknown") -> ClassificationResult:
        """
        Validates confidence bounds (0.0 to 1.0), handles NaN/Infinity,
        and enforces canonical taxonomy.
        """
        # Validate confidence
        try:
            confidence = float(result.confidence)
            if math.isnan(confidence) or math.isinf(confidence):
                confidence = 0.0
        except (ValueError, TypeError):
            confidence = 0.0
            
        # Bound confidence
        confidence = max(0.0, min(1.0, confidence))
        
        # Validate taxonomy
        doc_type = result.document_type
        if not is_valid_type(doc_type):
            # If invalid, safe fallback
            doc_type = fallback_type
            # Penalize confidence if we had to fallback
            confidence = 0.0
            
        # Validate evidence
        evidence = result.evidence
        if not isinstance(evidence, list):
            evidence = []
            
        # Ensure JSON safety for evidence (basic check)
        clean_evidence = []
        for item in evidence:
            if isinstance(item, dict):
                # We could deeply sanitize here, but for now just ensure it's a dict
                clean_evidence.append(item)
                
        return ClassificationResult(
            document_type=doc_type,
            confidence=round(confidence, 4),
            classifier_name=result.classifier_name,
            classifier_version=result.classifier_version,
            evidence=clean_evidence
        )
