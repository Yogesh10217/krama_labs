"""Deterministic layout analysis and reading order.

Assigns reading order to OCR regions based on spatial position.
Constructs full_text from ordered regions.

Algorithm:
1. Sort regions into horizontal bands (rows) using y-center.
2. Within each band, sort left-to-right by x-center.
3. Assign sequential reading_order.
4. Concatenate texts with appropriate whitespace.

Handles simple single-column and basic two-column layouts.
Does NOT implement: semantic document understanding, VLM-based layout,
advanced table reconstruction, or AI-driven analysis.
"""
from typing import List, Tuple
from app.ocr.base import OCRRegionResult


def assign_reading_order(
    regions: List[OCRRegionResult],
    band_tolerance: float = 0.015,
) -> List[Tuple[int, OCRRegionResult]]:
    """Assign deterministic reading order to OCR regions.
    
    Args:
        regions: List of OCRRegionResult with normalized coordinates.
        band_tolerance: Maximum y-center difference to consider regions on the same line.
            Expressed as fraction of page height (0.0-1.0). Default ~1.5% of page.
    
    Returns:
        List of (reading_order, region) tuples, sorted by reading order.
    """
    if not regions:
        return []
    
    # Calculate y-center for each region
    def y_center(r: OCRRegionResult) -> float:
        return (r.bbox[1] + r.bbox[3]) / 2.0
    
    def x_center(r: OCRRegionResult) -> float:
        return (r.bbox[0] + r.bbox[2]) / 2.0
    
    # Sort by y_center first
    sorted_regions = sorted(regions, key=y_center)
    
    # Group into bands
    bands: List[List[OCRRegionResult]] = []
    current_band: List[OCRRegionResult] = [sorted_regions[0]]
    current_y = y_center(sorted_regions[0])
    
    for region in sorted_regions[1:]:
        ry = y_center(region)
        if abs(ry - current_y) <= band_tolerance:
            current_band.append(region)
        else:
            bands.append(current_band)
            current_band = [region]
            current_y = ry
    bands.append(current_band)
    
    # Within each band, sort left-to-right
    ordered: List[Tuple[int, OCRRegionResult]] = []
    reading_order = 0
    for band in bands:
        band_sorted = sorted(band, key=x_center)
        for region in band_sorted:
            ordered.append((reading_order, region))
            reading_order += 1
    
    return ordered


def build_full_text(ordered_regions: List[Tuple[int, OCRRegionResult]]) -> str:
    """Construct page full text from reading-ordered regions.
    
    Regions on the same line (consecutive reading orders in same band)
    are separated by spaces. Different lines are separated by newlines.
    """
    if not ordered_regions:
        return ""
    
    parts = []
    prev_y_center = None
    band_tolerance = 0.015
    
    for _, region in ordered_regions:
        current_y = (region.bbox[1] + region.bbox[3]) / 2.0
        
        if prev_y_center is not None:
            if abs(current_y - prev_y_center) > band_tolerance:
                parts.append("\n")
            else:
                parts.append(" ")
        
        parts.append(region.text)
        prev_y_center = current_y
    
    return "".join(parts).strip()
