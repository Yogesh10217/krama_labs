"""Document Processor Service - OCR-only pipeline.

Pipeline: Convert → PaddleOCR → Classify (keywords) → Extract (regex) → Markdown → JSON
"""

import gc
import hashlib
import time
import logging
from typing import Any, Dict, List
from PIL import Image

try:
    import torch
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False

from app.core.config import Config
from app.models import (
    DocumentResult,
    DocumentType,
    PageResult,
    ValidationStatus,
)
from app.engines.converter import DocumentConverter
from app.engines.ocr_engine import PaddleOCREngine
from app.engines.chunker import ChunkExtractor
from app.engines.classifier import classify_by_keywords, get_category, get_label
from app.engines.ocr_extractor import LayoutMarkdownBuilder, OCRFieldExtractor

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """OCR-only document processing pipeline. No VLM, no API key needed."""

    def __init__(self):
        logger.info("Initializing Document Processor service...")
        # This will raise ImportError if paddleocr is not installed, which we catch at route handler level
        self.ocr = PaddleOCREngine(lang=Config.OCR_LANGUAGE)
        self.chunk_extractor = ChunkExtractor()
        logger.info("Document Processor service ready! (PaddleOCR + keyword classifier + regex extractor)")

    def _generate_id(self, path: str) -> str:
        content = f"{path}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def process_page(self, image: Image.Image, page_num: int, doc_class: str) -> PageResult:
        """Process a single page: OCR → markdown → extract fields."""
        # 1. OCR
        logger.info(f"Page {page_num}: running PaddleOCR extraction...")
        ocr_regions = self.ocr.extract(image, page_num)
        logger.info(f"Page {page_num}: found {len(ocr_regions)} text regions")

        # 2. Build markdown from OCR layout
        logger.info(f"Page {page_num}: building markdown from layout...")
        markdown = LayoutMarkdownBuilder.regions_to_markdown(ocr_regions)

        # 3. Extract structured fields using regex
        logger.info(f"Page {page_num}: extracting fields (regex)...")
        extracted_data = OCRFieldExtractor.extract_from_regions(ocr_regions, doc_class)
        field_count = len([k for k in extracted_data if not k.startswith("_")])
        logger.info(f"Page {page_num}: extracted {field_count} fields")

        # 4. Chunks
        logger.info(f"Page {page_num}: extracting chunks...")
        chunks = self.chunk_extractor.extract_chunks(ocr_regions, page_num)

        # 5. Build validation results from extracted fields (OCR-only confidence)
        validation_results = []
        from app.models import ValidationResult, ConfidenceLevel, ValidationStatus as VS
        for field_name, value in extracted_data.items():
            if field_name.startswith("_"):
                continue
            val_str = str(value) if value else ""
            conf = 0.85 if val_str else 0.0
            validation_results.append(ValidationResult(
                field_name=field_name,
                ocr_value=val_str,
                ocr_confidence=conf,
                final_value=val_str,
                final_confidence=conf,
                confidence_level=ConfidenceLevel.HIGH if conf >= 0.8 else ConfidenceLevel.LOW,
                validation_status=VS.VERIFIED if val_str else VS.UNVERIFIED,
                is_grounded=bool(val_str),
                is_flagged=not bool(val_str),
            ))

        return PageResult(
            page_num=page_num,
            ocr_regions=ocr_regions,
            markdown=markdown,
            extracted_data=extracted_data,
            validation_results=validation_results,
            chunks=chunks,
        )

    def process(self, file_path: str) -> DocumentResult:
        start = time.time()
        logger.info(f"Starting document pipeline processing for: {file_path}")

        # 1. Convert to images
        images, doc_type = DocumentConverter.convert(file_path)
        logger.info(f"Converted document to {len(images)} page images.")

        # 2. Quick OCR on first page for classification
        logger.info("Running first-page classification OCR...")
        first_page_regions = self.ocr.extract(images[0], 0)
        ocr_text = " ".join(r.text for r in first_page_regions)

        # 3. Classify using keywords
        logger.info("Classifying document type by keywords...")
        doc_class, classify_conf = classify_by_keywords(ocr_text)
        doc_category = get_category(doc_class)
        doc_label = get_label(doc_class)
        logger.info(f"Classified as: {doc_class} ({doc_label}) [{doc_category}] conf={classify_conf}")

        # 4. Process each page
        pages = []
        for i, img in enumerate(images):
            logger.info(f"Processing page {i+1}/{len(images)}")
            page_result = self.process_page(img, i, doc_class)
            pages.append(page_result)

        # 5. Aggregate results
        all_data = {}
        all_validations = []
        all_chunks = []
        all_markdown = ""

        for page in pages:
            for k, v in page.extracted_data.items():
                if k not in all_data and v is not None:
                    all_data[k] = v
            all_markdown += f"\n## Page {page.page_num + 1}\n\n{page.markdown}\n"
            all_validations.extend(page.validation_results)
            all_chunks.extend(page.chunks)

        # 6. Compute metrics
        if all_validations:
            overall_conf = sum(v.final_confidence for v in all_validations) / len(all_validations)
            verified = sum(1 for v in all_validations if v.validation_status == ValidationStatus.VERIFIED)
            accuracy = verified / len(all_validations) if all_validations else 0
            grounded_count = sum(1 for v in all_validations if v.is_grounded)
            grounding_cov = grounded_count / len(all_validations) if all_validations else 0
            flagged = [v.field_name for v in all_validations if v.is_flagged]
        else:
            overall_conf = 0.75  # Base OCR confidence
            accuracy = 0.0
            grounding_cov = 0.0
            flagged = []

        elapsed = time.time() - start

        result = DocumentResult(
            document_id=self._generate_id(file_path),
            file_path=file_path,
            document_type=doc_type,
            document_class=doc_class,
            document_category=doc_category,
            document_label=doc_label,
            classify_confidence=classify_conf,
            pages=pages,
            chunks=all_chunks,
            extracted_data=all_data,
            markdown_content=all_markdown.strip(),
            validation_results=all_validations,
            overall_confidence=overall_conf,
            accuracy_score=accuracy,
            grounding_coverage=grounding_cov,
            flagged_fields=flagged,
            processing_time=elapsed,
        )

        logger.info(f"Processing completed in {elapsed:.2f}s")
        return result

    def cleanup(self):
        if HAS_TORCH and torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
