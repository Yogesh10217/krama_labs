"""OCR result normalization.

Responsibilities:
- Validate and clamp coordinate values
- Normalize confidence to 0.0-1.0
- Derive axis-aligned bounding boxes from polygons
- Sanitize text (strip control chars, normalize unicode)
- Reject fundamentally invalid geometry
"""
import math
import unicodedata
from typing import List, Tuple
from app.ocr.base import OCRRegionResult


def normalize_confidence(value: float) -> float:
    """Clamp confidence to [0.0, 1.0]."""
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def normalize_coordinate(value: float) -> float:
    """Clamp a single coordinate to [0.0, 1.0]. Reject NaN/Inf."""
    if not math.isfinite(value):
        raise ValueError(f"Non-finite coordinate value: {value}")
    return max(0.0, min(1.0, float(value)))


def normalize_bbox(
    x1: float, y1: float, x2: float, y2: float
) -> Tuple[float, float, float, float]:
    """Normalize and validate a bounding box.
    
    Ensures x1 <= x2, y1 <= y2 and all values are in [0.0, 1.0].
    """
    x1 = normalize_coordinate(x1)
    y1 = normalize_coordinate(y1)
    x2 = normalize_coordinate(x2)
    y2 = normalize_coordinate(y2)
    # Ensure ordering
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    return (x1, y1, x2, y2)


def pixel_bbox_to_normalized(
    x1: float, y1: float, x2: float, y2: float,
    page_width: int, page_height: int
) -> Tuple[float, float, float, float]:
    """Convert pixel coordinates to normalized [0.0, 1.0] coordinates."""
    if page_width <= 0 or page_height <= 0:
        raise ValueError(f"Invalid page dimensions: {page_width}x{page_height}")
    return normalize_bbox(
        x1 / page_width, y1 / page_height,
        x2 / page_width, y2 / page_height,
    )


def pixel_polygon_to_normalized(
    polygon: List[List[float]], page_width: int, page_height: int
) -> List[List[float]]:
    """Convert a pixel polygon to normalized coordinates."""
    if page_width <= 0 or page_height <= 0:
        raise ValueError(f"Invalid page dimensions: {page_width}x{page_height}")
    result = []
    for point in polygon:
        nx = normalize_coordinate(point[0] / page_width)
        ny = normalize_coordinate(point[1] / page_height)
        result.append([nx, ny])
    return result


def derive_bbox_from_polygon(
    polygon: List[List[float]]
) -> Tuple[float, float, float, float]:
    """Derive axis-aligned bounding box from normalized polygon points."""
    if not polygon or len(polygon) < 3:
        raise ValueError("Polygon must have at least 3 points")
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return normalize_bbox(min(xs), min(ys), max(xs), max(ys))


def sanitize_text(text: str) -> str:
    """Conservative text sanitization.
    
    - NFC unicode normalization
    - Strip C0/C1 control chars except tab and newline
    - Consistent newline handling
    Does NOT: correct spelling, translate, guess missing words.
    """
    if not text:
        return ""
    # NFC normalize
    text = unicodedata.normalize("NFC", text)
    # Remove control chars except \t and \n
    cleaned = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith("C") and ch not in ("\t", "\n"):
            continue
        cleaned.append(ch)
    return "".join(cleaned).strip()


def normalize_regions(
    regions: List[OCRRegionResult]
) -> List[OCRRegionResult]:
    """Apply all normalization to a list of OCR regions in-place.
    
    Returns the normalized list (same objects, mutated).
    """
    valid = []
    for r in regions:
        r.confidence = normalize_confidence(r.confidence)
        r.text = sanitize_text(r.text)
        try:
            r.bbox = normalize_bbox(*r.bbox)
        except (ValueError, TypeError):
            continue  # Skip regions with fundamentally invalid geometry
        if r.polygon:
            try:
                r.polygon = [
                    [normalize_coordinate(p[0]), normalize_coordinate(p[1])]
                    for p in r.polygon
                ]
            except (ValueError, TypeError, IndexError):
                r.polygon = None  # Preserve the region but discard invalid polygon
        valid.append(r)
    return valid
