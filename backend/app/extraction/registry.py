from typing import Dict
from app.extraction.base import StructuredExtractor
from app.extraction.rules import RulesExtractor
from app.core.exceptions import KramaException

class ExtractorUnavailableException(KramaException):
    def __init__(self, provider: str):
        super().__init__(
            status_code=500,
            code="EXTRACTION_PROVIDER_UNAVAILABLE",
            message=f"Extraction provider {provider} is not available or registered."
        )

_EXTRACTORS: Dict[str, StructuredExtractor] = {
    "rules": RulesExtractor()
}

def get_extractor(provider: str) -> StructuredExtractor:
    extractor = _EXTRACTORS.get(provider)
    if not extractor:
        raise ExtractorUnavailableException(provider)
    return extractor
