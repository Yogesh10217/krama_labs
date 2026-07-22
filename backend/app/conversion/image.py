import io
from typing import Generator
from PIL import Image, ImageOps
from app.conversion.base import DocumentConverter, ConvertedPage
from app.core.config import Config
from app.core.exceptions import (
    CorruptedDocument,
    DocumentPageLimitExceeded,
    PageDimensionLimitExceeded,
    PagePixelLimitExceeded,
)


class ImageConverter(DocumentConverter):
    """Converts images (PNG, JPEG, TIFF) into canonical PNG format.

    Tiff formats can contain multiple frames/pages, which are rendered
    sequentially. JPEG & PNG yield exactly one page.
    """

    def supports(self, extension: str) -> bool:
        return extension.lower() in ("png", "jpg", "jpeg", "tif", "tiff")

    def convert(self, source_path: str) -> Generator[ConvertedPage, None, None]:
        try:
            img = Image.open(source_path)
        except Exception as e:
            raise CorruptedDocument(f"Failed to open image file. It may be corrupted: {e}")

        try:
            # Determine total frames/pages (Pillow uses n_frames for multi-frame TIFFs)
            total_pages = 1
            is_animated = getattr(img, "is_animated", False)
            if is_animated:
                total_pages = getattr(img, "n_frames", 1)

            max_pages = Config.MAX_DOCUMENT_PAGES
            if total_pages > max_pages:
                raise DocumentPageLimitExceeded(
                    f"Image contains {total_pages} frames, which exceeds maximum limit of {max_pages}."
                )

            for i in range(total_pages):
                if is_animated:
                    try:
                        img.seek(i)
                    except EOFError:
                        break

                # Safe copy of the frame to avoid modifying the original iterator
                frame = img.copy()

                # Process the frame
                width, height = frame.size
                if width > Config.MAX_PAGE_WIDTH or height > Config.MAX_PAGE_HEIGHT:
                    raise PageDimensionLimitExceeded(
                        f"Page {i + 1} dimensions ({width}x{height}) exceed maximum limits ({Config.MAX_PAGE_WIDTH}x{Config.MAX_PAGE_HEIGHT})."
                    )

                pixels = width * height
                if pixels > Config.MAX_PAGE_PIXELS:
                    raise PagePixelLimitExceeded(
                        f"Page {i + 1} total pixel count ({pixels}) exceeds the safety limit of {Config.MAX_PAGE_PIXELS} pixels."
                    )

                # Normalize orientation for JPEG/TIFF using ImageOps.exif_transpose
                try:
                    frame = ImageOps.exif_transpose(frame)
                except Exception:
                    pass  # Best effort

                # Save as PNG
                png_io = io.BytesIO()
                frame.save(png_io, format="PNG")
                png_io.seek(0)

                yield ConvertedPage(
                    page_number=i + 1,
                    width=frame.width,
                    height=frame.height,
                    content_type="image/png",
                    stream=png_io,
                )
        except Exception as e:
            if not isinstance(e, (PageDimensionLimitExceeded, PagePixelLimitExceeded, DocumentPageLimitExceeded)):
                raise CorruptedDocument(f"Failed to process image frame: {e}")
            raise
        finally:
            img.close()
