from typing import List, Optional
from app.conversion.base import DocumentConverter
from app.conversion.pdf import PDFConverter
from app.conversion.image import ImageConverter


class ConversionRegistry:
    """Registry mapping file extensions to their corresponding DocumentConverter."""

    def __init__(self) -> None:
        self._converters: List[DocumentConverter] = [
            PDFConverter(),
            ImageConverter(),
        ]

    def get_converter_for_extension(self, extension: str) -> Optional[DocumentConverter]:
        """Find the registered converter that supports the given file extension (with or without dot)."""
        clean_ext = extension.lower().lstrip(".")
        for converter in self._converters:
            if converter.supports(clean_ext):
                return converter
        return None


# Global singleton instance for app-wide use
registry = ConversionRegistry()
