import abc
import hashlib
from typing import Generator, IO, Optional


class ConvertedPage:
    """Represents a single materialized page yielded by a converter.

    Attributes:
        page_number: 1-based page number.
        width: Image width in pixels.
        height: Image height in pixels.
        content_type: MIME type (always image/png for canonical format).
        stream: File-like object containing raw PNG bytes. Caller is responsible for closing.
    """

    def __init__(
        self,
        page_number: int,
        width: int,
        height: int,
        content_type: str,
        stream: IO[bytes],
    ) -> None:
        self.page_number = page_number
        self.width = width
        self.height = height
        self.content_type = content_type
        self.stream = stream

    def read_metadata_and_hashes(self) -> tuple[int, str]:
        """Compute the size and SHA-256 checksum of the stream, resetting its pointer.

        Returns:
            (size_bytes, sha256_hex)
        """
        self.stream.seek(0, 2)
        size_bytes = self.stream.tell()
        self.stream.seek(0)

        hasher = hashlib.sha256()
        # Read in 64kb chunks
        while True:
            chunk = self.stream.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
        self.stream.seek(0)

        return size_bytes, hasher.hexdigest()


class DocumentConverter(abc.ABC):
    """Abstract base class for all format-specific page materializers."""

    @abc.abstractmethod
    def supports(self, extension: str) -> bool:
        """Return True if this converter supports the given extension (without leading dot)."""
        pass

    @abc.abstractmethod
    def convert(self, source_path: str) -> Generator[ConvertedPage, None, None]:
        """Yield ConvertedPage objects one by one to keep memory usage minimal.

        Args:
            source_path: Local absolute path to the raw input file.

        Yields:
            ConvertedPage: A single materialized page.
        """
        pass
