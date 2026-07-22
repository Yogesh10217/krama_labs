import copy
from typing import List

from app.ocr.base import OCREngine, OCRInput, OCRResult, OCRRegionResult


class FakeOCREngine(OCREngine):
    """Fake OCR engine for testing."""

    def __init__(self, should_fail: bool = False, version: str = "fake-1.0"):
        self.should_fail = should_fail
        self._version = version
        self.call_count = 0

    @property
    def name(self) -> str:
        return "fake"

    @property
    def version(self) -> str:
        return self._version

    def recognize(self, input_data: OCRInput) -> OCRResult:
        self.call_count += 1
        
        if self.should_fail:
            from app.core.exceptions import KramaException
            # Or some specific OCR_PROVIDER_UNAVAILABLE error as expected
            class OCRError(KramaException):
                status_code = 503
                code = "OCR_PROVIDER_UNAVAILABLE"
                message = "The OCR provider is currently unavailable."
            raise OCRError()

        # Generate fake deterministic output based on input
        # Coordinates must be normalized [0.0, 1.0]
        regions = [
            OCRRegionResult(
                text="Fake Word 1",
                confidence=0.99,
                bbox=(0.1, 0.1, 0.5, 0.15),
                polygon=[[0.1, 0.1], [0.5, 0.1], [0.5, 0.15], [0.1, 0.15]]
            ),
            OCRRegionResult(
                text="Low Confidence Word",
                confidence=0.15,
                bbox=(0.1, 0.4, 0.5, 0.45),
                polygon=[[0.1, 0.4], [0.5, 0.4], [0.5, 0.45], [0.1, 0.45]]
            )
        ]

        return OCRResult(
            engine="fake",
            engine_version=self._version,
            language="en",
            regions=regions,
            processing_time_ms=100
        )
