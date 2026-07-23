import abc
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ClassificationInput:
    """Canonical domain input for document classification."""
    document_id: str
    original_filename: str
    ocr_text: str  # Full concatenated OCR text in reading order
    pages_text: Dict[int, str]  # Page number to text
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ClassificationResult:
    """Canonical classification result."""
    document_type: str
    confidence: float
    classifier_name: str
    classifier_version: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)


class DocumentClassifier(abc.ABC):
    """Abstract interface for all document classifiers."""
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the classifier (e.g., 'rules')."""
        pass

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Version of the classifier (e.g., '1.0')."""
        pass

    @abc.abstractmethod
    def classify(self, input_data: ClassificationInput) -> ClassificationResult:
        """
        Produce a classification result from canonical input.
        Must not raise expected domain errors for unknown types; should return 'unknown' with low confidence.
        """
        pass
