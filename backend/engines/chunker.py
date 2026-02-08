"""Chunk extractor - extracts semantic chunks from OCR regions."""

import re
from typing import List

from models import BoundingBox, DocumentChunk, OCRRegion


class ChunkExtractor:
    """Extract semantic chunks from OCR regions."""

    def __init__(self):
        self.chunk_counter = 0

    def _generate_chunk_id(self) -> str:
        self.chunk_counter += 1
        return f"chunk_{self.chunk_counter:04d}"

    def _detect_chunk_type(self, text: str, bbox: BoundingBox, all_regions: List[OCRRegion]) -> str:
        text_lower = text.lower().strip()
        if len(text) < 100 and (
            text.isupper()
            or text.endswith(":")
            or any(text_lower.startswith(h) for h in ["chapter", "section", "part"])
        ):
            return "heading"
        if re.match(r"^[\d\u2022\-\*\[\]]+[.\)]\s", text):
            return "list_item"
        if len(re.findall(r"\$?[\d,]+\.?\d*", text)) >= 3:
            return "table_row"
        return "text"

    def _merge_nearby_regions(self, regions: List[OCRRegion], y_threshold: float = 15) -> List[List[OCRRegion]]:
        if not regions:
            return []
        sorted_regions = sorted(regions, key=lambda r: (r.bbox.y1, r.bbox.x1))
        lines = []
        current_line = [sorted_regions[0]]
        for region in sorted_regions[1:]:
            if abs(region.bbox.y1 - current_line[-1].bbox.y1) < y_threshold:
                current_line.append(region)
            else:
                lines.append(current_line)
                current_line = [region]
        if current_line:
            lines.append(current_line)
        return lines

    def extract_chunks(self, ocr_regions: List[OCRRegion], page_num: int = 0) -> List[DocumentChunk]:
        chunks = []
        lines = self._merge_nearby_regions(ocr_regions)
        for line_regions in lines:
            line_regions = sorted(line_regions, key=lambda r: r.bbox.x1)
            merged_text = " ".join(r.text for r in line_regions)
            x1 = min(r.bbox.x1 for r in line_regions)
            y1 = min(r.bbox.y1 for r in line_regions)
            x2 = max(r.bbox.x2 for r in line_regions)
            y2 = max(r.bbox.y2 for r in line_regions)
            merged_bbox = BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2, page=page_num)
            avg_conf = sum(r.confidence for r in line_regions) / len(line_regions)
            chunk_type = self._detect_chunk_type(merged_text, merged_bbox, ocr_regions)
            chunks.append(
                DocumentChunk(
                    chunk_id=self._generate_chunk_id(),
                    text=merged_text,
                    chunk_type=chunk_type,
                    bbox=merged_bbox,
                    page_num=page_num,
                    confidence=avg_conf,
                    metadata={"source_regions": len(line_regions)},
                )
            )
        return chunks
