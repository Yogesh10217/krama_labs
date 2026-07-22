import io
from typing import Generator
from app.conversion.base import DocumentConverter, ConvertedPage
from app.core.config import Config
from app.core.exceptions import (
    CorruptedDocument,
    EncryptedDocument,
    DocumentPageLimitExceeded,
    PageDimensionLimitExceeded,
    PagePixelLimitExceeded,
)


class PDFConverter(DocumentConverter):
    """Incremental PDF converter using PyMuPDF (fitz)."""

    def supports(self, extension: str) -> bool:
        return extension.lower() in ("pdf",)

    def convert(self, source_path: str) -> Generator[ConvertedPage, None, None]:
        try:
            import fitz
        except ImportError:
            raise ImportError("pymupdf is required for PDF conversion. Install it using pip.")

        try:
            doc = fitz.open(source_path)
        except Exception as e:
            raise CorruptedDocument(f"Failed to open PDF document. It may be corrupted: {e}")

        try:
            if doc.is_encrypted:
                raise EncryptedDocument("The PDF document is password-protected or encrypted.")

            page_count = doc.page_count
            max_pages = Config.MAX_DOCUMENT_PAGES
            if page_count > max_pages:
                raise DocumentPageLimitExceeded(
                    f"PDF document page count ({page_count}) exceeds the maximum allowed limit of {max_pages} pages."
                )

            dpi = Config.PDF_RENDER_DPI
            # fitz default resolution is 72 dpi. Zoom is the scaling factor.
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            for i in range(page_count):
                page = doc.load_page(i)
                rect = page.rect
                width = int(rect.width * zoom)
                height = int(rect.height * zoom)

                if width > Config.MAX_PAGE_WIDTH or height > Config.MAX_PAGE_HEIGHT:
                    raise PageDimensionLimitExceeded(
                        f"Page {i + 1} dimensions ({width}x{height}) exceed maximum limits ({Config.MAX_PAGE_WIDTH}x{Config.MAX_PAGE_HEIGHT})."
                    )

                pixels = width * height
                if pixels > Config.MAX_PAGE_PIXELS:
                    raise PagePixelLimitExceeded(
                        f"Page {i + 1} total pixel count ({pixels}) exceeds the safety limit of {Config.MAX_PAGE_PIXELS} pixels."
                    )

                try:
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    png_bytes = pix.tobytes("png")
                except Exception as e:
                    raise CorruptedDocument(f"Failed to render page {i + 1}: {e}")

                stream = io.BytesIO(png_bytes)

                yield ConvertedPage(
                    page_number=i + 1,
                    width=width,
                    height=height,
                    content_type="image/png",
                    stream=stream,
                )
        finally:
            doc.close()
