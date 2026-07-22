"""PaddleOCR engine implementation.

Lazy-loaded: PaddleOCR is only imported and initialized when
recognize() is first called, not during module import or app startup.

The application starts, serves health checks, uploads, and conversions
without PaddleOCR installed.
"""
import os
import logging
import time
from typing import Optional

from app.ocr.base import OCREngine, OCRInput, OCRResult, OCRRegionResult
from app.ocr.normalizer import (
    pixel_bbox_to_normalized,
    pixel_polygon_to_normalized,
    normalize_confidence,
    sanitize_text,
)

logger = logging.getLogger(__name__)

# Environment flags to prevent PaddlePaddle PIR crashes
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")


class PaddleOCREngine(OCREngine):
    """PaddleOCR provider with lazy initialization.
    
    The heavy PaddleOCR model is loaded only on first recognize() call.
    Thread safety: initialization is guarded by a simple flag.
    A proper lock can be added for concurrent worker deployments.
    """
    
    def __init__(self, lang: str = "en", use_gpu: bool = False):
        self._lang = lang
        self._use_gpu = use_gpu
        self._ocr = None
        self._version_str = "unknown"
        self._use_predict_api = False
    
    @property
    def name(self) -> str:
        return "paddle"
    
    @property
    def version(self) -> str:
        return self._version_str
    
    def _ensure_initialized(self) -> None:
        """Lazy-load PaddleOCR on first use."""
        if self._ocr is not None:
            return
        
        try:
            from paddleocr import PaddleOCR
            import paddleocr
            self._version_str = getattr(paddleocr, "__version__", getattr(paddleocr, "VERSION", "unknown"))
        except ImportError:
            raise ImportError(
                "PaddleOCR is not installed. Install paddleocr to use this OCR provider."
            )
        
        # Try new API (PaddleOCR v3+) first, fall back to old API
        try:
            self._ocr = PaddleOCR(
                lang=self._lang,
                use_textline_orientation=True,
                use_gpu=self._use_gpu,
            )
            self._use_predict_api = True
        except Exception:
            try:
                self._ocr = PaddleOCR(
                    lang=self._lang,
                    use_angle_cls=True,
                    use_gpu=self._use_gpu,
                    show_log=False,
                )
                self._use_predict_api = False
            except Exception:
                self._ocr = PaddleOCR(lang=self._lang)
                self._use_predict_api = hasattr(self._ocr, "predict")
        
        logger.info(
            "ocr_engine_initialized engine=paddle version=%s api=%s gpu=%s",
            self._version_str,
            "predict" if self._use_predict_api else "ocr",
            self._use_gpu,
        )
    
    def recognize(self, ocr_input: OCRInput) -> OCRResult:
        """Run PaddleOCR on the given input.
        
        Requires ocr_input.temp_path to be set (PaddleOCR needs a file path).
        """
        self._ensure_initialized()
        
        start = time.monotonic()
        
        # PaddleOCR needs either a file path or a numpy array
        # Use temp_path which OCRService provides
        if not ocr_input.temp_path:
            raise ValueError("PaddleOCR requires a temporary file path. OCRService must set temp_path.")
        
        regions = []
        width = ocr_input.width
        height = ocr_input.height
        
        # Try predict API first, fall back to ocr API
        for attempt, use_predict in enumerate([self._use_predict_api, not self._use_predict_api]):
            try:
                if use_predict:
                    raw = self._ocr.predict(ocr_input.temp_path)
                    if raw and len(raw) > 0:
                        data = raw[0]
                        texts = data.get("rec_texts", [])
                        scores = data.get("rec_scores", [])
                        polys = data.get("rec_polys", [])
                        for text, score, poly in zip(texts, scores, polys):
                            coords = poly.tolist() if hasattr(poly, "tolist") else poly
                            xs = [float(p[0]) for p in coords]
                            ys = [float(p[1]) for p in coords]
                            
                            norm_bbox = pixel_bbox_to_normalized(
                                min(xs), min(ys), max(xs), max(ys), width, height
                            )
                            norm_poly = pixel_polygon_to_normalized(coords, width, height)
                            
                            regions.append(OCRRegionResult(
                                text=sanitize_text(str(text)),
                                confidence=normalize_confidence(float(score)),
                                bbox=norm_bbox,
                                polygon=norm_poly,
                            ))
                else:
                    raw = self._ocr.ocr(ocr_input.temp_path, cls=True)
                    if raw and raw[0]:
                        for line in raw[0]:
                            if line is None:
                                continue
                            polygon = line[0]
                            text = line[1][0]
                            confidence = float(line[1][1])
                            xs = [float(p[0]) for p in polygon]
                            ys = [float(p[1]) for p in polygon]
                            
                            norm_bbox = pixel_bbox_to_normalized(
                                min(xs), min(ys), max(xs), max(ys), width, height
                            )
                            coords = [[float(p[0]), float(p[1])] for p in polygon]
                            norm_poly = pixel_polygon_to_normalized(coords, width, height)
                            
                            regions.append(OCRRegionResult(
                                text=sanitize_text(str(text)),
                                confidence=normalize_confidence(confidence),
                                bbox=norm_bbox,
                                polygon=norm_poly,
                            ))
                
                if regions:
                    break
                if attempt == 0 and not regions:
                    continue
                break
            except ImportError:
                raise
            except Exception as e:
                logger.warning("ocr_engine_attempt_failed api=%s error=%s", 
                             "predict" if use_predict else "ocr", type(e).__name__)
                if attempt == 0:
                    continue
                break
        
        elapsed = (time.monotonic() - start) * 1000
        
        return OCRResult(
            engine=self.name,
            engine_version=self._version_str,
            language=self._lang,
            regions=regions,
            processing_time_ms=round(elapsed, 2),
        )
