from typing import Dict, Any, List
from .base import DocumentClassifier, ClassificationInput, ClassificationResult
from .taxonomy import DOCUMENT_TAXONOMY

class RulesClassifier(DocumentClassifier):
    """
    Deterministic rule-based document classifier using keyword matching.
    """
    
    @property
    def name(self) -> str:
        return "rules"

    @property
    def version(self) -> str:
        return "1.0"

    def classify(self, input_data: ClassificationInput) -> ClassificationResult:
        text_lower = input_data.ocr_text.lower()
        if not text_lower.strip():
            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                classifier_name=self.name,
                classifier_version=self.version,
                evidence=[{"reason": "Empty OCR text"}]
            )

        scores: Dict[str, int] = {}
        evidence_acc: Dict[str, List[str]] = {}

        for doc_type, info in DOCUMENT_TAXONOMY.items():
            if doc_type == "unknown":
                continue
            
            keywords = info.get("keywords", [])
            score = 0
            matched = []
            
            # Simple substring matching
            for kw in keywords:
                if kw.lower() in text_lower:
                    score += 1
                    matched.append(kw)
            
            if score > 0:
                scores[doc_type] = score
                evidence_acc[doc_type] = matched

        if not scores:
            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                classifier_name=self.name,
                classifier_version=self.version,
                evidence=[{"reason": "No keyword matches found"}]
            )

        best_type = max(scores, key=scores.get)
        max_possible = len(DOCUMENT_TAXONOMY[best_type].get("keywords", []))
        
        raw_confidence = scores[best_type] / max(max_possible, 1)
        confidence = min(raw_confidence, 1.0)
        
        evidence = [
            {
                "rule": "keyword_match",
                "matched_keywords": evidence_acc[best_type],
                "score": scores[best_type],
                "max_possible": max_possible
            }
        ]

        return ClassificationResult(
            document_type=best_type,
            confidence=confidence,
            classifier_name=self.name,
            classifier_version=self.version,
            evidence=evidence
        )
