"""Preserved legacy AI and OCR engines."""

from app.engines.ocr_engine import PaddleOCREngine
from app.engines.vlm_engine import GeminiVLM
from app.engines.classifier import classify_by_keywords, get_category, get_label, DOCUMENT_TAXONOMY
from app.engines.ocr_extractor import LayoutMarkdownBuilder, OCRFieldExtractor
from app.engines.chunker import ChunkExtractor
from app.engines.converter import DocumentConverter
from app.engines.grounding import GroundingEngine
from app.engines.validator import TripleValidator
from app.engines.llm_provider import get_llm, BaseLLM
