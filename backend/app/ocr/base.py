"""Provider-neutral OCR engine abstraction.

Coordinate system convention:
    origin = top-left
    x increases toward right (0.0 to 1.0)
    y increases downward (0.0 to 1.0)

All coordinates are normalized relative to page dimensions.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OCRInput:
    """Provider-neutral input for OCR engines.

    OCRService materializes this from StorageProvider.
    Some providers need local paths; others accept bytes.
    """
    content: bytes
    width: int
    height: int
    content_type: str = "image/png"
    temp_path: Optional[str] = None  # Set by OCRService when provider needs file path


@dataclass
class OCRRegionResult:
    """Single recognized text region from OCR provider.

    All coordinates are normalized 0.0-1.0.
    """
    text: str
    confidence: float  # 0.0 to 1.0
    bbox: tuple  # (x1, y1, x2, y2) normalized
    polygon: Optional[List[List[float]]] = None  # [[x1,y1],[x2,y2],...] normalized
    region_type: str = "TEXT"  # TEXT, TITLE, TABLE_LIKE, UNKNOWN


@dataclass
class OCRResult:
    """Complete OCR output for a single page."""
    engine: str
    engine_version: str
    language: str
    regions: List[OCRRegionResult] = field(default_factory=list)
    processing_time_ms: float = 0.0


class OCREngine(ABC):
    """Abstract base for all OCR providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique engine identifier (e.g. 'paddle', 'tesseract')."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Engine version string."""
        ...

    @abstractmethod
    def recognize(self, ocr_input: OCRInput) -> OCRResult:
        """Perform OCR on the given input and return structured results.

        Coordinates in returned OCRRegionResult must be normalized 0.0-1.0.
        """
        ...
